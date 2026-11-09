"""Price label on admin purchases (free-text cost of the paid period)."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from .engine import Migration


def _migration_0113_admin_purchase_price(connection: Connection) -> None:
    inspector = inspect(connection)
    if "admin_purchases" not in inspector.get_table_names():
        return
    columns = {item["name"] for item in inspector.get_columns("admin_purchases")}
    if "price_label" not in columns:
        connection.execute(text("ALTER TABLE admin_purchases ADD COLUMN price_label VARCHAR(64)"))


CHAIN_0113_ADMIN_PURCHASE_PRICE = [
    Migration(
        id="0113_admin_purchase_price",
        description="Optional price label on admin purchase records",
        upgrade=_migration_0113_admin_purchase_price,
    )
]
