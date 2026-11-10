from aiogram import Router

from . import (
    advertiser,
    giveaway,
    notrial,
    promo_user,
    referral,
    start,
    trial_handler,
    winback,
)
from .subscription import router as subscription_router

user_router_aggregate = Router(name="user_router_aggregate")

user_router_aggregate.include_router(advertiser.router)
user_router_aggregate.include_router(winback.router)
user_router_aggregate.include_router(notrial.router)
user_router_aggregate.include_router(promo_user.router)
user_router_aggregate.include_router(giveaway.router)
user_router_aggregate.include_router(trial_handler.router)
user_router_aggregate.include_router(start.router)
user_router_aggregate.include_router(subscription_router)
user_router_aggregate.include_router(referral.router)
