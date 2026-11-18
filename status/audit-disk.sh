echo "###HOST $(hostname) $(date -Is)"
echo "--- df -h ---"
df -h -x tmpfs -x devtmpfs -x overlay 2>/dev/null
echo "--- docker system df ---"
docker system df 2>/dev/null
echo "--- docker images ---"
docker images -a --format '{{.Repository}}:{{.Tag}}  {{.Size}}  {{.CreatedSince}}' 2>/dev/null | head -40
echo "--- dangling images count ---"
docker images -f dangling=true -q 2>/dev/null | wc -l
echo "--- stopped containers ---"
docker ps -a --filter status=exited --format '{{.Names}}  {{.Status}}' 2>/dev/null
echo "--- builder cache (last lines) ---"
docker builder du 2>/dev/null | tail -3
echo "--- journal disk usage ---"
journalctl --disk-usage 2>/dev/null
echo "--- journald limits ---"
grep -E '^(SystemMaxUse|RuntimeMaxUse)' /etc/systemd/journald.conf 2>/dev/null
echo "--- /var/log size ---"
du -sh /var/log 2>/dev/null
echo "--- big files in /var/log ---"
find /var/log -type f -size +20M -printf '%s %p\n' 2>/dev/null | sort -rn | head -10
echo "--- apt cache ---"
du -sh /var/cache/apt 2>/dev/null
echo "--- tmp dirs ---"
du -sh /tmp /var/tmp 2>/dev/null
echo "--- top dirs /var ---"
du -xh -d1 /var 2>/dev/null | sort -rh | head -8
echo "--- top dirs /opt ---"
du -xh -d1 /opt 2>/dev/null | sort -rh | head -8
echo "--- top dirs /root ---"
du -xh -d1 /root 2>/dev/null | sort -rh | head -8
echo "--- docker volumes ---"
docker system df -v 2>/dev/null | awk '/VOLUME NAME/{f=1;next}/Build cache/{f=0}f' | head -30
echo "--- installed kernels ---"
dpkg -l 'linux-image-*' 2>/dev/null | grep ^ii | wc -l
echo "--- apt autoremove candidates ---"
apt-get -s autoremove 2>/dev/null | grep -c '^Remv'
echo "--- crash dumps ---"
ls -lh /var/crash 2>/dev/null | head -5
find / -xdev -name 'core*' -type f -size +10M 2>/dev/null | head -5
echo "--- rotated/compressed logs count ---"
ls /var/log/*.gz /var/log/*.1 2>/dev/null | wc -l
echo "###END"
