"""
Tool registry — all Claude-callable tools in one place.
Import TOOLS for the schema list, call dispatch(name, inputs) to execute.
"""

from tools.todo_manager import (
    add_todo, list_todos, complete_todo, update_todo,
    delete_todo, set_priority, set_due_date, get_todo_summary
)
from tools.recommendation import get_recommendations

# ── Tool schemas (what Claude sees) ──────────────────────────────────────────

TOOLS = [
    {
        "name": "add_todo",
        "description": "Add a new to-do item for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short title for the to-do"},
                "description": {"type": "string", "description": "Optional longer description or notes"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Priority level (default: medium)"
                },
                "due_date": {"type": "string", "description": "Optional due date in YYYY-MM-DD format"},
                "category": {"type": "string", "description": "Optional category/tag (e.g. 'work', 'personal', 'health')"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "list_todos",
        "description": "List the user's to-do items. Can filter by status, priority, or category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "done", "all"],
                    "description": "Filter by status (default: show pending and in_progress)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Filter by priority"
                },
                "category": {"type": "string", "description": "Filter by category"},
                "include_completed": {"type": "boolean", "description": "Whether to include completed items (default: false)"}
            },
            "required": []
        }
    },
    {
        "name": "complete_todo",
        "description": "Mark a to-do item as completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The ID of the to-do to complete"}
            },
            "required": ["todo_id"]
        }
    },
    {
        "name": "update_todo",
        "description": "Update an existing to-do item's title, description, category, or status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The ID of the to-do to update"},
                "title": {"type": "string", "description": "New title"},
                "description": {"type": "string", "description": "New description"},
                "category": {"type": "string", "description": "New category"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "done"],
                    "description": "New status"
                }
            },
            "required": ["todo_id"]
        }
    },
    {
        "name": "delete_todo",
        "description": "Delete a to-do item permanently.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The ID of the to-do to delete"}
            },
            "required": ["todo_id"]
        }
    },
    {
        "name": "set_priority",
        "description": "Change the priority of a to-do item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The ID of the to-do"},
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "New priority level"
                }
            },
            "required": ["todo_id", "priority"]
        }
    },
    {
        "name": "set_due_date",
        "description": "Set or update the due date for a to-do item.",
        "input_schema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "integer", "description": "The ID of the to-do"},
                "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format, or 'none' to clear"}
            },
            "required": ["todo_id", "due_date"]
        }
    },
    {
        "name": "get_todo_summary",
        "description": "Get a summary of the user's to-do statistics: counts by status, priority, overdue items, etc.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_recommendations",
        "description": "Analyze the user's current to-dos, priorities, and deadlines to recommend which tasks to focus on next and suggest a path forward. Call this when the user asks for advice on what to do next, or when they seem overwhelmed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {
                    "type": "string",
                    "description": "Optional additional context about what the user is working on or how they're feeling"
                }
            },
            "required": []
        }
    }
]


# ── Dispatcher ────────────────────────────────────────────────────────────────

def dispatch(tool_name: str, tool_input: dict, user_id: str) -> str:
    """Route a Claude tool call to the right Python function. Returns a string result."""
    try:
        match tool_name:
            case "add_todo":
                return add_todo(user_id=user_id, **tool_input)
            case "list_todos":
                return list_todos(user_id=user_id, **tool_input)
            case "complete_todo":
                return complete_todo(user_id=user_id, **tool_input)
            case "update_todo":
                return update_todo(user_id=user_id, **tool_input)
            case "delete_todo":
                return delete_todo(user_id=user_id, **tool_input)
            case "set_priority":
                return set_priority(user_id=user_id, **tool_input)
            case "set_due_date":
                return set_due_date(user_id=user_id, **tool_input)
            case "get_todo_summary":
                return get_todo_summary(user_id=user_id)
            case "get_recommendations":
                return get_recommendations(user_id=user_id, **tool_input)
            case _:
                return f"Error: unknown tool '{tool_name}'"
    except Exception as e:
        return f"Tool error ({tool_name}): {str(e)}"
