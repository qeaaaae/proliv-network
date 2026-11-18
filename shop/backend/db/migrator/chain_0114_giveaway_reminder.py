"""Reminder-sent marker on giveaways (admin ping before scheduled draw)."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from .engine import Migration


def _migration_0114_giveaway_reminder(connection: Connection) -> None:
    inspector = inspect(connection)
    if "giveaways" not in inspector.get_table_names():
        return
    columns = {item["name"] for item in inspector.get_columns("giveaways")}
    if "reminder_sent_at" not in columns:
        connection.execute(
            text("ALTER TABLE giveaways ADD COLUMN reminder_sent_at TIMESTAMPTZ")
        )


CHAIN_0114_GIVEAWAY_REMINDER = [
    Migration(
        id="0114_giveaway_reminder",
        description="Track whether the pre-draw admin reminder was sent",
        upgrade=_migration_0114_giveaway_reminder,
    )
]
