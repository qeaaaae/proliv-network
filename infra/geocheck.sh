#!/usr/bin/env bash
# geo-check: определяет, какую страну видят сервисы с этой ноды.
# Запуск на ноде:  bash <(curl -fsSL https://infra.proliv-network.xyz/geocheck.sh)
# Вывод: построчно  СЕРВИС=CC  и  СЕРВИС=BLOCKED|OK
set -u

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
TO=6 # таймаут curl, сек

q() { # q <url> [extra curl args...]
  curl -fsSL -m "$TO" -A "$UA" "$@" 2>/dev/null
}

echo "# Proliv geo-check $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
echo "PUBLIC_IP=$(q https://ifconfig.co/ip || echo unknown)"

# --- страна по geoip-сервисам ---
echo "IFCONFIG_CC=$(q 'https://ifconfig.co/country-iso' || echo '?')"
echo "IPQUERY_CC=$(q 'https://api.ipquery.io/?format=text' 2>/dev/null | grep -oiE '\b[A-Z]{2}\b' | head -1 || echo '?')"
echo "CLOUDFLARE_LOC=$(q https://www.cloudflare.com/cdn-cgi/trace | sed -n 's/^loc=//p' | head -1)"

# --- сервисные детекции ---
# Google: gl-параметр выдаётся в /search?gws_rd=ssl редиректе/странице
g=$(q 'https://www.google.com/ncr' -D - -o /dev/null | sed -n 's/^Location:.*gl=\([A-Za-z]*\).*/\1/ip' | head -1)
echo "GOOGLE_GL=${g:-?}"

# YouTube: "gl":"XX" в HTML главной
y=$(q 'https://www.youtube.com/' | grep -oE '"gl":"[A-Z]{2}"' | head -1 | cut -d'"' -f4)
echo "YOUTUBE_GL=${y:-?}"

# Gemini: доступность (200/302 = ок; 4xx = заблокирован по региону)
code=$(curl -s -m "$TO" -A "$UA" -o /dev/null -w '%{http_code}' 'https://gemini.google.com/' || echo 000)
echo "GEMINI=$([ "${code#2}" != "$code" ] || [ "$code" = 302 ] && echo OK || echo "BLOCKED($code)")"

# Netflix: 200/302 = доступен каталог региона; запросить заголовки
ncode=$(curl -s -m "$TO" -A "$UA" -o /dev/null -w '%{http_code}' 'https://www.netflix.com/' || echo 000)
echo "NETFLIX=$([ "${ncode#2}" != "$ncode" ] || [ "$ncode" = 301 ] || [ "$ncode" = 302 ] && echo "OK($ncode)" || echo "BLOCKED($ncode)")"

# CDN-приземление: ближайшие edge у популярных CDN
echo "CDN_CLOUDFLARE_EDGE=$(q https://www.cloudflare.com/cdn-cgi/trace | sed -n 's/^colo=//p' | head -1)"
echo "CDN_YOUTUBE_EDGE=$(q -o /dev/null -D - 'https://redirector.googlevideo.com/report_mapping?di=no' 2>/dev/null | sed -n 's/.*cc=\([A-Z]*\).*/\1/ip' | head -1 || echo '?')"
