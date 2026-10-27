"""Wrap decorative unicode emojis in locales with <tg-emoji> tags.

Telegram renders <tg-emoji emoji-id="ID">FALLBACK</tg-emoji> as a custom
emoji (HTML parse mode); the bot's CustomEmojiFallbackMiddleware strips the
tags back to the fallback char when custom emoji are unavailable.

Only user-facing text keys are touched. Skipped:
- *_button labels (button text is plain, tg-emoji would render literally)
- admin_/log_/wa_/webapp_/menu_/broadcast_/advertiser_ keys (web/admin UI)
- emojis inside <code>/<pre> (tg-emoji is not allowed there)

Icon IDs come from infra/TgAndroidIcons.txt (getStickerSet dump).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "infra" / "TgAndroidIcons.txt"
LOCALES = ROOT / "shop" / "locales"

BASE = r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF\u2300-\u23FF\u2B50\u2934-\u2935\u3030\u303D\u3297\u3299]"
EMOJI_SEQ = re.compile(BASE + r"(?:\ufe0f|\u200d" + BASE + r"\ufe0f?)*")
CODE_REGION = re.compile(
    r"<code>.*?</code>|<pre>.*?</pre>|<tg-emoji\b[^>]*>.*?</tg-emoji>", re.DOTALL
)

# Emojis missing from the icon set, mapped to the closest available icon.
ALIASES = {
    "🔐": "🔒",  # lock
    "📆": "📅",  # calendar
    "⏳": "⏰",  # time
    "🕐": "⏰",
    "⛔": "🚫",
    "🛑": "🚫",
    "🚀": "🛜",
    "📡": "📶",
    "😴": "💤",
    "🖥": "📱",
    "📜": "🗒",
    "🆘": "❓",
    "↩️": "🔄",
    "🟢": "✅",
    "👇": "🔽",
}

SKIP_PREFIXES = (
    "admin_",
    "log_",
    "wa_",
    "webapp_",
    "broadcast_",
    "advertiser_",
    "menu_",
    "maintenance_",
    "sync_",
    "inline_admin_",
    "user_card_",
)


def load_map() -> dict[str, str]:
    emoji_to_id: dict[str, str] = {}
    for line in ICONS.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        cid, emoji = line.split("\t", 1)
        emoji_to_id.setdefault(emoji, cid)
    return emoji_to_id


def convert_segment(segment: str, emoji_to_id: dict[str, str]) -> tuple[str, int]:
    def repl(match: re.Match) -> str:
        seq = match.group(0)
        cid = emoji_to_id.get(seq) or emoji_to_id.get(seq.rstrip("\ufe0f"))
        if not cid:
            alias = ALIASES.get(seq) or ALIASES.get(seq.rstrip("\ufe0f"))
            if alias:
                cid = emoji_to_id.get(alias) or emoji_to_id.get(alias.rstrip("\ufe0f"))
        if not cid:
            return seq
        return f'<tg-emoji emoji-id="{cid}">{seq}</tg-emoji>'

    out, count = EMOJI_SEQ.subn(repl, segment)
    return out, count


def convert_value(value: str, emoji_to_id: dict[str, str]) -> tuple[str, int]:
    total = 0
    parts: list[str] = []
    pos = 0
    for m in CODE_REGION.finditer(value):
        out, n = convert_segment(value[pos : m.start()], emoji_to_id)
        parts.append(out)
        parts.append(m.group(0))
        pos = m.end()
        total += n
    out, n = convert_segment(value[pos:], emoji_to_id)
    parts.append(out)
    total += n
    return "".join(parts), total


def main() -> int:
    emoji_to_id = load_map()
    changed_keys: list[str] = []
    total_wrapped = 0
    for locale in ("ru.json", "en.json"):
        path = LOCALES / locale
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if not isinstance(value, str):
                continue
            if key.startswith(SKIP_PREFIXES) or "_button" in key:
                continue
            new_value, n = convert_value(value, emoji_to_id)
            if n and new_value != value:
                data[key] = new_value
                changed_keys.append(f"{locale}:{key}")
                total_wrapped += n
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"wrapped {total_wrapped} emojis across {len(changed_keys)} keys")
    for k in changed_keys:
        print(" ", k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
