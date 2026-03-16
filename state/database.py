from datetime import datetime
from peewee import (
    SqliteDatabase, Model, CharField, IntegerField,
    BooleanField, DateTimeField, TextField, AutoField
)
from config.settings import settings

db = SqliteDatabase(settings.DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Todo(BaseModel):
    """A to-do item belonging to a user."""
    id = AutoField()
    user_id = CharField()
    title = CharField()
    description = TextField(default="")
    status = CharField(default="pending")       # pending | in_progress | done
    priority = CharField(default="medium")      # low | medium | high | urgent
    category = CharField(default="general")
    due_date = CharField(null=True)             # YYYY-MM-DD or null
    created_at = DateTimeField(default=datetime.now)
    completed_at = DateTimeField(null=True)

    class Meta:
        table_name = "todos"


class ConversationHistory(BaseModel):
    """Stores recent message history for Claude context."""
    user_id = CharField()
    role = CharField()          # 'user' | 'assistant'
    content = TextField()
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = "conversation_history"


def init_db():
    db.connect()
    db.create_tables([Todo, ConversationHistory], safe=True)
    db.close()
