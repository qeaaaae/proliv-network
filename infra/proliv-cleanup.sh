#!/bin/bash
# ProlivVPN weekly cleanup. Installed at /usr/local/sbin/proliv-cleanup.sh,
# scheduled via /etc/cron.d/proliv-cleanup. Safe to run manually anytime.
set -u
export DEBIAN_FRONTEND=noninteractive
LOG=/var/log/proliv-cleanup.log
exec >>"$LOG" 2>&1

echo "===== $(date -Is) cleanup start ($(hostname)) ====="
df -h / | tail -1

# journald: vacuum to 100M (SystemMaxUse=250M remains the hard cap)
journalctl --vacuum-size=100M

# apt cache + orphaned packages (keeps current + previous kernel)
if command -v apt-get >/dev/null; then
  apt-get clean -y
  apt-get -y autoremove --purge
fi

# tmp files older than 7d
find /tmp /var/tmp -xdev -type f -atime +7 -delete 2>/dev/null

# crash dumps older than 7d
find /var/crash -xdev -type f -mtime +7 -delete 2>/dev/null

# rotated/compressed logs older than 14d (syslog.1, *.2.gz, dpkg.log.1, ...)
find /var/log -xdev -type f -regextype posix-extended \
  -regex '.+\.[0-9]+(\.gz|\.xz|\.zst|\.old)?$' -mtime +14 -delete 2>/dev/null

# docker, if present and running
if command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  docker container prune -f --filter until=168h
  docker image prune -f
  docker image prune -a -f --filter until=720h
  docker volume prune -f
  docker builder prune -af --keep-storage 1GB
fi

echo "----- df after cleanup -----"
df -h / | tail -1
echo "===== $(date -Is) cleanup done ====="
