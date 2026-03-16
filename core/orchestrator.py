"""
The Claude API tool-use loop.
Takes a user message + conversation history, runs Claude with tools,
dispatches tool calls, loops until Claude returns a final text response.
"""

import anthropic
from config.settings import settings
from tools import TOOLS, dispatch

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a personal assistant chatbot on WhatsApp. You help the user manage their to-do list, stay organized, and recommend what to focus on next.

Your personality:
- Warm, concise, and conversational — this is WhatsApp, keep it casual and helpful
- You're like a smart friend who also keeps you on track
- Use short messages, break up long responses naturally
- You can use emojis sparingly to keep things friendly

Your capabilities (via tools):
- Manage to-dos: add, list, complete, update, delete, set priority and due dates
- Give recommendations on what to focus on next based on priorities, deadlines, and context
- Track progress and provide summaries

Rules:
- When the user mentions something they need to do, offer to add it as a to-do
- When listing to-dos, format them cleanly but keep it WhatsApp-friendly
- When the user seems overwhelmed or asks "what should I do?", use get_recommendations
- For ambiguous to-do references (e.g. "mark that one done"), use context from conversation history
- Always confirm destructive actions (delete) before executing
- If a user says a simple greeting, respond warmly and maybe show a quick summary if they have active to-dos
- Keep responses under 1000 chars when possible — this is WhatsApp, not email
- Use conversation history to maintain context about what the user was discussing
"""


def run(user_message: str, history: list[dict], user_id: str) -> str:
    """
    Synchronous Claude tool-use loop for a single user turn.
    """
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
