"""
To-do management tools — CRUD operations on the user's to-do list.
All functions take user_id to scope to-dos per WhatsApp user.
"""

from datetime import datetime, date
from state.database import Todo, db


def add_todo(
    user_id: str,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: str | None = None,
    category: str = "general"
) -> str:
    with db:
        todo = Todo.create(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            category=category,
        )
    return f"Added to-do #{todo.id}: \"{title}\" [{priority}] in {category}"


def list_todos(
    user_id: str,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    include_completed: bool = False,
) -> str:
    query = Todo.select().where(Todo.user_id == user_id)

    if status and status != "all":
        query = query.where(Todo.status == status)
    elif not include_completed:
        query = query.where(Todo.status != "done")

    if priority:
        query = query.where(Todo.priority == priority)
    if category:
        query = query.where(Todo.category == category)

    query = query.order_by(
        Todo.status.asc(),  # pending/in_progress before done
        _priority_order(),
        Todo.due_date.asc(nulls="LAST"),
        Todo.created_at.desc(),
    )

    todos = list(query)
    if not todos:
        return "No to-dos found matching your criteria."

    lines = []
    for t in todos:
        flag = _priority_emoji(t.priority)
        status_icon = {"pending": "⬜", "in_progress": "🔵", "done": "✅"}.get(t.status, "⬜")
        due = f" (due {t.due_date})" if t.due_date else ""
        overdue = ""
        if t.due_date and t.status != "done":
            try:
                if date.fromisoformat(t.due_date) < date.today():
                    overdue = " ⚠️ OVERDUE"
            except ValueError:
                pass
        desc = f"\n   {t.description}" if t.description else ""
        lines.append(f"{status_icon} #{t.id} {flag} {t.title}{due}{overdue} [{t.category}]{desc}")

    return "\n".join(lines)


def complete_todo(user_id: str, todo_id: int) -> str:
    try:
        todo = Todo.get(Todo.id == todo_id, Todo.user_id == user_id)
    except Todo.DoesNotExist:
        return f"To-do #{todo_id} not found."

    if todo.status == "done":
        return f"To-do #{todo_id} is already completed."

    with db:
        todo.status = "done"
        todo.completed_at = datetime.now()
        todo.save()

    return f"Completed to-do #{todo_id}: \"{todo.title}\" ✅"


def update_todo(
    user_id: str,
    todo_id: int,
    title: str | None = None,
    description: str | None = None,
    category: str | None = None,
    status: str | None = None,
) -> str:
    try:
        todo = Todo.get(Todo.id == todo_id, Todo.user_id == user_id)
    except Todo.DoesNotExist:
        return f"To-do #{todo_id} not found."

    changes = []
    with db:
        if title is not None:
            todo.title = title
            changes.append(f"title → \"{title}\"")
        if description is not None:
            todo.description = description
            changes.append("description updated")
        if category is not None:
            todo.category = category
            changes.append(f"category → {category}")
        if status is not None:
            todo.status = status
            if status == "done":
                todo.completed_at = datetime.now()
            changes.append(f"status → {status}")
        todo.save()

    return f"Updated to-do #{todo_id}: {', '.join(changes)}"


def delete_todo(user_id: str, todo_id: int) -> str:
    try:
        todo = Todo.get(Todo.id == todo_id, Todo.user_id == user_id)
    except Todo.DoesNotExist:
        return f"To-do #{todo_id} not found."

    title = todo.title
    with db:
        todo.delete_instance()

    return f"Deleted to-do #{todo_id}: \"{title}\""


def set_priority(user_id: str, todo_id: int, priority: str) -> str:
    try:
        todo = Todo.get(Todo.id == todo_id, Todo.user_id == user_id)
    except Todo.DoesNotExist:
        return f"To-do #{todo_id} not found."

    old = todo.priority
    with db:
        todo.priority = priority
        todo.save()

    return f"Priority for #{todo_id} changed: {old} → {priority}"


def set_due_date(user_id: str, todo_id: int, due_date: str) -> str:
    try:
        todo = Todo.get(Todo.id == todo_id, Todo.user_id == user_id)
    except Todo.DoesNotExist:
        return f"To-do #{todo_id} not found."

    with db:
        if due_date.lower() == "none":
            todo.due_date = None
            todo.save()
            return f"Cleared due date for #{todo_id}"
        else:
            todo.due_date = due_date
            todo.save()
            return f"Due date for #{todo_id} set to {due_date}"


def get_todo_summary(user_id: str) -> str:
    todos = list(Todo.select().where(Todo.user_id == user_id))
    if not todos:
        return "You have no to-dos yet."

    total = len(todos)
    by_status = {}
    by_priority = {}
    overdue = 0
    today = date.today()

    for t in todos:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        if t.status != "done":
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        if t.due_date and t.status != "done":
            try:
                if date.fromisoformat(t.due_date) < today:
                    overdue += 1
            except ValueError:
                pass

    lines = [f"📊 To-Do Summary ({total} total):"]
    for s in ["pending", "in_progress", "done"]:
        if s in by_status:
            icon = {"pending": "⬜", "in_progress": "🔵", "done": "✅"}[s]
            lines.append(f"  {icon} {s}: {by_status[s]}")

    if by_priority:
        lines.append("\nBy priority (active):")
        for p in ["urgent", "high", "medium", "low"]:
            if p in by_priority:
                lines.append(f"  {_priority_emoji(p)} {p}: {by_priority[p]}")

    if overdue:
        lines.append(f"\n⚠️ {overdue} overdue item(s)!")

    return "\n".join(lines)


def _priority_emoji(priority: str) -> str:
    return {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "🟡")


def _priority_order():
    """SQL CASE for ordering by priority."""
    from peewee import Case
    return Case(
        Todo.priority,
        [("urgent", 0), ("high", 1), ("medium", 2), ("low", 3)],
        4
    )
