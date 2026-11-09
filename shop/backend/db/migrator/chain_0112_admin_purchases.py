"""Admin purchase records (manual expense tracker with expiry reminders)."""

from sqlalchemy.engine import Connection

from db.admin_purchase_models import AdminPurchase

from .engine import Migration


def _migration_0112_admin_purchases(connection: Connection) -> None:
    AdminPurchase.__table__.create(connection, checkfirst=True)


CHAIN_0112_ADMIN_PURCHASES = [
    Migration(
        id="0112_admin_purchases",
        description="Manual admin purchase records with expiry dates for reminders",
        upgrade=_migration_0112_admin_purchases,
    )
]
