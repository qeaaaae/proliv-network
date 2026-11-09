from __future__ import annotations

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.admin_purchase_models import AdminPurchase


async def create_purchase(
    session: AsyncSession,
    *,
    provider: str,
    title: str,
    note: str | None,
    price_label: str | None,
    paid_on: date,
    period_label: str,
    expires_on: date,
    created_by_telegram_id: int | None,
) -> AdminPurchase:
    purchase = AdminPurchase(
        provider=provider,
        title=title,
        note=note,
        price_label=price_label,
        paid_on=paid_on,
        period_label=period_label,
        expires_on=expires_on,
        created_by_telegram_id=created_by_telegram_id,
    )
    session.add(purchase)
    await session.flush()
    return purchase


async def get_purchase(session: AsyncSession, purchase_id: int) -> AdminPurchase | None:
    return await session.get(AdminPurchase, purchase_id)


async def count_purchases(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count(AdminPurchase.purchase_id))) or 0)


async def list_purchases(
    session: AsyncSession, *, offset: int = 0, limit: int = 15
) -> list[AdminPurchase]:
    rows = await session.execute(
        select(AdminPurchase)
        .order_by(AdminPurchase.expires_on.asc(), AdminPurchase.purchase_id.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(rows.scalars())


async def all_expiry_price_pairs(session: AsyncSession) -> list[tuple[date, str | None]]:
    """(expires_on, price_label) for every record - used for the monthly total."""
    rows = await session.execute(select(AdminPurchase.expires_on, AdminPurchase.price_label))
    return [(row[0], row[1]) for row in rows.all()]


async def renew_purchase(
    session: AsyncSession,
    purchase: AdminPurchase,
    *,
    paid_on: date,
    period_label: str,
    expires_on: date,
    price_label: str | None = None,
) -> None:
    purchase.paid_on = paid_on
    purchase.period_label = period_label
    purchase.expires_on = expires_on
    if price_label is not None:
        purchase.price_label = price_label
    purchase.last_notified_on = None
    await session.flush()


async def mark_notified(session: AsyncSession, purchase: AdminPurchase, day: date) -> None:
    purchase.last_notified_on = day
    await session.flush()


async def delete_purchase(session: AsyncSession, purchase: AdminPurchase) -> None:
    await session.delete(purchase)
    await session.flush()


async def purchases_due_for_reminder(
    session: AsyncSession, today: date, days_left_values: tuple[int, ...]
) -> list[AdminPurchase]:
    """Active purchases whose ``expires_on - today`` is in ``days_left_values``
    and that were not already reminded today."""
    if not days_left_values:
        return []
    targets = [date.fromordinal(today.toordinal() + delta) for delta in days_left_values]
    rows = await session.execute(
        select(AdminPurchase)
        .where(
            AdminPurchase.expires_on.in_(targets),
            or_(
                AdminPurchase.last_notified_on.is_(None),
                AdminPurchase.last_notified_on < today,
            ),
        )
        .order_by(AdminPurchase.expires_on.asc())
    )
    return list(rows.scalars())
