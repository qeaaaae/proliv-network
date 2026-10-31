<script setup lang="ts">
interface HealthAlert {
  id: string | number
  severity: string
  message_key: string
  params: Record<string, unknown>
  sections: string[]
}
interface PanelCompatibility {
  version: string | null
  generation: string
  support_status: string
  certified_versions: string[]
  capabilities: string[]
  observed_capabilities: Record<string, boolean>
}
interface HealthData {
  alerts: HealthAlert[]
  checked_at: string | null
  panel_compatibility: PanelCompatibility | null
}

const props = defineProps<{
  health: HealthData | null
  stats: Record<string, unknown> | null
  loading: boolean
  error: string
}>()
const emit = defineEmits<{ refresh: [] }>()

// Русские тексты для частых alert-ключей бэкенда (message_key + {params}).
const ALERT_MESSAGES: Record<string, string> = {
  data_dir_missing: 'Каталог данных ({path}) не найден. Проверьте монтирование volume в контейнер.',
  data_dir_not_writable: 'Нет прав записи в {path} - бэкапы, тарифы и переводы не сохранятся.',
  data_mount_mismatch:
    'Сервисы используют разные монтирования /app/data ({mounts}). Настройте общий источник данных и пересоздайте контейнеры.',
  backups_dir_not_writable: 'Каталог бэкапов {path} недоступен для записи.',
  tariffs_config_invalid: 'Файл тарифов {path} не читается: {error}',
  locale_overrides_invalid: 'Файл переводов {path} повреждён: {error}',
  subscription_page_config_invalid: 'Конфиг страницы подписки не читается: {error}',
  provider_not_configured:
    'Провайдер {provider} включён, но не настроен - платежи через него не пройдут.',
  provider_webhook_needs_base_url:
    'Провайдеру {provider} нужен WEBHOOK_BASE_URL для вебхуков, но он не задан.',
  no_payment_methods: 'Не включён ни один способ оплаты.',
  mini_app_url_missing: 'SUBSCRIPTION_MINI_APP_URL не задан - кнопка Mini App не появится в боте.',
  mini_app_url_not_https: 'SUBSCRIPTION_MINI_APP_URL должен начинаться с https:// (сейчас {url}).',
  redis_not_configured: 'REDIS_URL не задан - состояния диалогов и кэши бота не переживут рестарт.',
  smtp_incomplete: 'SMTP настроен частично - вход по email не будет работать.',
  proxy_not_trusted:
    'Запросы приходят через прокси {remote}, которого нет в TRUSTED_PROXIES - вебхуки провайдеров могут отклоняться по IP.',
  bot_token_invalid: 'Telegram отклонил BOT_TOKEN - бот не работает.',
  telegram_api_error: 'Не удалось связаться с Telegram API: {error}',
  telegram_webhook_missing: 'Вебхук Telegram не задан - бот не получает обновления.',
  telegram_webhook_mismatch: 'Вебхук Telegram указывает на {actual}, ожидается {expected}.',
  telegram_webhook_error: 'Telegram сообщает об ошибке доставки вебхука: {error}',
  telegram_webhook_pending: 'В очереди Telegram {count} необработанных обновлений.',
  panel_api_not_configured:
    'PANEL_API_URL и PANEL_API_KEY не заданы - синхронизация и выдача подписок не работают.',
  panel_api_unreachable: 'Панель Remnawave недоступна по адресу {url}.',
  panel_api_version_unknown: 'Версия API панели не определена.',
  panel_api_version_unverified: 'Версия панели не проверена на совместимость.',
  panel_api_version_historical: 'Версия панели устарела - часть функций может быть недоступна.',
  panel_api_version_unsupported: 'Версия панели не поддерживается.',
  premium_squad_enforcement_leak: 'Есть пользователи с Premium-доступом вне разрешённых сквадов.',
  panel_limit_drift: 'Лимиты в панели расходятся с настройками minishop.',
}

const GENERATION_LABELS: Record<string, string> = {
  'rw3-numeric-user-id': 'Remnawave 3.x',
  'rw2-uuid-user-id': 'Remnawave 2.x',
  unknown: 'не определено',
}
const SUPPORT_LABELS: Record<string, string> = {
  certified: 'Сертифицирована',
  historical: 'Устаревшая',
  unsupported: 'Не поддерживается',
  unverified: 'Не проверена',
  unknown: 'Неизвестно',
}

const alerts = computed(() => props.health?.alerts || [])
const errorCount = computed(() => alerts.value.filter((a) => a.severity === 'error').length)
const warnCount = computed(() => alerts.value.filter((a) => a.severity === 'warning').length)
const compat = computed(() => props.health?.panel_compatibility || null)

const users = computed(() => (props.stats?.users || {}) as Record<string, unknown>)
const financial = computed(() => (props.stats?.financial || {}) as Record<string, unknown>)
const panelSystem = computed(() => {
  const panel = props.stats?.panel as Record<string, unknown> | null | undefined
  return (panel?.system || {}) as Record<string, unknown>
})
const onlineNow = computed(() => {
  const stats = (panelSystem.value.onlineStats || {}) as Record<string, unknown>
  const v = Number(stats.onlineNow)
  return Number.isFinite(v) ? v : null
})
const currency = computed(() => String(props.stats?.currency_symbol || 'RUB').toUpperCase())

function interpolate(tpl: string, params: Record<string, unknown>): string {
  return String(tpl || '').replace(/\{(\w+)\}/g, (match, key) =>
    params[key] !== undefined && params[key] !== null ? String(params[key]) : match,
  )
}
function alertText(alert: HealthAlert): string {
  return interpolate(ALERT_MESSAGES[alert.message_key] || alert.message_key, alert.params || {})
}
function severityTone(severity: string): 'danger' | 'warning' | 'muted' {
  if (severity === 'error') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'muted'
}
function severityLabel(severity: string): string {
  if (severity === 'error') return 'Ошибка'
  if (severity === 'warning') return 'Предупреждение'
  return 'Инфо'
}
function supportTone(status: string): 'success' | 'warning' | 'danger' | 'muted' {
  if (status === 'certified') return 'success'
  if (status === 'unsupported') return 'danger'
  if (status === 'historical' || status === 'unverified') return 'warning'
  return 'muted'
}
function num(value: unknown): number | null {
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}
function fmtNum(value: unknown): string {
  const n = num(value)
  return n === null ? '-' : n.toLocaleString('ru-RU')
}
function fmtMoney(value: unknown): string {
  const n = num(value)
  if (n === null) return '-'
  const sym = currency.value === 'RUB' ? '₽' : currency.value
  return `${n.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ${sym}`
}
function fmtDateTime(iso: string | null | undefined): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return String(iso)
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <section class="admin-card">
    <div class="admin-row card-head">
      <h2>Состояние системы</h2>
      <AdminBadge v-if="!loading && !error && !alerts.length" tone="success">Всё в порядке</AdminBadge>
      <AdminBadge v-if="errorCount" tone="danger">Ошибок: {{ errorCount }}</AdminBadge>
      <AdminBadge v-if="warnCount" tone="warning">Предупреждений: {{ warnCount }}</AdminBadge>
      <button class="admin-btn ghost" :disabled="loading" @click="emit('refresh')">
        {{ loading ? 'Обновление...' : 'Обновить' }}
      </button>
    </div>

    <p v-if="error" class="admin-note admin-error">{{ error }}</p>
    <p v-else-if="loading && !health" class="admin-note">Загрузка...</p>

    <template v-else>
      <p v-if="health?.checked_at" class="admin-note">Проверено: {{ fmtDateTime(health.checked_at) }}</p>

      <ul v-if="alerts.length" class="sys-alerts">
        <li v-for="alert in alerts" :key="String(alert.id)" class="sys-alert">
          <AdminBadge :tone="severityTone(alert.severity)">{{ severityLabel(alert.severity) }}</AdminBadge>
          <span class="sys-alert-text">{{ alertText(alert) }}</span>
        </li>
      </ul>

      <div v-if="stats" class="admin-grid cols-3 sys-kpis">
        <div class="admin-kpi">
          <small>Пользователей</small>
          <strong>{{ fmtNum(users.total_users) }}</strong>
        </div>
        <div class="admin-kpi">
          <small>Активных подписок</small>
          <strong>{{ fmtNum(users.active_subscriptions) }}</strong>
        </div>
        <div class="admin-kpi">
          <small>Онлайн сейчас</small>
          <strong>{{ onlineNow === null ? '-' : fmtNum(onlineNow) }}</strong>
        </div>
        <div class="admin-kpi">
          <small>Выручка сегодня</small>
          <strong>{{ fmtMoney(financial.today_revenue) }}</strong>
        </div>
        <div class="admin-kpi">
          <small>Выручка за 7 дней</small>
          <strong>{{ fmtMoney(financial.week_revenue) }}</strong>
        </div>
        <div class="admin-kpi">
          <small>Выручка за 30 дней</small>
          <strong>{{ fmtMoney(financial.month_revenue) }}</strong>
        </div>
      </div>

      <div v-if="compat" class="sys-version">
        <span class="admin-note">Панель:</span>
        <strong>{{ compat.version || 'версия не определена' }}</strong>
        <AdminBadge tone="muted">{{ GENERATION_LABELS[compat.generation] || compat.generation }}</AdminBadge>
        <AdminBadge :tone="supportTone(compat.support_status)">
          {{ SUPPORT_LABELS[compat.support_status] || compat.support_status }}
        </AdminBadge>
      </div>
      <p v-if="compat?.certified_versions?.length" class="admin-note">
        Сертифицированные версии: {{ compat.certified_versions.join(', ') }}
      </p>
    </template>
  </section>
</template>

<style scoped>
.card-head {
  justify-content: space-between;
}
.sys-alerts {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}
.sys-alert {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.sys-alert-text {
  font-size: 13px;
  line-height: 1.4;
}
.sys-version {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  padding-top: 4px;
  border-top: 1px solid var(--adm-border);
}
.sys-version strong {
  font-size: 13px;
}
</style>
