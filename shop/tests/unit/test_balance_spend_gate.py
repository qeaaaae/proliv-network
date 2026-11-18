from __future__ import annotations

import asyncio

from db.dal.referral_payment_dal import has_monthly_subscription_purchase
from db.models import Payment, User


def _payment(
    payment_id: int,
    *,
    user_id: int,
    status: str = "succeeded",
    amount: float = 100,
    sale_mode: str = "subscription",
    months: int | None = 1,
    days: int | None = None,
) -> Payment:
    return Payment(
        payment_id=payment_id,
        user_id=user_id,
        sale_mode=sale_mode,
        status=status,
        amount=amount,
        currency="RUB",
        provider="test",
        subscription_duration_months=months,
        subscription_duration_days=days,
    )


def test_monthly_subscription_purchase_unlocks_balance_spending():
    async def scenario():
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda c: User.metadata.create_all(
                        c, tables=[User.__table__, Payment.__table__]
                    )
                )
            async with async_sessionmaker(engine, expire_on_commit=False)() as session:
                cases = [
                    # user 1: no payments at all
                    # user 2: paid 1-month subscription
                    _payment(2, user_id=2),
                    # user 3: paid day-based subscription of a month or longer
                    _payment(3, user_id=3, sale_mode="subscription@plus", months=None, days=30),
                    # user 4: paid subscription shorter than a month
                    _payment(4, user_id=4, months=None, days=14),
                    # user 5: gift purchase does not unlock spending
                    _payment(5, user_id=5, sale_mode="subscription|gift"),
                    # user 6: non-subscription sale with a duration field
                    _payment(6, user_id=6, sale_mode="traffic"),
                    # user 7: refunded purchase does not count
                    _payment(7, user_id=7, status="refunded"),
                    # user 8: mid-flight success is not a committed purchase
                    _payment(8, user_id=8, status="succeeded_pending_finalization"),
                    # user 9: fully discounted (free) payment does not count
                    _payment(9, user_id=9, amount=0),
                    # user 10: monthly subscription of another user
                    _payment(10, user_id=99),
                ]
                for user_id in range(1, 11):
                    session.add(User(user_id=user_id))
                session.add(User(user_id=99))
                session.add_all(cases)
                await session.flush()

                expected = {
                    1: False,
                    2: True,
                    3: True,
                    4: False,
                    5: False,
                    6: False,
                    7: False,
                    8: False,
                    9: False,
                    10: False,
                }
                for user_id, wanted in expected.items():
                    actual = await has_monthly_subscription_purchase(session, user_id)
                    assert actual == wanted, f"user {user_id}: expected {wanted}"
        finally:
            await engine.dispose()

    asyncio.run(scenario())
