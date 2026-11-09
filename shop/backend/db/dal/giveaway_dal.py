from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.giveaway_models import (
    GIVEAWAY_STATUS_ACTIVE,
    GIVEAWAY_STATUS_CANCELLED,
    GIVEAWAY_STATUS_DRAFT,
    GIVEAWAY_STATUS_FINISHED,
    Giveaway,
    GiveawayParticipant,
)
from db.models import User


async def create_giveaway(
    session: AsyncSession,
    *,
    text_html: str,
    photo_file_id: str | None,
    created_by_telegram_id: int | None,
    winners_count: int = 3,
    scheduled_draw_at: datetime | None = None,
) -> Giveaway:
    giveaway = Giveaway(
        status=GIVEAWAY_STATUS_DRAFT,
        text_html=text_html,
        photo_file_id=photo_file_id,
        created_by_telegram_id=created_by_telegram_id,
        winners_count=winners_count,
        scheduled_draw_at=scheduled_draw_at,
    )
    session.add(giveaway)
    await session.flush()
    return giveaway


async def get_giveaway(session: AsyncSession, giveaway_id: int) -> Giveaway | None:
    return await session.get(Giveaway, giveaway_id)


async def get_latest_giveaway(session: AsyncSession) -> Giveaway | None:
    """Latest non-draft giveaway: abandoned composer drafts must not shadow it."""
    return (
        await session.execute(
            select(Giveaway)
            .where(Giveaway.status != GIVEAWAY_STATUS_DRAFT)
            .order_by(Giveaway.giveaway_id.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def publish_giveaway(
    session: AsyncSession, giveaway: Giveaway, *, chat_id: int, message_id: int
) -> None:
    giveaway.status = GIVEAWAY_STATUS_ACTIVE
    giveaway.chat_id = chat_id
    giveaway.message_id = message_id
    giveaway.published_at = datetime.now(UTC)
    await session.flush()


async def finish_giveaway(session: AsyncSession, giveaway: Giveaway) -> None:
    giveaway.status = GIVEAWAY_STATUS_FINISHED
    giveaway.finished_at = datetime.now(UTC)
    await session.flush()


async def cancel_giveaway(session: AsyncSession, giveaway: Giveaway) -> None:
    giveaway.status = GIVEAWAY_STATUS_CANCELLED
    giveaway.finished_at = datetime.now(UTC)
    await session.flush()


async def schedule_draw(session: AsyncSession, giveaway: Giveaway, when: datetime | None) -> None:
    giveaway.scheduled_draw_at = when
    await session.flush()


async def due_giveaways(session: AsyncSession, now: datetime) -> list[Giveaway]:
    return list(
        (
            await session.execute(
                select(Giveaway)
                .where(
                    Giveaway.status == GIVEAWAY_STATUS_ACTIVE,
                    Giveaway.scheduled_draw_at.isnot(None),
                    Giveaway.scheduled_draw_at <= now,
                )
                .order_by(Giveaway.scheduled_draw_at.asc())
            )
        ).scalars()
    )


async def set_display_count(session: AsyncSession, giveaway: Giveaway, value: int | None) -> None:
    giveaway.display_participants = value
    await session.flush()


async def bump_display_count(session: AsyncSession, giveaway: Giveaway) -> int:
    """Display counter for the participate button after a real join.

    Real count by default; when the admin overrode the number, +1 on top of it.
    """
    if giveaway.display_participants is None:
        count = await count_participants(session, int(giveaway.giveaway_id))
        giveaway.display_participants = count
    else:
        giveaway.display_participants = int(giveaway.display_participants) + 1
    await session.flush()
    return int(giveaway.display_participants)


async def discard_draft(session: AsyncSession, giveaway: Giveaway) -> None:
    """Drafts were never published, so participants cannot exist; hard delete."""
    if giveaway.status != GIVEAWAY_STATUS_DRAFT:
        return
    await session.delete(giveaway)
    await session.flush()


async def add_participant(
    session: AsyncSession, giveaway_id: int, user_id: int
) -> tuple[bool, bool]:
    """Returns (joined_now, already_joined)."""
    existing = await session.execute(
        select(GiveawayParticipant.participant_id).where(
            GiveawayParticipant.giveaway_id == giveaway_id,
            GiveawayParticipant.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False, True
    session.add(GiveawayParticipant(giveaway_id=giveaway_id, user_id=user_id))
    await session.flush()
    return True, False


async def count_participants(session: AsyncSession, giveaway_id: int) -> int:
    return int(
        await session.scalar(
            select(func.count(GiveawayParticipant.participant_id)).where(
                GiveawayParticipant.giveaway_id == giveaway_id
            )
        )
        or 0
    )


async def list_participants(
    session: AsyncSession, giveaway_id: int, *, offset: int = 0, limit: int = 15
) -> list[tuple[GiveawayParticipant, User]]:
    rows = await session.execute(
        select(GiveawayParticipant, User)
        .join(User, User.user_id == GiveawayParticipant.user_id)
        .where(GiveawayParticipant.giveaway_id == giveaway_id)
        .order_by(GiveawayParticipant.joined_at.asc())
        .offset(offset)
        .limit(limit)
    )
    return [(row[0], row[1]) for row in rows]


async def participant_users(
    session: AsyncSession, giveaway_id: int
) -> list[tuple[GiveawayParticipant, User]]:
    rows = await session.execute(
        select(GiveawayParticipant, User)
        .join(User, User.user_id == GiveawayParticipant.user_id)
        .where(GiveawayParticipant.giveaway_id == giveaway_id)
        .order_by(GiveawayParticipant.participant_id.asc())
    )
    return [(row[0], row[1]) for row in rows]


async def set_participant_place(
    session: AsyncSession, participant: GiveawayParticipant, place: int
) -> None:
    participant.place = place
    await session.flush()
