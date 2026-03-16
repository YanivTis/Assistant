"""
WhatsApp bot — Flask webhook server for the Meta WhatsApp Business Cloud API.
Receives incoming messages, routes through the Claude orchestrator,
and sends responses back via the WhatsApp API.
"""

import logging
import requests
from flask import Flask, request, jsonify
from config.settings import settings
from core.orchestrator import run as orchestrator_run
from state.database import ConversationHistory, db

logger = logging.getLogger(__name__)

app = Flask(__name__)

MAX_HISTORY = settings.MAX_HISTORY
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"


def get_history(user_id: str) -> list[dict]:
    """Fetch recent conversation history for Claude context."""
    rows = (
        ConversationHistory
        .select()
        .where(ConversationHistory.user_id == user_id)
        .order_by(ConversationHistory.created_at.desc())
        .limit(MAX_HISTORY)
    )
    messages = [{"role": r.role, "content": r.content} for r in rows]
    return list(reversed(messages))


def save_turn(user_id: str, user_msg: str, assistant_msg: str):
    """Persist a conversation turn to SQLite."""
    with db:
        ConversationHistory.create(user_id=user_id, role="user", content=user_msg)
        ConversationHistory.create(user_id=user_id, role="assistant", content=assistant_msg)


def send_whatsapp_message(to: str, text: str):
    """Send a text message via the WhatsApp Business Cloud API."""
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    # WhatsApp has a ~4096 char limit per message — chunk if needed
    for chunk in _chunk_message(text, limit=4000):
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": chunk},
        }
        resp = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if resp.status_code != 200:
            logger.error(f"WhatsApp API error: {resp.status_code} — {resp.text}")


def _chunk_message(text: str, limit: int = 4000) -> list[str]:
    """Split a message into WhatsApp-safe chunks."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        # Try to break at a newline
        if len(text) > limit:
            split_at = text.rfind("\n", 0, limit)
            if split_at == -1:
                split_at = limit
        else:
            split_at = len(text)
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


@app.route("/webhook", methods=["GET"])
def verify():
    """Webhook verification endpoint for Meta."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified.")
        return challenge, 200
    else:
        logger.warning("Webhook verification failed.")
        return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages."""
    data = request.get_json()

    if not data:
        return jsonify({"status": "no data"}), 400

    # Extract message from the webhook payload
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        # Skip non-message events (status updates, etc.)
        if "messages" not in value:
            return jsonify({"status": "ok"}), 200

        message = value["messages"][0]
        sender = message["from"]  # phone number
        msg_type = message.get("type", "")

        # Only handle text messages for now
        if msg_type != "text":
            send_whatsapp_message(
                sender,
                "I can only handle text messages for now. Send me a text and I'll help you out!"
            )
            return jsonify({"status": "ok"}), 200

        text = message["text"]["body"]

    except (KeyError, IndexError):
        logger.debug("Received non-message webhook event, ignoring.")
        return jsonify({"status": "ok"}), 200

    # Security: only respond to allowed phone numbers
    if settings.WHATSAPP_ALLOWED_NUMBERS and sender not in settings.WHATSAPP_ALLOWED_NUMBERS:
        logger.warning(f"Blocked message from unauthorized number: {sender}")
        return jsonify({"status": "ok"}), 200

    logger.info(f"Message from {sender}: {text[:80]}...")

    # Process through Claude orchestrator
    try:
        history = get_history(sender)
        response = orchestrator_run(text, history, user_id=sender)
        save_turn(sender, text, response)
        send_whatsapp_message(sender, response)
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        send_whatsapp_message(sender, "Sorry, I ran into an issue. Try again in a moment.")

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


def start():
    """Start the Flask webhook server."""
    app.run(host=settings.HOST, port=settings.PORT)
