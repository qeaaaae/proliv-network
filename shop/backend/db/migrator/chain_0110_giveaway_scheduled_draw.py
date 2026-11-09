"""Scheduled draw timestamp on giveaways."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from .engine import Migration


def _migration_0110_giveaway_scheduled_draw(connection: Connection) -> None:
    inspector = inspect(connection)
    if "giveaways" not in inspector.get_table_names():
        return
    columns = {item["name"] for item in inspector.get_columns("giveaways")}
    if "scheduled_draw_at" not in columns:
        connection.execute(text("ALTER TABLE giveaways ADD COLUMN scheduled_draw_at TIMESTAMPTZ"))
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_giveaways_scheduled_draw_at "
                "ON giveaways (scheduled_draw_at)"
            )
        )


CHAIN_0110_GIVEAWAY_SCHEDULED_DRAW = [
    Migration(
        id="0110_giveaway_scheduled_draw",
        description="Optional scheduled draw timestamp for automatic giveaway results",
        upgrade=_migration_0110_giveaway_scheduled_draw,
    )
]
