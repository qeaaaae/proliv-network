#!/bin/bash
# Проверяем hwidDeviceLimit юзеров в панели Remnawave
KEY=$(docker exec remnawave-minishop-backend printenv PANEL_API_KEY)
USERS=$(curl -s -H "Authorization: Bearer $KEY" -H 'X-Forwarded-For: 127.0.0.1' -H 'X-Forwarded-Proto: https' "http://127.0.0.1:3443/api/users?size=50")
echo "$USERS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
users=d.get('response',{}).get('users') or d.get('users') or []
for u in users:
    print(u.get('username'), '| hwidDeviceLimit=', u.get('hwidDeviceLimit'), '| status=', u.get('status'), '| uuid=', u.get('uuid'))
"
