"""
Recommendation engine — analyzes user's to-dos and provides
actionable advice on what to focus on next.
"""

from datetime import date
from state.database import Todo


def get_recommendations(user_id: str, context: str = "") -> str:
    todos = list(
        Todo.select()
        .where(Todo.user_id == user_id, Todo.status != "done")
        .order_by(Todo.created_at.asc())
    )

    if not todos:
        return "You have no active to-dos! Either you're all caught up, or it's time to plan your next steps."

    today = date.today()
    overdue = []
    due_today = []
    due_soon = []  # within 3 days
    urgent = []
    high = []
    in_progress = []
    stale = []  # pending for a while with no due date

    for t in todos:
        if t.status == "in_progress":
            in_progress.append(t)

        if t.priority == "urgent":
            urgent.append(t)
        elif t.priority == "high":
            high.append(t)

        if t.due_date:
            try:
                due = date.fromisoformat(t.due_date)
                delta = (due - today).days
                if delta < 0:
                    overdue.append((t, abs(delta)))
                elif delta == 0:
                    due_today.append(t)
                elif delta <= 3:
                    due_soon.append((t, delta))
            except ValueError:
                pass

    lines = ["📋 Here's my analysis of your current to-dos:\n"]

    if overdue:
        lines.append("🚨 *OVERDUE* — These need immediate attention:")
        for t, days in sorted(overdue, key=lambda x: -x[1]):
            lines.append(f"  • #{t.id} {t.title} ({days} day(s) overdue)")
        lines.append("")

    if due_today:
        lines.append("📅 *DUE TODAY:*")
        for t in due_today:
            lines.append(f"  • #{t.id} {t.title}")
        lines.append("")

    if due_soon:
        lines.append("⏰ *Coming up soon:*")
        for t, days in sorted(due_soon, key=lambda x: x[1]):
            lines.append(f"  • #{t.id} {t.title} (in {days} day(s))")
        lines.append("")

    if urgent and not any(t in [o[0] for o in overdue] for t in urgent):
        lines.append("🔴 *Urgent priority:*")
        for t in urgent:
            lines.append(f"  • #{t.id} {t.title}")
        lines.append("")

    if in_progress:
        lines.append("🔵 *Currently in progress:*")
        for t in in_progress:
            lines.append(f"  • #{t.id} {t.title}")
        lines.append("")

    # Build recommendation
    lines.append("💡 *My recommendation:*")
    if overdue:
        lines.append("Start by tackling your overdue items — they're past due and need closure.")
        if len(overdue) > 2:
            lines.append("If they're no longer relevant, consider deleting them to clear mental space.")
    elif due_today:
        lines.append("Focus on today's deadlines first to stay on track.")
    elif urgent:
        lines.append("Prioritize the urgent items before anything else.")
    elif in_progress and len(in_progress) >= 2:
        lines.append("You have multiple items in progress. Try finishing one before starting another — context switching is costly.")
    elif high:
        lines.append(f"Your highest priority item is #{high[0].id}: \"{high[0].title}\". I'd start there.")
    else:
        lines.append("Things look manageable! Pick the task that gives you the most momentum and knock it out.")

    if context:
        lines.append(f"\n(Considering your note: \"{context}\")")

    # Category breakdown
    categories = {}
    for t in todos:
        categories[t.category] = categories.get(t.category, 0) + 1
    if len(categories) > 1:
        lines.append(f"\n📂 Spread across: {', '.join(f'{cat} ({n})' for cat, n in sorted(categories.items(), key=lambda x: -x[1]))}")

    return "\n".join(lines)
