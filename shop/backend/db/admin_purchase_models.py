from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Index,
    Integer,
    String,
)
from sqlalchemy.sql import func

from db.base import Base

PURCHASE_ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


class AdminPurchase(Base):
    """Manual expense record: something the admin bought from a provider.

    ``expires_on`` is the source of truth for reminders; ``period_label``
    keeps the admin's own wording (e.g. "1 month") for display.
    """

    __tablename__ = "admin_purchases"
    __table_args__ = (Index("ix_admin_purchases_expires_on", "expires_on"),)

    purchase_id = Column(PURCHASE_ID_TYPE, primary_key=True, autoincrement=True)
    provider = Column(String(128), nullable=False)
    title = Column(String(255), nullable=False)
    note = Column(String(255), nullable=True)
    price_label = Column(String(64), nullable=True)
    paid_on = Column(Date, nullable=False)
    period_label = Column(String(64), nullable=False)
    expires_on = Column(Date, nullable=False)
    last_notified_on = Column(Date, nullable=True)
    created_by_telegram_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
