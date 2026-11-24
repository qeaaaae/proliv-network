# Гигиена серверов: аудит и чистка (2026-11-17)

Проверены все 8 хостов: `proliv-main` + ноды DE/EE/FI/UK/NL/KZ/RF
(LTE-ноды — контейнеры `remnanode-lte` на тех же VPS DE/EE/FI, отдельно
не проверялись — делят диск с основной нодой).

## Диски после чистки

| Хост | Размер | Было занято | Стало | Что было главного |
|---|---|---|---|---|
| proliv-main | 45G | 11G (27%) | ~10.5G | docker build cache 947M, journal 122M |
| DE | 25G | 5.9G (26%) | ~5.6G | journal 251M, syslog 149M (warp-спам) |
| EE | 25G | 6.2G (27%) | ~5.9G | journal 238M, syslog 148M (warp-спам) |
| FI | 25G | 6.9G (30%) | ~6.5G | **xhttp_hdr.log 426M без ротации**, syslog 550M (telemt+warp спам), btmp 31M |
| UK | 25G | 4.9G (21%) | ~4.7G | journal 204M |
| NL | **9.8G** | 4.7G (50%) | ~4.4G (48%) | journal 212M, **snap lxd ~1.7G** |
| KZ | 15G | 4.9G (35%) | ~4.6G | journal 227M |
| RF | 20G | 3.9G (21%) | ~3.8G | journal 85M |

Диски не критичны. Единственный тесный — **NL (9.8G, ~48%)**.

## Что почищено 17.11

1. **apt-кэш** `apt-get clean` на всех — ~113-167M на хост.
2. **journald**: `journalctl --rotate` + `--vacuum-size=80M` —
   на нодах было 200-260M, стало 38-80M. На main 122M→79M, KZ -125M.
   vacuum-size без rotate не работает (archives=0, всё в active-файле).
3. **Docker на main**: `docker builder prune -af` — освобождено
   **947MB** build-кэша. `docker image prune -f` (dangling) — 0B,
   dangling-образов не было.
4. **FI `/var/log/nginx/xhttp_hdr.log`** — диагностический лог заголовков
   xhttp (добавлен 12.11 под инцидент 431), ротации не было → 426M за 5
   дней. Добавлен `/etc/logrotate.d/xhttp-hdr`: daily, rotate 3, compress,
   copytruncate, size 50M. Прогнан `logrotate -f`.
5. **FI `/var/log/btmp`** — 31Mfailed-логинов, обнулён (`> btmp`).
6. **Спам warp-svc в syslog** (DE/EE/FI/NL): `warp-svc` пишет DEBUG-строки
   каждые ~3 сек → ~150-350M/нед в syslog. Добавлен
   `/etc/rsyslog.d/49-warp-svc.conf` = `:programname, isequal, "warp-svc" stop`
   + `systemctl restart rsyslog`. Проверено: после рестарта новых
   warp-svc строк в syslog нет. Логи warp остаются в
   `/var/log/cloudflare-warp/` и journald — ничего не потеряно.
7. **FI telemt**: `log_level = "verbose"` в `/etc/telemt/telemt.toml`
   спамил DEBUG в syslog (355k строк). Поставлено `"normal"` (валидные
   значения: debug/verbose/normal/silent — `"info"` НЕ существует,
   сервис упал на 4 сек, откатил). Бэкап конфига:
   `/etc/telemt/telemt.toml.bak-20261117`.

## Что НЕ трогал (осознанно)

- **`/root/*.bak`, `nginx_bak_*`, `*-backup.json` на нодах и main** —
  мелкие (KB-MB), но это рабочие точки отката, на них ссылаются доки
  (`cdn-xhttp.md`, `lan-freeze-fix.md`). Не бэкап-мусор.
- **`/root/proliv-backups/YYYY-MM-DD` на DE** — 15 дневных снапшотов
  ~2M каждый (~30M), пишет nodecheck/backup-скрипт. Мелочь, retention
  не трогал.
- **Неиспользуемые tagged-образы docker**: EE 299M, FI 100M reclaimable —
  оставлены как rollback-картинка старых версий remnanode.
- **`/var/backups/*` (dpkg/apt)** — системные, килобайты.
- **KZ `/root/backup-*` + `rollback-torrent-ban.sh`** — 140K, артефакт
  torrent-инцидента, оставлен.
- **syslog/syslog.1 текущих размеров** — ротируются logrotate'ом
  (weekly), после фильтров warp/telemt новый спам не пишется.

## Рекомендации (не делал — нужно решение)

1. ~~**NL: снести snap LXD**~~ **ВЫПОЛНЕНО 17.11** — `snap remove lxd` + чистка `/var/lib/snapd/cache` (189M). Освобождено ~1.4G, диск NL 50%→46%. Остались core20+snapd (~976M) — это сама snap-система, сносить snapd целиком не стал.
   (`/var/lib/snapd` 436M + `/snap` 1.3G). Демон active, но контейнеров
   нет (`lxc list` пуст) — не используется. Диск NL 9.8G, 48% занято.
   Единственное, что держит — если вдруг понадобится LXD.
2. **Retention для `/root/proliv-backups` на DE** — сейчас 15 дней,
   ~2M/день. Если место на DE станет тесно — резать до 7.
3. **Journal SystemMaxUse=250M** уже выставлен на хостах (AGENTS.md) —
   после rotate+vacuum активный файл дорастёт до лимита и будет
   ротироваться сам, ручная чистка не нужна.
4. **xhttp_hdr.log** — если инцидент с 431 закрыт навсегда, лог можно
   вообще выключить из nginx-конфига (экономия ~30M/день записи).

## Бэкапы (что реально есть)

- **Nightly 03:30** `proliv-backup.timer` -> `/opt/proliv/infra/backup.sh`:
  pg_dump panel+shop -> `/opt/proliv/backups/YYYY-MM-DD/` (retention 14
  дней) + rsync offsite на DE-ноду `/root/proliv-backups/`.
- **Daily 00:00** `infra/backup-tg.sh` (cron root): ОДИН архив `backup-<date>.tar.gz`
  (panel.dump + shop.dump + configs/ с env+compose) -> sendDocument в TG
  админу, caption `#backup дд.мм.гггг` (BOT_TOKEN + BOOTSTRAP_OWNER_TELEGRAM_ID
  из shop/.env). Лог `/var/log/backup-tg.log`.
- **Точечные** `/root/*.bak`, `nginx_bak_*` на нодах — ручные откаты,
  не часть системы.
## Команды для повторной чистки

```bash
# на любом хосте:
apt-get clean
journalctl --rotate && journalctl --vacuum-size=80M
docker builder prune -af && docker image prune -f
df -h /

# принудительная ротация конкретного лога:
logrotate -f /etc/logrotate.d/<name>
```

Алиасы ssh: `proliv-main`, `proliv-node-de|ee|ee2|fi|uk|nl|kz|rf`.
(`proliv-node-qwins` = EE2, 163.245.52.213; контейнеры `remnanode` +
`remnanode-lte`). LTE-ноды = `docker exec`/`ssh` на тот же хост +
контейнер `remnanode-lte`.

## Ловушки, найденные в этой чистке

- `journalctl --vacuum-size` БЕЗ `--rotate` ничего не освобождает,
  если journald не архивировал текущий файл.
- rsyslog-фильтр `:programname ... stop` работает только если файл в
  `rsyslog.d/` с именем < 50 (иначе 50-default.conf уже записал).
  После правки обязателен `systemctl restart rsyslog`.
- telemt log_level: ТОЛЬКО `debug|verbose|normal|silent`. `info` роняет
  сервис (Config error → crash-loop).
- `docker image prune` без `-a` удаляет только dangling — tagged
  неиспользуемые образы остаются (это фича, не баг).
- FI — единственная нода с telemt (MTProto proxy) и VK-CDN
  xhttp-логом; у остальных профиль мусора другой.
