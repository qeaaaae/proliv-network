from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    confirming_broadcast = State()
    waiting_for_promo_details = State()
    waiting_for_promo_code = State()
    waiting_for_promo_type = State()
    waiting_for_promo_bonus_days = State()
    waiting_for_promo_discount = State()
    waiting_for_promo_max_activations = State()
    waiting_for_promo_validity_days = State()
    waiting_for_promo_edit_details = State()
    waiting_for_promo_edit_code = State()
    waiting_for_promo_edit_bonus_days = State()
    waiting_for_promo_edit_max_activations = State()
    waiting_for_promo_edit_validity_days = State()
    waiting_for_bulk_promo_quantity = State()
    waiting_for_bulk_promo_bonus_days = State()
    waiting_for_bulk_promo_max_activations = State()
    waiting_for_bulk_promo_validity_days = State()
    waiting_for_user_id_to_ban = State()
    waiting_for_user_id_to_unban = State()

    waiting_for_user_id_for_logs = State()

    # User management states
    waiting_for_user_search = State()
    waiting_for_subscription_days_to_add = State()
    waiting_for_direct_message_to_user = State()
    waiting_for_user_delete_confirmation = State()
    waiting_for_premium_override_bonus_gb = State()
    waiting_for_traffic_grant_gb = State()
    waiting_for_hwid_device_limit = State()

    # Support tickets
    waiting_for_support_reply = State()

    # Ads campaigns
    waiting_for_ad_source = State()
    waiting_for_ad_start_param = State()
    waiting_for_ad_cost = State()

    # Admin post composer
    waiting_for_post_text = State()
    waiting_for_post_image = State()
    waiting_for_post_button_url = State()
    waiting_for_post_button_label = State()
    confirming_post = State()

    # Admin giveaway composer
    waiting_for_giveaway_text = State()
    waiting_for_giveaway_image = State()
    waiting_for_giveaway_schedule = State()
    waiting_for_giveaway_reschedule = State()
    waiting_for_giveaway_counter = State()
    confirming_giveaway = State()

    # Admin purchases (expense tracker)
    waiting_for_purchase_provider = State()
    waiting_for_purchase_title = State()
    waiting_for_purchase_price = State()
    waiting_for_purchase_note = State()
    waiting_for_purchase_paid_on = State()
    waiting_for_purchase_period = State()
    confirming_purchase = State()
    waiting_for_purchase_renew_paid_on = State()
    waiting_for_purchase_renew_price = State()
    waiting_for_purchase_renew_period = State()
