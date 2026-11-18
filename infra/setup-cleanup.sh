#!/bin/bash
# Deploys proliv-cleanup (script + cron.d + logrotate tightening + journald cap)
# on a ProlivVPN host, then runs the first cleanup pass.
# Usage: scp proliv-cleanup.sh proliv-cleanup.cron setup-cleanup.sh host:/tmp/pc/
#        ssh host "bash /tmp/pc/setup-cleanup.sh && rm -rf /tmp/pc"
set -u
SRC="$(cd "$(dirname "$0")" && pwd)"

sed -i 's/\r$//' "$SRC/proliv-cleanup.sh" "$SRC/proliv-cleanup.cron"
install -m 755 "$SRC/proliv-cleanup.sh" /usr/local/sbin/proliv-cleanup.sh
install -m 644 "$SRC/proliv-cleanup.cron" /etc/cron.d/proliv-cleanup

# rsyslog: 4 weekly rotations -> 2, cap single file at 300M
if [ -f /etc/logrotate.d/rsyslog ]; then
  sed -i -E 's/^([[:space:]]*)rotate[[:space:]]+4([[:space:]]*)$/\1rotate 2\2\n\1maxsize 300M/' /etc/logrotate.d/rsyslog
fi
# nginx: 14 daily rotations -> 5
if [ -f /etc/logrotate.d/nginx ]; then
  sed -i -E 's/^([[:space:]]*)rotate[[:space:]]+14([[:space:]]*)$/\1rotate 5\2/' /etc/logrotate.d/nginx
fi

# journald hard cap where missing (e.g. fresh hosts)
if ! grep -qsE '^[[:space:]]*SystemMaxUse=' /etc/systemd/journald.conf /etc/systemd/journald.conf.d/*.conf; then
  mkdir -p /etc/systemd/journald.conf.d
  printf '[Journal]\nSystemMaxUse=250M\n' > /etc/systemd/journald.conf.d/10-proliv.conf
  systemctl restart systemd-journald 2>/dev/null || true
fi

echo "--- rsyslog logrotate ---"
grep -nE 'rotate|maxsize' /etc/logrotate.d/rsyslog 2>/dev/null | head -6
echo "--- nginx logrotate ---"
grep -nE 'rotate' /etc/logrotate.d/nginx 2>/dev/null | head -4
echo "--- cron ---"
cat /etc/cron.d/proliv-cleanup

# first cleanup pass now
/usr/local/sbin/proliv-cleanup.sh
tail -20 /var/log/proliv-cleanup.log

# one-time purge of oversized old rotations (won't return under new policy)
echo "--- purging rotated logs >30M ---"
find /var/log -xdev -type f -regextype posix-extended \
  -regex '.+\.[0-9]+(\.gz|\.xz|\.zst)?$' -size +30M -print -delete 2>/dev/null

df -h / | tail -1
echo "SETUP-DONE $(hostname)"
