#!/bin/bash
# Proliv node security checklist audit (read-only)
MYIP=$(hostname -I | awk '{print $1}')
case "$MYIP" in
  13.143.192.49) NODE=de; EXP_PUB="22 80 443 8444 2222 2223";;
  31.76.60.63)   NODE=uk; EXP_PUB="22 80 443 8444 2222";;
  31.76.70.98)   NODE=ee; EXP_PUB="22 80 443 8444 2222 2223";;
  179.253.82.201) NODE=fi; EXP_PUB="22 80 443 465 2222 2223";;
  87.58.201.121) NODE=nl; EXP_PUB="22 80 443 8444 2222";;
  79.183.193.149) NODE=kz; EXP_PUB="22 80 443 2222";;
  48.102.213.215) NODE=rf; EXP_PUB="22 80 443";;
  163.245.52.213)   NODE=ee2; EXP_PUB="22 80 443 2222 2223"; SNI_DOMAIN="ee-2.proliv-network.xyz";;
  *) NODE=unknown-$MYIP; EXP_PUB="22 80 443";;
esac
SNI_DOMAIN=${SNI_DOMAIN:-$NODE.proliv-network.xyz}
PANEL=144.31.240.216
echo "###### $NODE ($MYIP) ######"

ok(){ echo "  [OK]   $1"; }
no(){ echo "  [FAIL] $1"; }
wn(){ echo "  [WARN] $1"; }

# 1. Firewall active / default-deny
if [ "$NODE" = "fi" ]; then
  if iptables -L INPUT -n 2>/dev/null | grep -q "PROLIV-IN"; then ok "fw: FI PROLIV-IN chain active"; else no "fw: FI PROLIV-IN missing"; fi
  [ -f /etc/iptables/rules.v4 ] && ok "fw: rules.v4 persistent" || no "fw: rules.v4 missing"
else
  ST=$(ufw status 2>/dev/null | head -1)
  if echo "$ST" | grep -qi active; then ok "fw: ufw active"; else no "fw: ufw $ST"; fi
  ufw status verbose 2>/dev/null | grep -qi "deny (incoming)" && ok "fw: default deny incoming" || no "fw: default policy NOT deny-incoming"
fi

# 2. Public listeners vs expected set
echo "  -- listeners (non-127.0.0.1):"
ss -tlnp 2>/dev/null | awk 'NR>1{split($4,a,":");p=a[length(a)];if($4 !~ /127\.|::1|172\.(1[6-9]|2[0-9]|3[01])\./)print p,$7}' | sort -un | while read p proc; do
  exp=no; for e in $EXP_PUB; do [ "$p" = "$e" ] && exp=yes; done
  short=$(echo "$proc" | grep -oE '"[a-zA-Z0-9_.-]+"' | head -1 | tr -d '"')
  [ "$exp" = yes ] && echo "  [OK]   port $p ($short) expected" || echo "  [FAIL] port $p ($short) UNEXPECTED - not in allowlist"
done

# 3. NODE_PORT only from panel
for np in 2222 2223; do
  if ss -tln 2>/dev/null | grep -q ":$np "; then
    if [ "$NODE" = "fi" ]; then
      if iptables -L PROLIV-IN -n 2>/dev/null | grep "$np" | grep -q "$PANEL"; then ok "nodeport $np: panel-only (PROLIV-IN)"; else no "nodeport $np: no panel-only rule"; fi
    else
      R=$(ufw status 2>/dev/null | grep -E "^$np")
      if echo "$R" | grep -q "$PANEL"; then
        echo "$R" | grep -q "ALLOW.*Anywhere\|ALLOW.*0.0.0.0" && no "nodeport $np: world-open in ufw" || ok "nodeport $np: ufw panel-only"
      else
        [ -z "$R" ] && no "nodeport $np: listening but NO ufw rule (world-open if ufw default allow?)" || wn "nodeport $np: rule='$R'"
      fi
      iptables -L DOCKER-USER -n 2>/dev/null | grep "$np" | grep -q DROP && ok "nodeport $np: DOCKER-USER drop present" || wn "nodeport $np: no DOCKER-USER drop (docker publish bypasses ufw)"
    fi
  fi
done

# 4. NL socks :8444 restricted to node IPs
if [ "$NODE" = "nl" ]; then
  N=$(ufw status 2>/dev/null | grep -c "^8444.*ALLOW")
  BAD=$(ufw status 2>/dev/null | grep "^8444.*ALLOW.*Anywhere" | wc -l)
  [ "$BAD" -gt 0 ] && no "nl:8444 socks world-open" || ok "nl:8444 socks restricted ($N allow-rules)"
fi
# on other nodes 8444 = CDN-origin (yccdn dynamic edge IPs, 404 foreign host) - just note
if [ "$NODE" = "de" ] || [ "$NODE" = "uk" ] || [ "$NODE" = "ee" ]; then
  CODE=$(curl -sk -o /dev/null -w '%{http_code}' --connect-timeout 3 -H 'Host: evil.example.com' https://127.0.0.1:8444/ 2>/dev/null)
  [ "$CODE" = "404" ] && ok ":8444 CDN-origin 404 on foreign Host ($CODE)" || wn ":8444 foreign Host -> $CODE"
fi

# 5. ping closed
if [ "$NODE" = "fi" ]; then
  iptables -L PROLIV-IN -n 2>/dev/null | grep -q "icmp.*echo\|icmp.*DROP" && ok "ping: drop rule present (FI)" || wn "ping: check manually"
  sysctl -n net.ipv4.icmp_echo_ignore_all 2>/dev/null | grep -q 1 && ok "ping: icmp_echo_ignore_all=1" || wn "ping: icmp_echo_ignore_all!=1"
else
  sysctl -n net.ipv4.icmp_echo_ignore_all 2>/dev/null | grep -q 1 && ok "ping: icmp_echo_ignore_all=1" || wn "ping: sysctl not ignoring"
  iptables -L INPUT -n 2>/dev/null | grep -iE "icmp.*DROP|icmp.*echo|icmptype 8" | head -1 | grep -q . && ok "ping: iptables drop/echo rule" || wn "ping: no explicit drop found"
fi

# 6. fail2ban
FB=$(fail2ban-client status 2>/dev/null | grep "Jail list" | tr -d ' ')
echo "  -- fail2ban jails: ${FB##*:}"
echo "$FB" | grep -q sshd && ok "f2b: sshd jail" || no "f2b: sshd jail missing"
echo "$FB" | grep -q portscan && ok "f2b: portscan jail" || no "f2b: portscan jail missing"
if grep -q "ignoreregex.*DPT" /etc/fail2ban/filter.d/portscan.conf 2>/dev/null; then ok "f2b: portscan ignoreregex DPT (no user false-bans)"; else no "f2b: portscan ignoreregex MISSING (user false-ban risk!)"; fi
BANNED=$(fail2ban-client status portscan 2>/dev/null | grep "Banned IP" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | wc -l)
echo "  -- f2b portscan currently banned: $BANNED"

# 7. Self-steal / decoys
P443=$(ss -tlnp 2>/dev/null | grep ":443 " | grep -oE '"[a-zA-Z0-9_.-]+"' | head -1 | tr -d '"')
if [ "$NODE" = "rf" ]; then
  [ "$P443" = "nginx" ] && ok ":443 = nginx stream relay (RF arch)" || wn ":443 = $P443"
else
  echo "$P443" | grep -qE "xray|rw-core|rw-node" && ok ":443 = $P443 (REALITY self-steal)" || no ":443 = $P443 - NOT reality (deanon!)"
fi
# bogus SNI to 443 -> should NOT return our domain cert
CERTCN=$(echo | timeout 5 openssl s_client -connect 127.0.0.1:443 -servername totally-bogus-sni.invalid 2>/dev/null | openssl x509 -noout -subject 2>/dev/null | grep -oE 'CN *= *[^,]*')
echo "  -- bogus SNI :443 cert: ${CERTCN:-no cert / reset}"
[ "$NODE" != "rf" ] && { echo "$CERTCN" | grep -qi "proliv-network" && no "bogus SNI leaks domain cert!" || ok "bogus SNI no domain leak"; }
# TLS1.3 to steal-dest :8443 (NL incident regression)
if ss -tln 2>/dev/null | grep -q "127.0.0.1:8443"; then
  T13=$(echo | timeout 5 openssl s_client -connect 127.0.0.1:8443 -servername $SNI_DOMAIN -tls1_3 2>/dev/null | grep -m1 -oE "TLSv1\.[0-9]")
  [ "$T13" = "TLSv1.3" ] && ok "steal-dest :8443 negotiates TLS1.3" || no "steal-dest :8443 NO TLS1.3 ($T13) - reality mimicry broken!"
fi
# decoy on :80
D80=$(curl -sk -o /dev/null -w '%{http_code}' --connect-timeout 3 http://127.0.0.1:80/ 2>/dev/null)
[ "$D80" = "200" ] || [ "$D80" = "301" ] || [ "$D80" = "302" ] && ok ":80 decoy site responds ($D80)" || wn ":80 -> $D80"

# 8. sshd hardening
PA=$(sshd -T -C user=root,host=x,addr=x 2>/dev/null | grep -i passwordauthentication | awk '{print $2}')
PR=$(sshd -T -C user=root,host=x,addr=x 2>/dev/null | grep -i permitrootlogin | awk '{print $2}')
[ "$PA" = "no" ] && ok "sshd: PasswordAuthentication no" || no "sshd: PasswordAuthentication $PA"
echo "$PR" | grep -qE "prohibit-password|without-password|no" && ok "sshd: PermitRootLogin $PR" || no "sshd: PermitRootLogin $PR"
if [ "$NODE" != "fi" ]; then ufw status 2>/dev/null | grep -qE "^22/tcp.*LIMIT|22.*LIMIT" && ok "sshd: 22 rate-limited" || wn "sshd: no ufw limit on 22"; fi

# extras: containers + node agent
docker ps --format '{{.Names}} {{.Status}}' 2>/dev/null | grep -E "remnanode|xray" | while read l; do echo "  -- container: $l"; done
uptime | awk -F'load average' '{print "  -- load:"$2}'
echo ""
