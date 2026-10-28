#!/usr/bin/env bash
# Prints TLS ClientHello record length + PQ (0x11ec) presence for incoming hellos from the user IP
timeout 90 tcpdump -i any -nn -s0 -x -c 40 'src host 176.116.143.217 and tcp dst port 443 and (tcp[((tcp[12]&0xf0)>>2)]=0x16)' 2>/dev/null > /tmp/hello.txt
python3 - <<'PY'
import re
pkts=open('/tmp/hello.txt').read().split('\n')
cur=[];out=[]
for line in pkts:
    if re.match(r'^\d\d:\d\d',line):
        if cur: out.append(cur)
        cur=[]
    else:
        cur+=re.findall(r'\b[0-9a-f]{4}\b',line.split(':',1)[1] if ':' in line else '')
if cur: out.append(cur)
for words in out:
    h=''.join(words)
    i=h.find('160301')
    if i<0: continue
    rec=int(h[i+6:i+10],16)
    print('hello record len =',rec,'| PQ x25519mlkem768 =', '11ec' in h[i:])
PY
