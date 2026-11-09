from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.base import Base

GIVEAWAY_ID_TYPE = BigInteger().with_variant(Integer, "sqlite")

GIVEAWAY_STATUS_DRAFT = "draft"
GIVEAWAY_STATUS_ACTIVE = "active"
GIVEAWAY_STATUS_FINISHED = "finished"
GIVEAWAY_STATUS_CANCELLED = "cancelled"


class Giveaway(Base):
    __tablename__ = "giveaways"
    __table_args__ = (Index("ix_giveaways_status_created", "status", "created_at"),)

    giveaway_id = Column(GIVEAWAY_ID_TYPE, primary_key=True, autoincrement=True)
    status = Column(String(16), nullable=False, default=GIVEAWAY_STATUS_DRAFT, index=True)
    text_html = Column(Text, nullable=False)
    photo_file_id = Column(String, nullable=True)
    chat_id = Column(BigInteger, nullable=True)
    message_id = Column(BigInteger, nullable=True)
    winners_count = Column(Integer, nullable=False, default=3)
    created_by_telegram_id = Column(BigInteger, nullable=True)
    scheduled_draw_at = Column(DateTime(timezone=True), nullable=True, index=True)
    # Shown on the participate button instead of the real count when set.
    display_participants = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    participants = relationship(
        "GiveawayParticipant", back_populates="giveaway", cascade="all, delete-orphan"
    )


class GiveawayParticipant(Base):
    __tablename__ = "giveaway_participants"
    __table_args__ = (
        UniqueConstraint("giveaway_id", "user_id", name="uq_giveaway_participants_giveaway_user"),
        Index("ix_giveaway_participants_user", "user_id"),
    )

    participant_id = Column(GIVEAWAY_ID_TYPE, primary_key=True, autoincrement=True)
    giveaway_id = Column(
        GIVEAWAY_ID_TYPE,
        ForeignKey("giveaways.giveaway_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    place = Column(Integer, nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    giveaway = relationship("Giveaway", back_populates="participants")
    user = relationship("User")
