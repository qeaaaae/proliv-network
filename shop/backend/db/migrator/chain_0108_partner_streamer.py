"""Partner kind and streamer banner placement fields on partner profiles."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from .engine import Migration


def _migration_0108_partner_streamer(connection: Connection) -> None:
    additions = (
        ("partner_profiles", "kind", "VARCHAR(32) NOT NULL DEFAULT 'standard'"),
        ("partner_profiles", "banner_below_stream", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("partner_profiles", "banner_on_stream", "BOOLEAN NOT NULL DEFAULT FALSE"),
    )
    inspector = inspect(connection)
    for table, column, definition in additions:
        if table not in inspector.get_table_names():
            continue
        if column not in {item["name"] for item in inspector.get_columns(table)}:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))


CHAIN_0108_PARTNER_STREAMER = [
    Migration(
        id="0108_partner_streamer",
        description="Partner kind (standard/streamer/clipper) and streamer banner placements",
        upgrade=_migration_0108_partner_streamer,
    )
]
