from aiogram import Router

from . import (
    ads,
    broadcast,
    common,
    giveaway,
    ip_check,
    logs_admin,
    nodes_status,
    payments,
    post,
    purchases,
    statistics,
    support_admin,
    sync_admin,
    user_management,
)
from .promo import promo_router_aggregate

admin_router_aggregate = Router(name="admin_features_router")

admin_router_aggregate.include_router(common.router)
admin_router_aggregate.include_router(broadcast.router)
admin_router_aggregate.include_router(promo_router_aggregate)
admin_router_aggregate.include_router(user_management.router)
admin_router_aggregate.include_router(statistics.router)
admin_router_aggregate.include_router(sync_admin.router)
admin_router_aggregate.include_router(logs_admin.router)
admin_router_aggregate.include_router(payments.router)
admin_router_aggregate.include_router(ads.router)
admin_router_aggregate.include_router(nodes_status.router)
admin_router_aggregate.include_router(ip_check.router)
admin_router_aggregate.include_router(support_admin.router)
admin_router_aggregate.include_router(post.router)
admin_router_aggregate.include_router(giveaway.router)
admin_router_aggregate.include_router(purchases.router)

__all__ = ("admin_router_aggregate",)
