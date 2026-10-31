#!/usr/bin/env python3
"""One-off: add Finland to location lists in minishop /app/data files.

Patches descriptions in tariffs.json and referral texts in
locales-overrides.json by string replacement (keeps all other prod
values - topup prices, bonus wording - untouched).
Usage: python3 patch-fi-locations.py <file> [<file> ...]
"""
import json
import sys

REPLACEMENTS = [
    ("UK, Эстония, Германия.", "UK, Эстония, Германия, Финляндия."),
    ("UK, Estonia, Germany.", "UK, Estonia, Germany, Finland."),
    ("UK, Эстонии и Германии", "UK, Эстонии, Германии и Финляндии"),
    ("the UK, Estonia and Germany", "the UK, Estonia, Germany and Finland"),
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
