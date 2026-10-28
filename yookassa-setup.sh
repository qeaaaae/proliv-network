#!/bin/bash
# Proliv - подключение ЮKassa
# Запуск: bash /opt/proliv/yookassa-setup.sh
set -e

ENV=/opt/proliv/shop/.env
SHOP=/opt/proliv/shop
COMPOSE="-f docker-compose.yml -f /opt/proliv/infra/minishop.compose.yml -f /opt/proliv/infra/minishop.prod.compose.yml"

echo "=== ЮKassa - настройка оплаты ==="
echo "Данные берутся в личном кабинете ЮKassa: https://yookassa.ru/my"
echo

read -rp "Shop ID (shopId, число): " SHOP_ID
[ -z "$SHOP_ID" ] && { echo "Пусто - выход"; exit 1; }

read -rp "Секретный ключ (secret_key, вида live_...): " SECRET
[ -z "$SECRET" ] && { echo "Пусто - выход"; exit 1; }

read -rp "Email для чеков по умолчанию [Enter = пропустить]: " RECEIPT

setvar() {
  if grep -q "^$1=" "$ENV"; then
    sed -i "s|^$1=.*|$1=$2|" "$ENV"
  else
    echo "$1=$2" >> "$ENV"
  fi
}

setvar YOOKASSA_ENABLED True
setvar YOOKASSA_SHOP_ID "$SHOP_ID"
setvar YOOKASSA_SECRET_KEY "$SECRET"
setvar YOOKASSA_RETURN_URL "https://app.proliv-network.xyz/purchases"
[ -n "$RECEIPT" ] && setvar YOOKASSA_DEFAULT_RECEIPT_EMAIL "$RECEIPT"
grep -q '^YOOKASSA_VAT_CODE=' "$ENV" || setvar YOOKASSA_VAT_CODE 6

echo
echo ">>> Записано в $ENV:"
grep '^YOOKASSA_' "$ENV" | sed 's/SECRET_KEY=.*/SECRET_KEY=***скрыт***/'

echo
echo ">>> Пересоздаю backend и bot..."
cd "$SHOP"
docker compose $COMPOSE up -d backend bot 2>&1 | tail -3

sleep 8
echo
echo ">>> Проверка:"
docker exec remnawave-minishop-backend env | grep -q 'YOOKASSA_ENABLED=True' \
  && echo "OK - backend видит YOOKASSA_ENABLED=True" \
  || echo "ОШИБКА - env не подхватился, проверь контейнер"

CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST https://api.proliv-network.xyz/webhook/yookassa -d '{}')
echo "Webhook /webhook/yookassa -> HTTP $CODE (403 = роут жив, подпись проверяется)"

echo
echo ">>> Осталось в личном кабинете ЮKassa:"
echo "  Настройки -> Уведомления -> URL для уведомлений:"
echo "  https://api.proliv-network.xyz/webhook/yookassa"
echo
echo "Проверь в кабинете https://app.proliv-network.xyz/purchases -"
echo "должен появиться 'Способ оплаты: ЮKassa' и активная кнопка."
