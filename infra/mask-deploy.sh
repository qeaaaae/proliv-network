#!/bin/bash
set -e
DOM="p.proliv-network.xyz"

# 1. cert через существующий webroot на :80
certbot certonly --webroot -w /var/www/acme --non-interactive --agree-tos --register-unsafely-without-email -d $DOM

# 2. mask site
mkdir -p /var/www/mask
cat > /var/www/mask/index.html <<'EOF'
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Filebox - обмен файлами</title>
<style>
*{box-sizing:border-box;margin:0;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}
body{background:#0e0f12;color:#e8e9eb;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:#17191f;border:1px solid #26292f;border-radius:16px;max-width:560px;width:100%;padding:32px}
.brand{color:#8ab4f8;font-size:13px;letter-spacing:2px;text-transform:uppercase}
h1{font-size:28px;margin:8px 0 4px}
.sub{color:#9aa0a6;font-size:14px;margin-bottom:24px}
.drop{border:2px dashed #3c4047;border-radius:12px;padding:48px 20px;text-align:center;color:#9aa0a6;cursor:pointer}
.drop svg{display:block;margin:0 auto 12px;opacity:.6}
.row{display:flex;gap:10px;margin:16px 0}
.opt{flex:1;background:#1e2128;border:1px solid #2c2f36;border-radius:10px;padding:12px;font-size:13px;color:#c8cad0}
.linkrow{display:flex;margin-top:8px}
.linkrow input{flex:1;background:#1e2128;border:1px solid #2c2f36;border-radius:10px 0 0 10px;padding:12px;color:#9aa0a6;font-size:14px}
.linkrow button{background:#3c4047;border:none;border-radius:0 10px 10px 0;color:#e8e9eb;padding:0 16px;cursor:pointer}
.foot{margin-top:20px;font-size:12px;color:#5f6368}
</style>
</head>
<body>
<div class="card">
<div class="brand">Filebox</div>
<h1>Отправить файл</h1>
<div class="sub">Добавьте файл и выберите параметры ссылки</div>
<div class="drop">
<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 16V4m0 0l-4 4m4-4l4 4"/><path d="M4 20h16"/></svg>
Перетащите файл в это поле<br><small>или нажмите для выбора - до 2 ГБ</small>
</div>
<div class="row">
<div class="opt">Срок хранения<br><b>24 часа</b></div>
<div class="opt">Доступ<br><b>По ссылке</b></div>
</div>
<div class="linkrow"><input readonly value="Ссылка появится после загрузки"><button>+</button></div>
<div class="foot">Filebox - быстрый обмен файлами без регистрации</div>
</div>
</body>
</html>
EOF

# 3. nginx вхост для p.* только на localhost:8444
cat > /etc/nginx/sites-available/mask-p <<EOF
server {
    listen 127.0.0.1:8444 ssl;
    server_name $DOM;
    ssl_certificate     /etc/letsencrypt/live/$DOM/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOM/privkey.pem;
    root /var/www/mask;
    index index.html;
    location / { try_files \$uri \$uri/ =404; }
}
EOF
ln -sf /etc/nginx/sites-available/mask-p /etc/nginx/sites-enabled/mask-p
nginx -t && systemctl reload nginx

# 4. telemt: домен + маска
sed -i 's/^tls_domain = ".*"/tls_domain = "'$DOM'"/' /etc/telemt/telemt.toml
grep -q '^mask ' /etc/telemt/telemt.toml || sed -i '/^tls_domain/a mask = true\nmask_port = 8444\nmask_host = "127.0.0.1"' /etc/telemt/telemt.toml
systemctl restart telemt
sleep 3

# 5. пинги офф + fail2ban
iptables -C INPUT -p icmp --icmp-type echo-request -j DROP 2>/dev/null || iptables -I INPUT -p icmp --icmp-type echo-request -j DROP
apt-get install -y -qq iptables-persistent >/dev/null 2>&1 || true
systemctl enable --now fail2ban >/dev/null 2>&1 || true

echo "=== STATUS ==="
grep -nE 'tls_domain|mask' /etc/telemt/telemt.toml
systemctl status telemt --no-pager | head -6
journalctl -u telemt -n 15 --no-pager | grep -iE 'tls|mask|error|fail' | tail -8
