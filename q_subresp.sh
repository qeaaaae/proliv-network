#!/usr/bin/env bash
set -uo pipefail
SUB="http://127.0.0.1:3444/WKA2c2STkbrb5LHf"

echo "=== HEADERS (Happ UA) ==="
curl -s -D - -o /tmp/sub_happ.json -A 'Happ/5.8.0/ios/2609081608581' "$SUB" | grep -iE 'subscription-userinfo|profile-title|content-type|announce'

echo "=== XRAY_JSON outbounds remarks ==="
python3 -c '
import json
d=json.load(open("/tmp/sub_happ.json"))
def walk(o,path=""):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in ("tag","remarks","remark") and isinstance(v,str):
                print(path+"."+k,"=",repr(v))
            walk(v,path+"."+k)
    elif isinstance(o,list):
        for i,v in enumerate(o):
            walk(v,path+f"[{i}]")
walk(d)
' 2>/dev/null | head -60

echo "=== HEADERS (v2rayN UA - plain sub) ==="
curl -s -D - -o /tmp/sub_plain.txt -A 'v2rayN/7.0' "$SUB" | grep -iE 'subscription-userinfo|profile-title'

echo "=== plain vless remarks ==="
base64 -d /tmp/sub_plain.txt 2>/dev/null | grep -oE '#.*' | head -10
