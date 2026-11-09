"""Display-participant override on giveaways (button counter)."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from .engine import Migration


def _migration_0111_giveaway_display_count(connection: Connection) -> None:
    inspector = inspect(connection)
    if "giveaways" not in inspector.get_table_names():
        return
    columns = {item["name"] for item in inspector.get_columns("giveaways")}
    if "display_participants" not in columns:
        connection.execute(text("ALTER TABLE giveaways ADD COLUMN display_participants INTEGER"))


CHAIN_0111_GIVEAWAY_DISPLAY_COUNT = [
    Migration(
        id="0111_giveaway_display_count",
        description="Optional display-participants override for the participate button",
        upgrade=_migration_0111_giveaway_display_count,
    )
]
