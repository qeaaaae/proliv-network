import math
from collections.abc import Callable

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from bot.middlewares.i18n import JsonI18n
from config.settings import Settings
from db.models import User


def get_admin_panel_keyboard(
    i18n_instance: JsonI18n, lang: str, settings: Settings
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    # Statistics and monitoring
    builder.button(
        text=_(key="admin_stats_and_monitoring_section"),
        callback_data="admin_section:stats_monitoring",
    )

    # User management
    builder.button(
        text=_(key="admin_user_management_section"), callback_data="admin_section:user_management"
    )

    # Promo codes and marketing
    builder.button(
        text=_(key="admin_promo_marketing_section"), callback_data="admin_section:promo_marketing"
    )

    # Advertising
    builder.button(text=_(key="admin_ads_section"), callback_data="admin_action:ads")

    # System functions
    builder.button(
        text=_(key="admin_system_functions_section"), callback_data="admin_section:system_functions"
    )

    builder.adjust(1)
    return builder.as_markup()


def get_stats_monitoring_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    builder.button(text=_(key="admin_stats_button"), callback_data="admin_action:stats")
    builder.button(
        text=_(key="admin_view_payments_button"), callback_data="admin_action:view_payments"
    )
    builder.button(
        text=_(key="admin_view_logs_menu_button"), callback_data="admin_action:view_logs_menu"
    )

    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_user_management_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_(key="admin_users_management_button"), callback_data="admin_action:users_list:0"
    )
    builder.button(
        text=_(key="admin_users_search_button"), callback_data="admin_action:users_search_prompt"
    )
    builder.button(
        text=_(key="admin_ban_management_section"), callback_data="admin_section:ban_management"
    )
    builder.button(
        text=_(key="admin_user_ratings_button"), callback_data="admin_action:user_ratings"
    )

    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def get_ban_management_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_(key="admin_ban_user_button"), callback_data="admin_action:ban_user_prompt"
    )
    builder.button(
        text=_(key="admin_unban_user_button"), callback_data="admin_action:unban_user_prompt"
    )
    builder.button(
        text=_(key="admin_view_banned_users_button"), callback_data="admin_action:view_banned:0"
    )

    builder.button(
        text=_(key="back_to_user_management_button"), callback_data="admin_section:user_management"
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_promo_marketing_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    builder.button(
        text=_(key="admin_create_promo_button"), callback_data="admin_action:create_promo"
    )
    builder.button(
        text=_(key="admin_create_bulk_promo_button"), callback_data="admin_action:create_bulk_promo"
    )
    builder.button(
        text=_(key="admin_promo_management_button"), callback_data="admin_action:promo_management"
    )

    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_system_functions_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    builder.button(text=_(key="admin_broadcast_button"), callback_data="admin_action:broadcast")
    builder.button(text=_(key="admin_post_button"), callback_data="admin_action:post")
    builder.button(text=_(key="admin_giveaway_button"), callback_data="admin_action:giveaway")
    builder.button(text=_(key="admin_purchases_button"), callback_data="admin_action:purchases")
    builder.button(text=_(key="admin_sync_panel_button"), callback_data="admin_action:sync_panel")
    builder.button(
        text=_(key="admin_queue_status_button"), callback_data="admin_action:queue_status"
    )

    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_post_step_keyboard(
    _: Callable[..., str], skip_callback: str | None = None
) -> InlineKeyboardMarkup:
    """Composer prompts: optional step-skip plus a cancel that exits the flow."""
    builder = InlineKeyboardBuilder()
    if skip_callback:
        builder.button(text=_(key="admin_post_skip_button"), callback_data=skip_callback)
    builder.button(text=_(key="cancel_button"), callback_data="admin_post:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_post_confirm_keyboard(_: Callable[..., str]) -> InlineKeyboardMarkup:
    """Final composer step: test send to the admin, send to group, or cancel."""
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="admin_post_send_test_button"), callback_data="admin_post:send_test")
    builder.button(
        text=_(key="admin_post_send_group_button"), callback_data="admin_post:send_group"
    )
    builder.button(text=_(key="cancel_button"), callback_data="admin_post:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_post_after_test_keyboard(_: Callable[..., str]) -> InlineKeyboardMarkup:
    """Shown after a test send: the draft lives on, so group publish stays open."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_post_send_group_button"), callback_data="admin_post:send_group"
    )
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_post:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_participate_keyboard(
    url: str, label: str, count: int | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text = f"{label} ({count})" if count is not None else label
    # ZWSP keeps a leading Unicode emoji as plain text: the custom-emoji
    # middleware only promotes an emoji that is the whole first token, and a
    # promoted icon does not render on channel posts.
    builder.button(text="\u200b" + text, url=url)
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_menu_keyboard(
    _: Callable[..., str], giveaway_id: int | None, is_active: bool
) -> InlineKeyboardMarkup:
    """Giveaway section root: actions for the latest giveaway plus a new draft."""
    builder = InlineKeyboardBuilder()
    if giveaway_id is not None and is_active:
        builder.button(
            text=_(key="admin_giveaway_participants_button"),
            callback_data=f"admin_giveaway:list:{giveaway_id}:0",
        )
        builder.button(
            text=_(key="admin_giveaway_draw_button"),
            callback_data=f"admin_giveaway:draw:{giveaway_id}",
        )
        builder.button(
            text=_(key="admin_giveaway_schedule_button"),
            callback_data=f"admin_giveaway:schedule:{giveaway_id}",
        )
        builder.button(
            text=_(key="admin_giveaway_setcount_button"),
            callback_data=f"admin_giveaway:setcount:{giveaway_id}",
        )
        builder.button(
            text=_(key="admin_giveaway_cancel_gw_button"),
            callback_data=f"admin_giveaway:cancel_gw:{giveaway_id}",
        )
    builder.button(text=_(key="admin_giveaway_new_button"), callback_data="admin_giveaway:new")
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_step_keyboard(
    _: Callable[..., str], skip_callback: str | None = None
) -> InlineKeyboardMarkup:
    """Composer prompts: optional step-skip plus a cancel that exits the flow."""
    builder = InlineKeyboardBuilder()
    if skip_callback:
        builder.button(text=_(key="admin_post_skip_button"), callback_data=skip_callback)
    builder.button(text=_(key="cancel_button"), callback_data="admin_giveaway:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_confirm_keyboard(_: Callable[..., str]) -> InlineKeyboardMarkup:
    """Final composer step: test send to the admin, publish to group, or cancel."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_post_send_test_button"), callback_data="admin_giveaway:send_test"
    )
    builder.button(
        text=_(key="admin_giveaway_send_group_button"),
        callback_data="admin_giveaway:send_group",
    )
    builder.button(text=_(key="cancel_button"), callback_data="admin_giveaway:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_after_test_keyboard(_: Callable[..., str]) -> InlineKeyboardMarkup:
    """Shown after a test send: the draft lives on, so group publish stays open."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_giveaway_send_group_button"),
        callback_data="admin_giveaway:send_group",
    )
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_giveaway:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_draw_confirm_keyboard(
    _: Callable[..., str], giveaway_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_giveaway_draw_confirm_button"),
        callback_data=f"admin_giveaway:draw_confirm:{giveaway_id}",
    )
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_giveaway:menu")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_cancel_confirm_keyboard(
    _: Callable[..., str], giveaway_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_giveaway_cancel_confirm_button"),
        callback_data=f"admin_giveaway:cancel_confirm:{giveaway_id}",
    )
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_giveaway:menu")
    builder.adjust(1)
    return builder.as_markup()


def get_giveaway_participants_keyboard(
    _: Callable[..., str],
    giveaway_id: int,
    current_page: int,
    total_pages: int,
    is_active: bool,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    row_buttons = []
    if current_page > 0:
        row_buttons.append(
            InlineKeyboardButton(
                text="⬅️ " + _("prev_page_button"),
                callback_data=f"admin_giveaway:list:{giveaway_id}:{current_page - 1}",
            )
        )
    row_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page + 1}/{max(total_pages, 1)}",
            callback_data="admin_giveaway:page_display",
        )
    )
    if current_page < total_pages - 1:
        row_buttons.append(
            InlineKeyboardButton(
                text=_("next_page_button") + " ➡️",
                callback_data=f"admin_giveaway:list:{giveaway_id}:{current_page + 1}",
            )
        )
    builder.row(*row_buttons)
    if is_active:
        builder.button(
            text=_(key="admin_giveaway_draw_button"),
            callback_data=f"admin_giveaway:draw:{giveaway_id}",
        )
    builder.button(text=_(key="admin_giveaway_back_button"), callback_data="admin_giveaway:menu")
    builder.adjust(1)
    return builder.as_markup()


def get_purchases_menu_keyboard(
    _: Callable[..., str],
    purchases: list,
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    """Purchases section root: one button per record plus the add button."""
    builder = InlineKeyboardBuilder()
    for purchase in purchases:
        label = _("admin_purchases_item_button", title=purchase.title)
        builder.button(
            text=label,
            callback_data=f"admin_purchases:card:{purchase.purchase_id}:{current_page}",
        )
    if total_pages > 1:
        row = []
        if current_page > 0:
            row.append(
                InlineKeyboardButton(
                    text="⬅️ " + _("prev_page_button"),
                    callback_data=f"admin_purchases:page:{current_page - 1}",
                )
            )
        row.append(
            InlineKeyboardButton(
                text=f"{current_page + 1}/{total_pages}",
                callback_data="admin_purchases:page_display",
            )
        )
        if current_page < total_pages - 1:
            row.append(
                InlineKeyboardButton(
                    text=_("next_page_button") + " ➡️",
                    callback_data=f"admin_purchases:page:{current_page + 1}",
                )
            )
        builder.row(*row)
    builder.button(text=_(key="admin_purchases_add_button"), callback_data="admin_purchases:new")
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(1)
    return builder.as_markup()


def get_purchase_card_keyboard(
    _: Callable[..., str], purchase_id: int, back_page: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_purchases_renew_button"),
        callback_data=f"admin_purchases:renew:{purchase_id}:{back_page}",
    )
    builder.button(
        text=_(key="admin_purchases_delete_button"),
        callback_data=f"admin_purchases:delete:{purchase_id}:{back_page}",
    )
    builder.button(
        text=_(key="admin_purchases_back_button"),
        callback_data=f"admin_purchases:page:{back_page}",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_purchase_delete_confirm_keyboard(
    _: Callable[..., str], purchase_id: int, back_page: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="admin_purchases_delete_confirm_button"),
        callback_data=f"admin_purchases:delete_confirm:{purchase_id}:{back_page}",
    )
    builder.button(
        text=_(key="admin_purchases_back_button"),
        callback_data=f"admin_purchases:card:{purchase_id}:{back_page}",
    )
    builder.adjust(1)
    return builder.as_markup()


def get_purchase_step_keyboard(
    _: Callable[..., str], skip_callback: str | None = None
) -> InlineKeyboardMarkup:
    """Composer prompts: optional step-skip plus a cancel that exits the flow."""
    builder = InlineKeyboardBuilder()
    if skip_callback:
        builder.button(text=_(key="admin_post_skip_button"), callback_data=skip_callback)
    builder.button(text=_(key="cancel_button"), callback_data="admin_purchases:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_purchase_confirm_keyboard(_: Callable[..., str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="admin_purchases_save_button"), callback_data="admin_purchases:save")
    builder.button(text=_(key="cancel_button"), callback_data="admin_purchases:cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_ads_menu_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="admin_ads_create_button"), callback_data="admin_action:ads_create")
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(1, 1)
    return builder.as_markup()


def get_ads_list_keyboard(
    i18n_instance: JsonI18n,
    lang: str,
    campaigns: list,
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    for c in campaigns:
        title = f"{c.source}"
        builder.button(
            text=title,
            callback_data=f"admin_ads:card:{c.ad_campaign_id}:{current_page}",
        )

    # Pagination row (only when needed)
    if total_pages > 1:
        row = []
        if current_page > 0:
            row.append(
                InlineKeyboardButton(
                    text="⬅️ " + _("prev_page_button"),
                    callback_data=f"admin_ads:page:{current_page - 1}",
                )
            )
        row.append(
            InlineKeyboardButton(
                text=f"{current_page + 1}/{total_pages}",
                callback_data="ads_page_display",
            )
        )
        if current_page < total_pages - 1:
            row.append(
                InlineKeyboardButton(
                    text=_("next_page_button") + " ➡️",
                    callback_data=f"admin_ads:page:{current_page + 1}",
                )
            )
        if row:
            builder.row(*row)

    builder.button(text=_(key="admin_ads_create_button"), callback_data="admin_action:ads_create")
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(1)
    return builder.as_markup()


def get_ad_card_keyboard(
    i18n_instance: JsonI18n, lang: str, campaign_id: int, back_page: int
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    # Dangerous action: Delete campaign
    builder.button(
        text=_(key="admin_ads_delete_button"),
        callback_data=f"admin_ads:delete:{campaign_id}:{back_page}",
    )
    builder.button(
        text=_(key="back_to_ads_list_button"), callback_data=f"admin_ads:page:{back_page}"
    )
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(1)
    return builder.as_markup()


def get_logs_menu_keyboard(i18n_instance: JsonI18n, lang: str) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="admin_view_all_logs_button"), callback_data="admin_logs:view_all:0")
    builder.button(
        text=_(key="admin_view_user_logs_prompt_button"), callback_data="admin_logs:prompt_user"
    )
    builder.button(
        text=_(key="admin_export_logs_csv_button"), callback_data="admin_logs:export_csv"
    )
    builder.row(
        InlineKeyboardButton(
            text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main"
        )
    )
    builder.adjust(2, 1, 1)
    return builder.as_markup()


def get_logs_pagination_keyboard(
    current_page: int,
    total_pages: int,
    base_callback_data: str,
    i18n_instance: JsonI18n,
    lang: str,
    back_to_logs_menu: bool = False,
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    row_buttons = []
    if current_page > 0:
        row_buttons.append(
            InlineKeyboardButton(
                text="⬅️ " + _("prev_page_button"),
                callback_data=f"{base_callback_data}:{current_page - 1}",
            )
        )
    if current_page < total_pages - 1:
        row_buttons.append(
            InlineKeyboardButton(
                text=_("next_page_button") + " ➡️",
                callback_data=f"{base_callback_data}:{current_page + 1}",
            )
        )

    if row_buttons:
        builder.row(*row_buttons)

    if back_to_logs_menu:
        builder.row(
            InlineKeyboardButton(
                text=_(key="admin_logs_menu_title"), callback_data="admin_action:view_logs_menu"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main"
            )
        )
    return builder.as_markup()


def get_banned_users_keyboard(
    banned_users: list[User],
    current_page: int,
    total_banned: int,
    i18n_instance: JsonI18n,
    lang: str,
    settings: Settings,
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    page_size = settings.LOGS_PAGE_SIZE

    if not banned_users and total_banned == 0:
        pass

    for user_row in banned_users:
        user_display_parts = []
        if user_row.first_name:
            user_display_parts.append(user_row.first_name)
        if user_row.username:
            user_display_parts.append(f"(@{user_row.username})")
        elif user_row.email:
            user_display_parts.append(f"({user_row.email})")
        if not user_display_parts:
            user_display_parts.append(f"ID: {getattr(user_row, 'minishop_id', None) or '—'}")

        user_display = " ".join(user_display_parts).strip()

        button_text = _(
            "admin_banned_user_button_text",
            user_display=user_display,
            user_id=getattr(user_row, "minishop_id", None) or "—",
        )
        builder.row(
            InlineKeyboardButton(
                text=button_text, callback_data=f"admin_user_card:{user_row.user_id}:{current_page}"
            )
        )

    if total_banned > page_size:
        total_pages = math.ceil(total_banned / page_size)
        pagination_buttons = []
        if current_page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=_("prev_page_button"),
                    callback_data=f"admin_action:view_banned:{current_page - 1}",
                )
            )
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{current_page + 1}/{total_pages}", callback_data="stub_page_display"
            )
        )
        if current_page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=_("next_page_button"),
                    callback_data=f"admin_action:view_banned:{current_page + 1}",
                )
            )
        if pagination_buttons:
            builder.row(*pagination_buttons)

    builder.row(
        InlineKeyboardButton(
            text=_("back_to_admin_panel_button"), callback_data="admin_action:main"
        )
    )
    return builder.as_markup()


def get_users_list_keyboard(
    users: list[User],
    current_page: int,
    total_users: int,
    i18n_instance: JsonI18n,
    lang: str,
    page_size: int = 15,
) -> InlineKeyboardMarkup:
    """Generate keyboard for paginated user list"""
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    # Add user buttons
    for user in users:
        user_display_parts = []
        if user.username:
            user_display_parts.append(f"@{user.username}")
        elif user.email:
            user_display_parts.append(user.email)
        user_display_parts.append(f"ID: {getattr(user, 'minishop_id', None) or '—'}")
        if user.first_name:
            user_display_parts.append(f"- {user.first_name}")

        button_text = " ".join(user_display_parts)
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"admin_user_card_from_list:{user.user_id}:{current_page}",
            )
        )

    # Pagination buttons
    if total_users > page_size:
        total_pages = math.ceil(total_users / page_size)
        pagination_buttons = []
        if current_page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=_("prev_page_button"),
                    callback_data=f"admin_action:users_list:{current_page - 1}",
                )
            )
        pagination_buttons.append(
            InlineKeyboardButton(
                text=f"{current_page + 1}/{total_pages}", callback_data="stub_page_display"
            )
        )
        if current_page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=_("next_page_button"),
                    callback_data=f"admin_action:users_list:{current_page + 1}",
                )
            )
        if pagination_buttons:
            builder.row(*pagination_buttons)

    # Back button
    builder.row(
        InlineKeyboardButton(
            text=_("back_to_user_management_button"), callback_data="admin_section:user_management"
        )
    )

    return builder.as_markup()


def get_user_card_keyboard(
    user_id: int, is_banned: bool, i18n_instance: JsonI18n, lang: str, banned_list_page: int = 0
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    if is_banned:
        builder.button(
            text=_(key="user_card_unban_button"),
            callback_data=f"admin_unban_confirm:{user_id}:{banned_list_page}",
        )
    else:
        builder.button(
            text=_(key="user_card_ban_button"),
            callback_data=f"admin_ban_confirm:{user_id}:{banned_list_page}",
        )
    builder.button(text=_(key="user_card_open_profile_button"), url=f"tg://user?id={user_id}")
    builder.button(
        text=_(key="user_card_back_to_banned_list_button"),
        callback_data=f"admin_action:view_banned:{banned_list_page}",
    )
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    builder.adjust(1)
    return builder.as_markup()


def get_confirmation_keyboard(
    yes_callback_data: str, no_callback_data: str, i18n_instance: JsonI18n, lang: str
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="yes_button"), callback_data=yes_callback_data)
    builder.button(text=_(key="no_button"), callback_data=no_callback_data)
    return builder.as_markup()


def get_broadcast_confirmation_keyboard(
    lang: str, i18n_instance: JsonI18n, target: str = "all"
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()

    # Row: target selection (all / active / inactive / expired)
    target_all_label = _(key="broadcast_target_all_button")
    target_active_label = _(key="broadcast_target_active_button")
    target_inactive_label = _(key="broadcast_target_inactive_button")
    target_expired_label = _(key="broadcast_target_expired_button")

    # Highlight current selection with a prefix
    def mark_selected(label: str, is_selected: bool) -> str:
        return ("• " + label) if is_selected else label

    builder.button(
        text=mark_selected(target_all_label, target == "all"),
        callback_data="broadcast_target:all",
    )
    builder.button(
        text=mark_selected(target_active_label, target == "active"),
        callback_data="broadcast_target:active",
    )
    builder.button(
        text=mark_selected(target_inactive_label, target == "inactive"),
        callback_data="broadcast_target:inactive",
    )
    builder.button(
        text=mark_selected(target_expired_label, target == "expired"),
        callback_data="broadcast_target:expired",
    )

    # Row: confirmation
    builder.button(
        text=_(key="confirm_broadcast_send_button"), callback_data="broadcast_final_action:send"
    )
    builder.button(
        text=_(key="cancel_broadcast_button"), callback_data="broadcast_final_action:cancel"
    )
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_back_to_admin_panel_keyboard(lang: str, i18n_instance: JsonI18n) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(text=_(key="back_to_admin_panel_button"), callback_data="admin_action:main")
    return builder.as_markup()


def get_back_to_stats_monitoring_keyboard(
    lang: str, i18n_instance: JsonI18n
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="back_to_stats_monitoring_button"),
        callback_data="admin_section:stats_monitoring",
    )
    return builder.as_markup()


def get_back_to_user_management_keyboard(
    lang: str, i18n_instance: JsonI18n
) -> InlineKeyboardMarkup:
    _ = lambda key, **kwargs: i18n_instance.gettext(lang, key, **kwargs)
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_(key="back_to_user_management_button"), callback_data="admin_section:user_management"
    )
    return builder.as_markup()
