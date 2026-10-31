#!/usr/bin/env python3
"""Verify FI patch on /tmp/proliv-data dumps."""
import json

for path in ("/tmp/proliv-data/tariffs.json", "/tmp/proliv-data/locales-overrides.json"):
    d = json.load(open(path, encoding="utf-8"))
    print("==", path)
    if "tariffs" in d:
        for t in d["tariffs"]:
            for lang, s in t.get("descriptions", {}).items():
                print(f"  desc[{lang}]: {s}")
    else:
        for lang, msgs in d.items():
            for k, v in msgs.items():
                if "referral" in k:
                    print(f"  {lang}.{k}: {v.splitlines()[0]}")
