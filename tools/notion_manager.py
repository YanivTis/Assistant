"""
Notion integration — create notes and manage a to-do checklist in Notion.
Uses the Notion API directly (no SDK needed).
"""

import logging
import requests
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _notion_configured() -> bool:
    return bool(settings.NOTION_API_KEY)


# ── Notes ────────────────────────────────────────────────────────────────────


def create_note(user_id: str, title: str, content: str, **kwargs) -> str:
    """Create a new note page under the Notes parent page in Notion."""
    if not _notion_configured():
        return "Error: Notion is not configured. Ask the user to set NOTION_API_KEY and NOTION_NOTES_PAGE_ID."

    if not settings.NOTION_NOTES_PAGE_ID:
        return "Error: NOTION_NOTES_PAGE_ID is not set. The user needs to share a Notion page for notes."

    # Build rich text blocks from content (split by double newline for paragraphs)
    children = []
    for paragraph in content.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": paragraph}}]
            },
        })

    payload = {
        "parent": {"page_id": settings.NOTION_NOTES_PAGE_ID},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": children,
    }

    resp = requests.post(f"{NOTION_BASE}/pages", headers=_headers(), json=payload)
    if resp.status_code != 200:
        logger.error("Notion create_note failed: %s %s", resp.status_code, resp.text)
        return f"Error creating note in Notion: {resp.status_code}"

    page = resp.json()
    url = page.get("url", "")
    return f"Note '{title}' created in Notion. {url}"


def append_note(user_id: str, page_id: str, content: str, **kwargs) -> str:
    """Append content to an existing Notion page."""
    if not _notion_configured():
        return "Error: Notion is not configured."

    children = []
    for paragraph in content.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": paragraph}}]
            },
        })

    resp = requests.patch(
        f"{NOTION_BASE}/blocks/{page_id}/children",
        headers=_headers(),
        json={"children": children},
    )
    if resp.status_code != 200:
        logger.error("Notion append_note failed: %s %s", resp.status_code, resp.text)
        return f"Error appending to note: {resp.status_code}"

    return "Content appended to note."


def search_notes(user_id: str, query: str, **kwargs) -> str:
    """Search for existing notes by title."""
    if not _notion_configured():
        return "Error: Notion is not configured."

    payload = {
        "query": query,
        "filter": {"property": "object", "value": "page"},
        "page_size": 5,
    }

    resp = requests.post(f"{NOTION_BASE}/search", headers=_headers(), json=payload)
    if resp.status_code != 200:
        logger.error("Notion search failed: %s %s", resp.status_code, resp.text)
        return f"Error searching Notion: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No matching notes found."

    lines = []
    for page in results:
        title_parts = page.get("properties", {}).get("title", {}).get("title", [])
        title = title_parts[0]["plain_text"] if title_parts else "(untitled)"
        page_id = page["id"]
        url = page.get("url", "")
        lines.append(f"• {title} (id: {page_id})\n  {url}")

    return "Found notes:\n" + "\n".join(lines)


# ── To-do checklist ──────────────────────────────────────────────────────────


def add_notion_todo(user_id: str, title: str, priority: str = "medium",
                    due_date: str = None, category: str = "general", **kwargs) -> str:
    """Add a to-do item to the Notion Todos database."""
    if not _notion_configured():
        return "Error: Notion is not configured. Ask the user to set NOTION_API_KEY and NOTION_TODOS_DB_ID."

    if not settings.NOTION_TODOS_DB_ID:
        return "Error: NOTION_TODOS_DB_ID is not set. The user needs to create a Notion database for todos."

    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Priority": {"select": {"name": priority.capitalize()}},
        "Category": {"select": {"name": category}},
        "Status": {"checkbox": False},
    }

    if due_date:
        properties["Due Date"] = {"date": {"start": due_date}}

    payload = {
        "parent": {"database_id": settings.NOTION_TODOS_DB_ID},
        "properties": properties,
    }

    resp = requests.post(f"{NOTION_BASE}/pages", headers=_headers(), json=payload)
    if resp.status_code != 200:
        logger.error("Notion add_todo failed: %s %s", resp.status_code, resp.text)
        return f"Error adding todo to Notion: {resp.status_code}"

    url = resp.json().get("url", "")
    return f"Todo '{title}' added to Notion. {url}"
