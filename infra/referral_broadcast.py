#!/usr/bin/env python3
"""Referral promo broadcast - one-off per user, re-sent every THROTTLE_DAYS.

Audience: users who ever took a trial (subscription with empty tariff_key)
OR currently have an active subscription, and have telegram_id + referral_code.

State: /opt/proliv/infra/.referral_broadcast_state.json {tg_id: last_sent_epoch}
Run manually: python3 referral_broadcast.py [--dry-run]
Cron: daily, script self-throttles per user.
"""
import json, os, sys, time, urllib.request, urllib.parse, subprocess
from datetime import datetime, timezone

THROTTLE_DAYS = 14
STATE = '/opt/proliv/infra/.referral_broadcast_state.json'
LOG = '/var/log/referral-broadcast.log'
ENV = '/opt/proliv/shop/.env'

E = {
    'gift': '6032937473162614352',
    'money': '5811989245761426317',
    'people': '5915556996215476302',
    'rocket': '5967432491684860012',
}

def ce(eid, ch):
    return f'<tg-emoji emoji-id="{eid}">{ch}</tg-emoji>'

def log(msg):
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(line)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass

def get_token():
    for line in open(ENV, encoding='utf-8'):
        if line.startswith('BOT_TOKEN='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise RuntimeError('BOT_TOKEN not found')

def get_recipients():
    sql = """
COPY (
  SELECT u.telegram_id, u.referral_code
  FROM users u
  WHERE u.telegram_id IS NOT NULL
    AND u.referral_code IS NOT NULL AND u.referral_code <> ''
    AND (
      EXISTS (SELECT 1 FROM subscriptions s
              WHERE s.user_id = u.user_id
                AND (s.tariff_key IS NULL OR s.tariff_key = ''))
      OR EXISTS (SELECT 1 FROM subscriptions s
                 WHERE s.user_id = u.user_id
                   AND s.is_active AND s.end_date > now())
    )
  ORDER BY u.telegram_id
) TO STDOUT CSV
"""
    out = subprocess.run(
        ['docker', 'exec', 'remnawave-minishop-postgres',
         'psql', '-U', 'remnawave_minishop', '-d', 'remnawave_minishop', '-c', sql],
        capture_output=True, text=True, check=True)
    res = []
    for line in out.stdout.strip().splitlines():
        if not line.strip():
            continue
        tg, code = line.split(',', 1)
        res.append((int(tg), code.strip()))
    return res

def build_payload(tg_id, code):
    ref_link = f'https://t.me/ProlivNetworkBot?start=ref_u{code}'
    text = (
        f'{ce(E["gift"], "🎁")} <b>Приглашай друзей и получай деньги</b>\n\n'
        'Поделись своей реферальной ссылкой - друг регистрируется по ней, а когда он '
        'оплачивает подписку, тебе на бонусный баланс приходит процент от платежа.\n\n'
        f'{ce(E["money"], "💰")} Эти деньги можно потратить на подписку <b>полностью</b> '
        'или обменять на дни - 1 день = 10 ₽.\n\n'
        f'{ce(E["people"], "👥")} Друг тоже получает бонус при переходе по твоей ссылке.\n\n'
        '<b>Твоя ссылка:</b>\n'
        f'<code>{ref_link}</code>\n\n'
        f'{ce(E["rocket"], "🚀")} Чем больше друзей - тем больше денег.'
    )
    share_text = ('VPN с белыми списками и безлимитным трафиком - Proliv Network.\n'
                  'Я уже пользуюсь им! Покупай с 10% скидкой!')
    share_url = 'https://t.me/share/url?' + urllib.parse.urlencode(
        {'url': ref_link, 'text': share_text})
    return {
        'chat_id': tg_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True,
        'reply_markup': {'inline_keyboard': [[
            {'text': 'Пригласить друга', 'url': share_url,
             'icon_custom_emoji_id': E['gift']},
        ]]},
    }

def send(token, payload):
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{token}/sendMessage',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})
    try:
        resp = json.load(urllib.request.urlopen(req, timeout=15))
        return resp.get('ok'), resp.get('description')
    except Exception as e:
        return False, str(e)

def main():
    dry = '--dry-run' in sys.argv
    token = get_token()
    recipients = get_recipients()
    now = time.time()
    throttle = THROTTLE_DAYS * 86400

    state = {}
    if os.path.exists(STATE):
        try:
            state = json.load(open(STATE, encoding='utf-8'))
        except Exception:
            state = {}

    due = []
    for tg, code in recipients:
        last = state.get(str(tg), 0)
        if now - last >= throttle:
            due.append((tg, code))

    log(f'audience={len(recipients)} due={len(due)} dry={dry}')
    if dry:
        for tg, code in due:
            print(f'  would send -> {tg} ref_u{code}')
        return

    ok_n = fail_n = 0
    for tg, code in due:
        payload = build_payload(tg, code)
        ok, desc = send(token, payload)
        if ok:
            state[str(tg)] = now
            ok_n += 1
            log(f'sent -> {tg}')
        else:
            fail_n += 1
            log(f'FAIL -> {tg}: {desc}')
        time.sleep(0.4)

    tmp = STATE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(state, f)
    os.replace(tmp, STATE)
    log(f'done ok={ok_n} fail={fail_n}')

if __name__ == '__main__':
    main()
