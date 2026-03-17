"""
AI tool-use loop supporting both Anthropic (Claude) and OpenAI providers.
Takes a user message + conversation history, runs the model with tools,
dispatches tool calls, loops until the model returns a final text response.
"""

import json
import logging

from config.settings import settings
from tools import TOOLS, OPENAI_TOOLS, dispatch

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a personal assistant chatbot on WhatsApp. You help the user capture notes, manage to-dos, stay organized, and recommend what to focus on next.

Your personality:
- Warm, concise, and conversational — this is WhatsApp, keep it casual and helpful
- You're like a smart friend who also keeps you on track
- Use short messages, break up long responses naturally
- You can use emojis sparingly to keep things friendly

Your capabilities (via tools):
- Manage to-dos: add, list, complete, update, delete, set priority and due dates
- Save notes to Notion: create new notes, append to existing ones, search for notes
- Sync to-dos to Notion: when adding a to-do, also add it to the Notion checklist
- Give recommendations on what to focus on next based on priorities, deadlines, and context
- Track progress and provide summaries

How to route messages:
- The user shares a thought, idea, or information worth saving → use create_note to save it in Notion
- The user wants to add to a previous note → use search_notes to find it, then append_note
- The user has a to-do or action item → use BOTH add_todo (for WhatsApp quick access) AND add_notion_todo (for Notion checklist) with the same details
- The user is just chatting or asking questions → respond normally in WhatsApp
- The user asks "what should I do?" or seems overwhelmed → use get_recommendations

Rules:
- When the user mentions something they need to do, offer to add it as a to-do
- When adding a to-do, always add it to both local storage AND Notion so it appears in both places
- When the user shares something noteworthy (ideas, meeting notes, decisions, reflections), save it as a Notion note
- When listing to-dos, format them cleanly but keep it WhatsApp-friendly
- For ambiguous to-do references (e.g. "mark that one done"), use context from conversation history
- Always confirm destructive actions (delete) before executing
- If a user says a simple greeting, respond warmly and maybe show a quick summary if they have active to-dos
- Keep responses under 1000 chars when possible — this is WhatsApp, not email
- Use conversation history to maintain context about what the user was discussing
- If a Notion tool returns an error about configuration, let the user know they need to set up their Notion integration
"""


# ── Provider implementations ─────────────────────────────────────────────────


def _run_anthropic(user_message: str, history: list[dict], user_id: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    messages = history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch(block.name, block.input, user_id=user_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "(no response)"


def _run_openai(user_message: str, history: list[dict], user_id: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Convert Anthropic-style history to OpenAI format
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        role = msg["role"]
        content = msg.get("content", "")
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        # Skip non-string content blocks (tool results in Anthropic format)
        # — they are re-created by the OpenAI loop below

    messages.append({"role": "user", "content": user_message})

    while True:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=OPENAI_TOOLS,
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls":
            # Append the assistant message with tool calls
            messages.append(choice.message)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                result = dispatch(fn_name, fn_args, user_id=user_id)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
        else:
            return choice.message.content or "(no response)"


# ── Public API ───────────────────────────────────────────────────────────────


def run(user_message: str, history: list[dict], user_id: str) -> str:
    """
    Synchronous tool-use loop for a single user turn.
    Routes to Anthropic or OpenAI based on AI_PROVIDER setting.
    """
    provider = settings.AI_PROVIDER.lower()
    logger.info(f"Using AI provider: {provider}")

    if provider == "openai":
        return _run_openai(user_message, history, user_id)
    else:
        return _run_anthropic(user_message, history, user_id)
