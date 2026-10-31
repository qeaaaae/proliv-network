<script setup lang="ts">
import { adminErrorMessage, tariffName } from './format'
import type {
  AdminMergeContext,
  AdminTariffOption,
  AdminUser,
  AdminUserDetail,
} from './types'

const props = defineProps<{
  userId: number
  detail: AdminUserDetail
  tariffOptions: AdminTariffOption[]
}>()
const emit = defineEmits<{
  updated: []
  notice: [text: string, isError: boolean]
}>()

const { call } = useAdminApi()
const router = useRouter()

const user = computed(() => props.detail.user)
const activeSub = computed(() => props.detail.active_subscription)
const balance = computed(() => props.detail.balance)

type ModalKind =
  | 'ban'
  | 'extend'
  | 'tariff'
  | 'grant'
  | 'premium'
  | 'regular'
  | 'hwid'
  | 'strategy'
  | 'resetTrial'
  | 'reissue'
  | 'message'
  | 'profileLink'
  | 'balance'
  | 'convert'
  | 'prefs'
  | 'merge'
  | 'delete'
  | ''

const modal = ref<ModalKind>('')
const busy = ref(false)
const modalError = ref('')

function open(kind: ModalKind) {
  modal.value = kind
  modalError.value = ''
  if (kind === 'extend') {
    extendMode.value = 'days'
    extendDays.value = '30'
    extendDate.value = ''
    extendTariff.value = ''
    extendHwid.value = true
    extendApplyTariffHwid.value = false
  }
  if (kind === 'tariff') {
    tariffKey.value = activeSub.value?.tariff_key || ''
    tariffApplyHwid.value = false
  }
  if (kind === 'grant') {
    grantKind.value = 'regular'
    grantGb.value = ''
  }
  if (kind === 'premium') {
    premiumUnlimited.value = Boolean(activeSub.value?.premium_unlimited_override)
    premiumBonusGb.value = activeSub.value?.premium_bonus_bytes
      ? String(Math.round((activeSub.value.premium_bonus_bytes / 1024 ** 3) * 100) / 100)
      : '0'
  }
  if (kind === 'regular') {
    regularUnlimited.value = Boolean(activeSub.value?.regular_unlimited_override)
    regularBonusGb.value = activeSub.value?.regular_bonus_bytes
      ? String(Math.round((activeSub.value.regular_bonus_bytes / 1024 ** 3) * 100) / 100)
      : '0'
  }
  if (kind === 'hwid') {
    const limit = activeSub.value?.hwid_device_limit
    hwidMode.value = limit === 0 ? 'unlimited' : limit === null || limit === undefined ? 'default' : 'custom'
    hwidLimit.value = limit ? String(limit) : ''
  }
  if (kind === 'strategy') {
    strategy.value = activeSub.value?.traffic_limit_strategy || 'MONTH'
  }
  if (kind === 'message') {
    messageText.value = ''
    messageSent.value = ''
  }
  if (kind === 'balance') {
    balanceTarget.value = 'user'
    balanceMode.value = 'add'
    balanceAmount.value = ''
    balanceReason.value = ''
  }
  if (kind === 'convert') {
    convertDirection.value = 'partner_to_user'
    convertAmount.value = ''
    convertReason.value = ''
  }
  if (kind === 'prefs') {
    const p = props.detail.notification_preferences
    prefsMarketingEmail.value = p.marketing_email
    prefsMarketingTelegram.value = p.marketing_telegram
    prefsSystemEmail.value = p.system_email
    prefsSystemTelegram.value = p.system_telegram
  }
  if (kind === 'merge') {
    mergeSourceId.value = ''
    mergeSourceUser.value = null
    mergeTargetCtx.value = null
    mergeSourceCtx.value = null
    mergeChecked.value = false
  }
  if (kind === 'delete') {
    deleteConfirm.value = ''
  }
}

function close() {
  if (busy.value) return
  modal.value = ''
}

function ok(text: string) {
  emit('notice', text, false)
  modal.value = ''
  emit('updated')
}

function fail(e: unknown) {
  modalError.value = adminErrorMessage(e)
}

// --- поля модалок ---
const extendDays = ref('30')
const extendDate = ref('')
const extendTariff = ref('')
const extendHwid = ref(true)
const extendApplyTariffHwid = ref(false)
const extendMode = ref<'days' | 'date'>('days')

const tariffKey = ref('')
const tariffApplyHwid = ref(false)

const grantKind = ref<'regular' | 'premium'>('regular')
const grantGb = ref('')

const premiumUnlimited = ref(false)
const premiumBonusGb = ref('0')

const regularUnlimited = ref(false)
const regularBonusGb = ref('0')

const hwidMode = ref<'default' | 'unlimited' | 'custom'>('default')
const hwidLimit = ref('')

const strategy = ref('MONTH')

const messageText = ref('')
const messageSent = ref('')

const balanceTarget = ref<'user' | 'partner'>('user')
const balanceMode = ref<'add' | 'subtract' | 'set'>('add')
const balanceAmount = ref('')
const balanceReason = ref('')

const convertDirection = ref<'partner_to_user' | 'user_to_partner'>('partner_to_user')
const convertAmount = ref('')
const convertReason = ref('')

const prefsMarketingEmail = ref(false)
const prefsMarketingTelegram = ref(false)
const prefsSystemEmail = ref(false)
const prefsSystemTelegram = ref(false)

const mergeSourceId = ref('')
const mergeSourceUser = ref<AdminUser | null>(null)
const mergeTargetCtx = ref<AdminMergeContext | null>(null)
const mergeSourceCtx = ref<AdminMergeContext | null>(null)
const mergeChecked = ref(false)

const deleteConfirm = ref('')

const periodTariffItems = computed(() => [
  { value: '', label: 'Не менять' },
  ...props.tariffOptions
    .filter((t) => t.is_enabled !== false && t.is_configured)
    .map((t) => ({ value: t.tariff_key, label: tariffName(t) })),
])

const tariffItems = computed(() =>
  props.tariffOptions
    .filter((t) => t.is_enabled !== false && t.is_configured)
    .map((t) => ({ value: t.tariff_key, label: tariffName(t) })),
)

const partnerSource = computed(() => balance.value?.sources?.find((s) => s.id === 'partner'))
const canConvert = computed(
  () =>
    Boolean(partnerSource.value?.convertible) ||
    Boolean(balance.value?.enabled && partnerSource.value && partnerSource.value.amount_minor > 0),
)

// --- действия ---
async function run(fn: () => Promise<void>) {
  busy.value = true
  modalError.value = ''
  try {
    await fn()
  } catch (e) {
    fail(e)
  } finally {
    busy.value = false
  }
}

async function doBan() {
  await run(async () => {
    const banned = !user.value.is_banned
    await call(`users/${props.userId}/ban`, { method: 'POST', body: { banned } })
    ok(banned ? 'Пользователь заблокирован' : 'Пользователь разблокирован')
  })
}

async function doExtend() {
  await run(async () => {
    const body: Record<string, unknown> = {
      extend_hwid_devices: extendHwid.value,
      apply_tariff_hwid_limit: extendApplyTariffHwid.value,
    }
    if (extendMode.value === 'date') {
      if (!extendDate.value) {
        modalError.value = 'Выберите дату окончания'
        return
      }
      body.end_date = extendDate.value
    } else {
      const days = Number(extendDays.value)
      if (!Number.isFinite(days) || days === 0) {
        modalError.value = 'Введите ненулевое число дней'
        return
      }
      body.days = Math.trunc(days)
    }
    if (extendTariff.value) body.tariff_key = extendTariff.value
    await call(`users/${props.userId}/extend`, { method: 'POST', body })
    ok('Подписка обновлена')
  })
}

async function doTariff() {
  await run(async () => {
    if (!tariffKey.value) {
      modalError.value = 'Выберите тариф'
      return
    }
    await call(`users/${props.userId}/tariff`, {
      method: 'POST',
      body: { tariff_key: tariffKey.value, apply_tariff_hwid_limit: tariffApplyHwid.value },
    })
    ok('Тариф изменён')
  })
}

async function doGrant() {
  await run(async () => {
    const gb = Number(String(grantGb.value).replace(',', '.'))
    if (!Number.isFinite(gb) || gb <= 0) {
      modalError.value = 'Введите объём больше нуля'
      return
    }
    const res = await call<{ grant?: { granted_gb?: number } }>(`users/${props.userId}/traffic-grant`, {
      method: 'POST',
      body: { kind: grantKind.value, gb },
    })
    ok(`Начислено ${res.grant?.granted_gb ?? gb} ГБ`)
  })
}

async function doPremium() {
  await run(async () => {
    const gb = Number(String(premiumBonusGb.value).replace(',', '.'))
    if (!Number.isFinite(gb) || gb < 0) {
      modalError.value = 'Некорректный бонус'
      return
    }
    await call(`users/${props.userId}/premium-override`, {
      method: 'POST',
      body: { unlimited: premiumUnlimited.value, bonus_gb: gb },
    })
    ok('Премиум-лимит обновлён')
  })
}

async function doRegular() {
  await run(async () => {
    const gb = Number(String(regularBonusGb.value).replace(',', '.'))
    if (!Number.isFinite(gb) || gb < 0) {
      modalError.value = 'Некорректный бонус'
      return
    }
    await call(`users/${props.userId}/regular-traffic-override`, {
      method: 'POST',
      body: { unlimited: regularUnlimited.value, regular_bonus_gb: gb },
    })
    ok('Лимит основного трафика обновлён')
  })
}

async function doHwid() {
  await run(async () => {
    const body: Record<string, unknown> = {}
    if (hwidMode.value === 'unlimited') body.unlimited = true
    else if (hwidMode.value === 'default') body.use_default = true
    else {
      const limit = Number(hwidLimit.value)
      if (!Number.isInteger(limit) || limit < 1) {
        modalError.value = 'Введите целое число от 1'
        return
      }
      body.hwid_device_limit = limit
    }
    await call(`users/${props.userId}/hwid-device-limit`, { method: 'POST', body })
    ok('Лимит устройств обновлён')
  })
}

async function doStrategy() {
  await run(async () => {
    await call(`users/${props.userId}/traffic-strategy`, {
      method: 'POST',
      body: { traffic_limit_strategy: strategy.value },
    })
    ok('Стратегия сброса обновлена')
  })
}

async function doResetTrial() {
  await run(async () => {
    await call(`users/${props.userId}/reset-trial`, { method: 'POST', body: {} })
    ok('Триал сброшен')
  })
}

async function doReissue() {
  await run(async () => {
    const res = await call<{ email_sent?: boolean }>(`users/${props.userId}/subscription-reissue`, {
      method: 'POST',
      body: {},
    })
    ok(res.email_sent ? 'Ссылка перевыпущена, письмо отправлено' : 'Ссылка перевыпущена')
  })
}

async function doMessage(preview: boolean) {
  await run(async () => {
    const text = messageText.value.trim()
    if (!text) {
      modalError.value = 'Введите текст сообщения'
      return
    }
    await call(`users/${props.userId}/message${preview ? '/preview' : ''}`, {
      method: 'POST',
      body: { text },
    })
    if (preview) {
      messageSent.value = 'Предпросмотр отправлен вам в Telegram'
      modalError.value = ''
    } else {
      ok('Сообщение отправлено')
    }
  })
}

async function doProfileLink() {
  await run(async () => {
    await call(`users/${props.userId}/telegram-profile-link`, { method: 'POST', body: {} })
    ok('Ссылка на профиль отправлена вам в Telegram')
  })
}

async function doBalance() {
  await run(async () => {
    const amount = Number(String(balanceAmount.value).replace(',', '.'))
    if (!Number.isFinite(amount) || amount < 0) {
      modalError.value = 'Введите сумму не меньше нуля'
      return
    }
    await call(`users/${props.userId}/balance-adjustment`, {
      method: 'POST',
      body: {
        target: balanceTarget.value,
        mode: balanceMode.value,
        amount,
        reason: balanceReason.value.trim(),
      },
    })
    ok('Баланс обновлён')
  })
}

async function doConvert() {
  await run(async () => {
    const amount = Number(String(convertAmount.value).replace(',', '.'))
    if (!Number.isFinite(amount) || amount <= 0) {
      modalError.value = 'Введите сумму больше нуля'
      return
    }
    await call(`users/${props.userId}/balance-conversion`, {
      method: 'POST',
      body: {
        direction: convertDirection.value,
        amount,
        reason: convertReason.value.trim(),
      },
    })
    ok('Конвертация выполнена')
  })
}

async function doPrefs() {
  await run(async () => {
    await call(`users/${props.userId}/notification-preferences`, {
      method: 'PATCH',
      body: {
        marketing_email: prefsMarketingEmail.value,
        marketing_telegram: prefsMarketingTelegram.value,
        system_email: prefsSystemEmail.value,
        system_telegram: prefsSystemTelegram.value,
      },
    })
    ok('Настройки уведомлений сохранены')
  })
}

async function checkMerge() {
  const sourceId = Number(mergeSourceId.value)
  if (!Number.isInteger(sourceId) || sourceId <= 0) {
    modalError.value = 'Введите user_id второго аккаунта'
    return
  }
  if (sourceId === props.userId) {
    modalError.value = 'Укажите другой аккаунт'
    return
  }
  busy.value = true
  modalError.value = ''
  mergeChecked.value = false
  try {
    const [srcDetail, targetCtx, sourceCtx] = await Promise.all([
      call<{ user: AdminUser }>(`users/${sourceId}`),
      call<AdminMergeContext>(`users/${props.userId}/merge-context`),
      call<AdminMergeContext>(`users/${sourceId}/merge-context`),
    ])
    mergeSourceUser.value = srcDetail.user
    mergeTargetCtx.value = targetCtx
    mergeSourceCtx.value = sourceCtx
    mergeChecked.value = true
    if (!targetCtx.merge_eligibility.allowed) {
      modalError.value = adminErrorMessage({ code: targetCtx.merge_eligibility.reason || '' })
    } else if (!sourceCtx.merge_eligibility.allowed) {
      modalError.value = adminErrorMessage({ code: sourceCtx.merge_eligibility.reason || '' })
    }
  } catch (e) {
    modalError.value = adminErrorMessage(e)
  } finally {
    busy.value = false
  }
}

const mergeAllowed = computed(
  () =>
    mergeChecked.value &&
    mergeTargetCtx.value?.merge_eligibility.allowed &&
    mergeSourceCtx.value?.merge_eligibility.allowed,
)

async function doMerge() {
  await run(async () => {
    const sourceId = Number(mergeSourceId.value)
    const res = await call<{ panel_reconciliation_pending?: boolean }>(`users/${props.userId}/merge`, {
      method: 'POST',
      body: { source_user_id: sourceId, confirmation_user_id: props.userId },
    })
    ok(
      res.panel_reconciliation_pending
        ? 'Аккаунты объединены, синхронизация панели в очереди'
        : 'Аккаунты объединены',
    )
  })
}

async function doDelete() {
  await run(async () => {
    await call(`users/${props.userId}`, { method: 'DELETE' })
    emit('notice', 'Пользователь удалён', false)
    modal.value = ''
    router.push('/admin/users')
  })
}
</script>

<template>
  <section class="admin-card">
    <h2>Действия</h2>
    <div class="adm-users-actions">
      <button class="admin-btn" @click="open('extend')">Продлить подписку</button>
      <button class="admin-btn ghost" :disabled="!activeSub" @click="open('tariff')">Сменить тариф</button>
      <button class="admin-btn ghost" :disabled="!activeSub" @click="open('grant')">Выдать трафик</button>
      <button class="admin-btn ghost" :disabled="!activeSub" @click="open('premium')">Премиум-лимит</button>
      <button class="admin-btn ghost" :disabled="!activeSub" @click="open('regular')">Основной лимит</button>
      <button class="admin-btn ghost" :disabled="!activeSub" @click="open('hwid')">Лимит устройств</button>
      <button
        v-if="activeSub?.traffic_strategy_editable"
        class="admin-btn ghost"
        @click="open('strategy')"
      >
        Сброс трафика
      </button>
      <button class="admin-btn ghost" @click="open('resetTrial')">Сбросить триал</button>
      <button class="admin-btn ghost" @click="open('reissue')">Перевыпустить ссылку</button>
      <button class="admin-btn ghost" :disabled="!user.telegram_id" @click="open('message')">Написать</button>
      <button class="admin-btn ghost" :disabled="!user.telegram_id" @click="open('profileLink')">
        Ссылка на профиль
      </button>
      <button v-if="balance?.enabled" class="admin-btn ghost" @click="open('balance')">Баланс</button>
      <button v-if="canConvert" class="admin-btn ghost" @click="open('convert')">Конвертация</button>
      <button class="admin-btn ghost" @click="open('prefs')">Уведомления</button>
      <button class="admin-btn ghost" @click="open('merge')">Объединить аккаунты</button>
      <button
        class="admin-btn"
        :class="{ danger: !user.is_banned }"
        @click="open('ban')"
      >
        {{ user.is_banned ? 'Разблокировать' : 'Заблокировать' }}
      </button>
      <button class="admin-btn danger" @click="open('delete')">Удалить</button>
    </div>

    <!-- Бан -->
    <AdminModal :open="modal === 'ban'" :title="user.is_banned ? 'Разблокировать пользователя' : 'Заблокировать пользователя'" @close="close">
      <p class="admin-note">
        {{ user.is_banned
          ? 'Пользователь снова сможет пользоваться ботом и подпиской.'
          : 'Пользователь потеряет доступ к боту, его подписка будет отключена в панели.' }}
      </p>
      <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :class="{ danger: !user.is_banned }" :disabled="busy" @click="doBan">
          {{ user.is_banned ? 'Разблокировать' : 'Заблокировать' }}
        </button>
      </template>
    </AdminModal>

    <!-- Продление -->
    <AdminModal :open="modal === 'extend'" title="Изменить срок подписки" @close="close">
      <div class="adm-users-form">
        <AdminSelect
          v-model="extendMode"
          :items="[
            { value: 'days', label: 'На количество дней' },
            { value: 'date', label: 'До конкретной даты' },
          ]"
        />
        <label v-if="extendMode === 'days'" class="adm-users-field-edit">
          <span>Дней (можно отрицательное)</span>
          <input v-model="extendDays" class="admin-input" type="number" step="1" />
        </label>
        <label v-else class="adm-users-field-edit">
          <span>Новая дата окончания</span>
          <input v-model="extendDate" class="admin-input" type="date" />
        </label>
        <label class="adm-users-field-edit">
          <span>Тариф для продления</span>
          <AdminSelect v-model="extendTariff" :items="periodTariffItems" />
        </label>
        <label class="admin-check">
          <input v-model="extendHwid" type="checkbox" /> Продлить докупленные устройства
        </label>
        <label class="admin-check">
          <input v-model="extendApplyTariffHwid" type="checkbox" /> Применить лимит устройств тарифа
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doExtend">Применить</button>
      </template>
    </AdminModal>

    <!-- Тариф -->
    <AdminModal :open="modal === 'tariff'" title="Сменить тариф" @close="close">
      <div class="adm-users-form">
        <label class="adm-users-field-edit">
          <span>Тариф</span>
          <AdminSelect v-model="tariffKey" :items="tariffItems" placeholder="Выберите тариф" />
        </label>
        <label class="admin-check">
          <input v-model="tariffApplyHwid" type="checkbox" /> Применить лимит устройств тарифа
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doTariff">Сменить</button>
      </template>
    </AdminModal>

    <!-- Выдача трафика -->
    <AdminModal :open="modal === 'grant'" title="Выдать трафик" @close="close">
      <div class="adm-users-form">
        <label class="adm-users-field-edit">
          <span>Тип</span>
          <AdminSelect
            v-model="grantKind"
            :items="[
              { value: 'regular', label: 'Основной' },
              { value: 'premium', label: 'Премиум' },
            ]"
          />
        </label>
        <label class="adm-users-field-edit">
          <span>Объём, ГБ</span>
          <input v-model="grantGb" class="admin-input" type="number" min="0" step="0.1" />
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doGrant">Начислить</button>
      </template>
    </AdminModal>

    <!-- Премиум-лимит -->
    <AdminModal :open="modal === 'premium'" title="Премиум-трафик" @close="close">
      <div class="adm-users-form">
        <label class="admin-check">
          <input v-model="premiumUnlimited" type="checkbox" /> Безлимитный премиум
        </label>
        <label class="adm-users-field-edit">
          <span>Бонусный премиум, ГБ</span>
          <input v-model="premiumBonusGb" class="admin-input" type="number" min="0" step="0.1" :disabled="premiumUnlimited" />
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doPremium">Сохранить</button>
      </template>
    </AdminModal>

    <!-- Основной лимит -->
    <AdminModal :open="modal === 'regular'" title="Основной трафик" @close="close">
      <div class="adm-users-form">
        <label class="admin-check">
          <input v-model="regularUnlimited" type="checkbox" /> Безлимитный трафик
        </label>
        <label class="adm-users-field-edit">
          <span>Бонусный трафик, ГБ</span>
          <input v-model="regularBonusGb" class="admin-input" type="number" min="0" step="0.1" :disabled="regularUnlimited" />
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doRegular">Сохранить</button>
      </template>
    </AdminModal>

    <!-- HWID-лимит -->
    <AdminModal :open="modal === 'hwid'" title="Лимит устройств" @close="close">
      <div class="adm-users-form">
        <AdminSelect
          v-model="hwidMode"
          :items="[
            { value: 'default', label: 'По умолчанию (тариф/.env)' },
            { value: 'unlimited', label: 'Безлимит' },
            { value: 'custom', label: 'Свой лимит' },
          ]"
        />
        <label v-if="hwidMode === 'custom'" class="adm-users-field-edit">
          <span>Устройств</span>
          <input v-model="hwidLimit" class="admin-input" type="number" min="1" step="1" />
        </label>
        <p class="admin-note">Докупленные устройства прибавляются к лимиту отдельно.</p>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doHwid">Сохранить</button>
      </template>
    </AdminModal>

    <!-- Стратегия сброса -->
    <AdminModal :open="modal === 'strategy'" title="Стратегия сброса трафика" @close="close">
      <div class="adm-users-form">
        <AdminSelect
          v-model="strategy"
          :items="[
            { value: 'NO_RESET', label: 'Без сброса' },
            { value: 'DAY', label: 'Раз в день' },
            { value: 'WEEK', label: 'Раз в неделю' },
            { value: 'MONTH', label: 'Раз в месяц' },
            { value: 'MONTH_ROLLING', label: 'Скользящий месяц' },
          ]"
        />
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doStrategy">Сохранить</button>
      </template>
    </AdminModal>

    <!-- Сброс триала -->
    <AdminModal :open="modal === 'resetTrial'" title="Сбросить триал" @close="close">
      <p class="admin-note">
        Пользователь сможет заново активировать пробный период. Активная триал-подписка будет завершена.
      </p>
      <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doResetTrial">Сбросить</button>
      </template>
    </AdminModal>

    <!-- Перевыпуск ссылки -->
    <AdminModal :open="modal === 'reissue'" title="Перевыпустить ссылку подписки" @close="close">
      <p class="admin-note">
        Старая ссылка подписки перестанет работать. Если у пользователя привязан email - новая ссылка будет отправлена письмом.
      </p>
      <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doReissue">Перевыпустить</button>
      </template>
    </AdminModal>

    <!-- Сообщение -->
    <AdminModal :open="modal === 'message'" title="Сообщение пользователю" @close="close">
      <div class="adm-users-form">
        <label class="adm-users-field-edit">
          <span>Текст (HTML-разметка Telegram)</span>
          <textarea v-model="messageText" class="admin-input" rows="5" />
        </label>
        <p v-if="messageSent" class="admin-note">{{ messageSent }}</p>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="doMessage(true)">Предпросмотр себе</button>
        <button class="admin-btn" :disabled="busy" @click="doMessage(false)">Отправить</button>
      </template>
    </AdminModal>

    <!-- Ссылка на профиль -->
    <AdminModal :open="modal === 'profileLink'" title="Ссылка на профиль Telegram" @close="close">
      <p class="admin-note">Бот отправит вам в Telegram сообщение с кнопкой для открытия профиля этого пользователя.</p>
      <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doProfileLink">Получить ссылку</button>
      </template>
    </AdminModal>

    <!-- Баланс -->
    <AdminModal :open="modal === 'balance'" title="Корректировка баланса" @close="close">
      <div class="adm-users-form">
        <label class="adm-users-field-edit">
          <span>Баланс</span>
          <AdminSelect
            v-model="balanceTarget"
            :items="[
              { value: 'user', label: 'Основной' },
              { value: 'partner', label: 'Партнёрский' },
            ]"
          />
        </label>
        <label class="adm-users-field-edit">
          <span>Операция</span>
          <AdminSelect
            v-model="balanceMode"
            :items="[
              { value: 'add', label: 'Начислить' },
              { value: 'subtract', label: 'Списать' },
              { value: 'set', label: 'Установить' },
            ]"
          />
        </label>
        <label class="adm-users-field-edit">
          <span>Сумма, {{ balance?.currency || 'RUB' }}</span>
          <input v-model="balanceAmount" class="admin-input" type="number" min="0" step="0.01" />
        </label>
        <label class="adm-users-field-edit">
          <span>Комментарий</span>
          <input v-model="balanceReason" class="admin-input" maxlength="500" placeholder="Причина корректировки" />
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doBalance">Применить</button>
      </template>
    </AdminModal>

    <!-- Конвертация -->
    <AdminModal :open="modal === 'convert'" title="Конвертация баланса" @close="close">
      <div class="adm-users-form">
        <label class="adm-users-field-edit">
          <span>Направление</span>
          <AdminSelect
            v-model="convertDirection"
            :items="[
              { value: 'partner_to_user', label: 'Партнёрский -> основной' },
              { value: 'user_to_partner', label: 'Основной -> партнёрский' },
            ]"
          />
        </label>
        <label class="adm-users-field-edit">
          <span>Сумма, {{ balance?.currency || 'RUB' }}</span>
          <input v-model="convertAmount" class="admin-input" type="number" min="0" step="0.01" />
        </label>
        <label class="adm-users-field-edit">
          <span>Комментарий</span>
          <input v-model="convertReason" class="admin-input" maxlength="500" />
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doConvert">Перевести</button>
      </template>
    </AdminModal>

    <!-- Уведомления -->
    <AdminModal :open="modal === 'prefs'" title="Настройки уведомлений" @close="close">
      <div class="adm-users-form">
        <label class="admin-check"><input v-model="prefsSystemTelegram" type="checkbox" /> Системные в Telegram</label>
        <label class="admin-check"><input v-model="prefsMarketingTelegram" type="checkbox" /> Маркетинг в Telegram</label>
        <label class="admin-check"><input v-model="prefsSystemEmail" type="checkbox" /> Системные на email</label>
        <label class="admin-check"><input v-model="prefsMarketingEmail" type="checkbox" /> Маркетинг на email</label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="doPrefs">Сохранить</button>
      </template>
    </AdminModal>

    <!-- Объединение -->
    <AdminModal :open="modal === 'merge'" title="Объединить аккаунты" @close="close">
      <div class="adm-users-form">
        <p class="admin-note">
          Аккаунт-источник будет влит в текущий ({{ user.minishop_id || `#${user.user_id}` }}): Telegram, подписки и платежи перейдут сюда, источник будет удалён.
        </p>
        <label class="adm-users-field-edit">
          <span>user_id аккаунта-источника</span>
          <input v-model="mergeSourceId" class="admin-input" type="number" min="1" step="1" />
        </label>
        <div class="admin-row">
          <button class="admin-btn ghost" :disabled="busy" @click="checkMerge">Проверить</button>
        </div>
        <template v-if="mergeChecked && mergeSourceUser">
          <div class="adm-users-merge-preview">
            <strong>Источник:</strong> {{ mergeSourceUser.first_name || mergeSourceUser.username || mergeSourceUser.minishop_id || `#${mergeSourceUser.user_id}` }}
            ({{ mergeSourceUser.minishop_id || `#${mergeSourceUser.user_id}` }})
            <p v-if="mergeSourceCtx" class="admin-note">
              Email: {{ mergeSourceCtx.verified_emails.join(', ') || 'нет' }} · passkey: {{ mergeSourceCtx.passkey_count }}
            </p>
          </div>
        </template>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button class="admin-btn danger" :disabled="busy || !mergeAllowed" @click="doMerge">Объединить</button>
      </template>
    </AdminModal>

    <!-- Удаление -->
    <AdminModal :open="modal === 'delete'" title="Удалить пользователя" @close="close">
      <div class="adm-users-form">
        <p class="admin-note admin-error">
          Необратимо: пользователь и все его данные (подписки, платежи, баланс, аккаунт в панели) будут удалены.
        </p>
        <label class="adm-users-field-edit">
          <span>Для подтверждения введите user_id: {{ user.user_id }}</span>
          <input v-model="deleteConfirm" class="admin-input" type="number" />
        </label>
        <p v-if="modalError" class="admin-note admin-error">{{ modalError }}</p>
      </div>
      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="close">Отмена</button>
        <button
          class="admin-btn danger"
          :disabled="busy || String(deleteConfirm).trim() !== String(user.user_id)"
          @click="doDelete"
        >
          Удалить навсегда
        </button>
      </template>
    </AdminModal>
  </section>
</template>

<style scoped>
.adm-users-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.adm-users-form {
  display: grid;
  gap: 12px;
}
.adm-users-field-edit {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
.adm-users-merge-preview {
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--adm-border, #232c3d);
  font-size: 13px;
}
</style>
