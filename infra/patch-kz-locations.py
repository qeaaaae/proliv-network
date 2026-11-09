#!/usr/bin/env python3
"""One-off: add Kazakhstan to location lists in minishop /app/data files.

Patches descriptions in tariffs.json and purchase/referral texts in
locales-overrides.json by string replacement (keeps all other prod
values - topup prices, bonus wording - untouched).
Usage: python3 patch-kz-locations.py <file> [<file> ...]
"""
import json
import sys

REPLACEMENTS = [
    # tariff descriptions
    ("UK, Эстония, Германия, Финляндия, Нидерланды.", "UK, Эстония, Германия, Финляндия, Нидерланды, Казахстан."),
    ("UK, Estonia, Germany, Finland, Netherlands.", "UK, Estonia, Germany, Finland, Netherlands, Kazakhstan."),
    # purchase description
    ("<b>5 локаций</b> с портом 10 Гбит/с — Эстония, Великобритания, Германия, Финляндия, Нидерланды", "<b>6 локаций</b> с портом до 10 Гбит/с — Эстония, Великобритания, Германия, Финляндия, Нидерланды, Казахстан"),
    ("<b>5 locations</b> on 10 Gbit/s ports — Estonia, UK, Germany, Finland, Netherlands", "<b>6 locations</b> on ports up to 10 Gbit/s — Estonia, UK, Germany, Finland, Netherlands, Kazakhstan"),
    # referral share/friend texts
    ("в UK, Эстонии, Германии, Финляндии и Нидерландах.", "в UK, Эстонии, Германии, Финляндии, Нидерландах и Казахстане."),
    ("in the UK, Estonia, Germany, Finland and the Netherlands.", "in the UK, Estonia, Germany, Finland, the Netherlands and Kazakhstan."),
]


def patch(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    changed = 0
    for old, new in REPLACEMENTS:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            changed += n
    # валидация: остаётся валидным JSON и структура не меняется
    json.loads(text)
    if not changed:
        print(f"{path}: nothing to patch")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{path}: {changed} replacement(s)")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        patch(p)
