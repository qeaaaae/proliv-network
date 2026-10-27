"""Generate validated SQL literals for Telegram menu appearance overrides.

Run inside the backend container:
    docker exec -i remnawave-minishop-backend python - < gen_menu_appearance.py
Prints SQL that upserts TELEGRAM_* overrides into app_setting_overrides.
"""

import json

from config.telegram_menu import normalized_telegram_setting

# icon_custom_emoji_id values come from the TgAndroidIcons sticker set
# (https://t.me/addemoji/TgAndroidIcons). Resolved via getStickerSet;
# each id's fallback emoji is noted for maintenance.
APPEARANCE = {
    "schema_version": 1,
    "buttons": {
        "trial": {"style": "success", "icon_custom_emoji_id": "6030822047150512346", "icon_mode": "custom"},  # gift
        "personal_account": {"style": "default", "icon_custom_emoji_id": "6005570495603282482", "icon_mode": "custom"},  # key
        "bot_interface": {"style": "default", "icon_custom_emoji_id": "5931415565955503486", "icon_mode": "custom"},  # robot
        "purchases": {"style": "primary", "icon_custom_emoji_id": "5924720918826848520", "icon_mode": "custom"},  # package
        "subscribe": {"style": "default", "icon_custom_emoji_id": "5924681813149618024", "icon_mode": "custom"},  # wifi/connect
        "my_subscription": {"style": "default", "icon_custom_emoji_id": "5936017305585586269", "icon_mode": "custom"},  # id card
        "payment_history": {"style": "default", "icon_custom_emoji_id": "5967548335542767952", "icon_mode": "custom"},  # card
        "promo": {"style": "default", "icon_custom_emoji_id": "5854776233950188167", "icon_mode": "custom"},  # tag
        "referral": {"style": "default", "icon_custom_emoji_id": "5915556996215476302", "icon_mode": "custom"},  # people
        "language": {"style": "default", "icon_custom_emoji_id": "5879585266426973039", "icon_mode": "custom"},  # globe
        "server_status": {"style": "default", "icon_custom_emoji_id": "5877485980901971030", "icon_mode": "custom"},  # chart
        "support": {"style": "default", "icon_custom_emoji_id": "5886666250158870040", "icon_mode": "custom"},  # chat
        "information": {"style": "default", "icon_custom_emoji_id": "5879785854284599288", "icon_mode": "custom"},  # info
        "back_to_main": {"style": "default", "icon_custom_emoji_id": "5875082500023258804", "icon_mode": "custom"},  # back arrow
        "privacy": {"style": "default", "icon_custom_emoji_id": "5832546462478635761", "icon_mode": "custom"},  # lock
        "user_agreement": {"style": "default", "icon_custom_emoji_id": "5839323457015256759", "icon_mode": "custom"},  # document
    },
}

LIBRARY = {"schema_version": 1, "sets": ["TgAndroidIcons"], "manual_ids": []}

appearance_norm = normalized_telegram_setting("TELEGRAM_MENU_APPEARANCE_JSON", APPEARANCE)
library_norm = normalized_telegram_setting("TELEGRAM_CUSTOM_EMOJI_LIBRARY_JSON", LIBRARY)

# app_setting_overrides.value stores json.dumps() of the normalized string.
sql = f"""INSERT INTO app_setting_overrides (key, value, updated_at, updated_by) VALUES
  ('TELEGRAM_MENU_APPEARANCE_JSON', $${json.dumps(appearance_norm)}$$, now(), NULL),
  ('TELEGRAM_CUSTOM_EMOJI_LIBRARY_JSON', $${json.dumps(library_norm)}$$, now(), NULL)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now(), updated_by = NULL;
"""
print(sql)
