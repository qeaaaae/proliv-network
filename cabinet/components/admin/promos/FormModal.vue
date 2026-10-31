<script setup lang="ts">
// Создание/редактирование промокода.
// Create: POST /api/admin/promos (code=null -> сервер сам генерирует).
// Edit: PATCH /api/admin/promos/{id} (отправляем всю форму; is_active не
// трогаем здесь - отдельная кнопка вкл/выкл в списке).

interface AdminPromo {
  id: number
  code: string
  bot_link: string | null
  webapp_link: string | null
  app_link: string | null
  bonus_days: number
  regular_traffic_gb: number
  premium_traffic_gb: number
  discount_percent: number | null
  duration_multiplier: number | null
  traffic_multiplier: number | null
  bonus_requires_payment: boolean
  applies_to: string
  min_subscription_months: number | null
  min_subscription_days: number | null
  min_traffic_gb: number | null
  origin: string
  effect_summary: string
  max_activations: number
  current_activations: number
  is_active: boolean
  valid_until: string | null
  created_at: string | null
  user_id: number | null
  user_username: string | null
  user_name: string | null
}

type EffectType = 'days' | 'traffic' | 'discount' | 'duration' | 'traffic_x'

const props = defineProps<{ open: boolean; promo: AdminPromo | null }>()
const emit = defineEmits<{ close: []; saved: [promo: AdminPromo] }>()

const { call } = useAdminApi()

const isEdit = computed(() => props.promo !== null)
const title = computed(() =>
  isEdit.value ? `Промокод ${props.promo?.code || ''}` : 'Новый промокод',
)

const code = ref('')
const effectType = ref<EffectType>('days')
const bonusDays = ref('')
const regularGb = ref('')
const premiumGb = ref('')
const discountPercent = ref('')
const durationMultiplier = ref('')
const trafficMultiplier = ref('')
const bonusRequiresPayment = ref(false)
const appliesTo = ref('all')
const minSubValue = ref('')
const minSubUnit = ref<'months' | 'days'>('months')
const minTrafficGb = ref('')
const maxActivations = ref('1')
const unlimited = ref(true)
const validDays = ref('')
const origin = ref('admin')

const busy = ref(false)
const errorText = ref('')

const effectItems = [
  { value: 'days', label: 'Бонусные дни' },
  { value: 'traffic', label: 'Трафик (ГБ)' },
  { value: 'discount', label: 'Скидка %' },
  { value: 'duration', label: 'Множитель длительности' },
  { value: 'traffic_x', label: 'Множитель трафика' },
]
const scopeItems = [
  { value: 'all', label: 'Всё' },
  { value: 'subscription', label: 'Подписка' },
  { value: 'traffic', label: 'Пакеты трафика' },
  { value: 'traffic_topup', label: 'Докупка трафика' },
  { value: 'hwid', label: 'Устройства (HWID)' },
]
const minSubUnitItems = [
  { value: 'months', label: 'мес.' },
  { value: 'days', label: 'дн.' },
]

const isFixedGrant = computed(() => effectType.value === 'days' || effectType.value === 'traffic')
const hasThreshold = computed(
  () => num(minSubValue.value) !== null || num(minTrafficGb.value) !== null,
)
// Сервер: фиксированный бонус + порог действует только в режиме 'при оплате'.
const paymentModeForced = computed(() => isFixedGrant.value && hasThreshold.value)

function num(v: string): number | null {
  const t = v.trim().replace(',', '.')
  if (!t) return null
  const n = Number(t)
  return Number.isFinite(n) ? n : null
}

function intOrNull(v: string): number | null {
  const n = num(v)
  return n === null ? null : Math.trunc(n)
}

function reset() {
  const p = props.promo
  code.value = p?.code || ''
  bonusDays.value = p && p.bonus_days > 0 ? String(p.bonus_days) : ''
  regularGb.value = p && p.regular_traffic_gb > 0 ? String(p.regular_traffic_gb) : ''
  premiumGb.value = p && p.premium_traffic_gb > 0 ? String(p.premium_traffic_gb) : ''
  discountPercent.value = p?.discount_percent ? String(p.discount_percent) : ''
  durationMultiplier.value = p?.duration_multiplier ? String(p.duration_multiplier) : ''
  trafficMultiplier.value = p?.traffic_multiplier ? String(p.traffic_multiplier) : ''
  if (p?.discount_percent) effectType.value = 'discount'
  else if (p && p.duration_multiplier && p.duration_multiplier > 1) effectType.value = 'duration'
  else if (p && p.traffic_multiplier && p.traffic_multiplier > 1) effectType.value = 'traffic_x'
  else if (p && (p.regular_traffic_gb > 0 || p.premium_traffic_gb > 0)) effectType.value = 'traffic'
  else effectType.value = 'days'
  bonusRequiresPayment.value = Boolean(p?.bonus_requires_payment)
  appliesTo.value = p?.applies_to || 'all'
  if (p?.min_subscription_days) {
    minSubValue.value = String(p.min_subscription_days)
    minSubUnit.value = 'days'
  } else if (p?.min_subscription_months) {
    minSubValue.value = String(p.min_subscription_months)
    minSubUnit.value = 'months'
  } else {
    minSubValue.value = ''
    minSubUnit.value = 'months'
  }
  minTrafficGb.value = p?.min_traffic_gb ? String(p.min_traffic_gb) : ''
  maxActivations.value = String(p?.max_activations ?? 1)
  if (p?.valid_until) {
    const left = Math.ceil((new Date(p.valid_until).getTime() - Date.now()) / 86400_000)
    unlimited.value = false
    validDays.value = String(Math.max(1, left))
  } else {
    unlimited.value = true
    validDays.value = ''
  }
  origin.value = p?.origin || 'admin'
  errorText.value = ''
}

watch(
  () => props.open,
  (open) => {
    if (open) reset()
  },
)

const ERROR_TEXTS: Record<string, string> = {
  duplicate_code: 'Такой код уже существует',
  empty_effect: 'Задайте хотя бы один эффект',
  invalid_activation_code: 'Код: только латиница, цифры, _ и -',
  invalid_valid_days: 'Некорректный срок действия',
  invalid_bonus_days: 'Некорректное число бонусных дней',
  invalid_discount_percent: 'Скидка: от 0 до 100',
  invalid_duration_multiplier: 'Множитель длительности: от 1 до макс. лимита',
  invalid_traffic_multiplier: 'Множитель трафика: от 1 до макс. лимита',
  invalid_regular_traffic_gb: 'Некорректный объём трафика (ГБ)',
  invalid_premium_traffic_gb: 'Некорректный объём премиум-трафика (ГБ)',
  invalid_min_subscription_months: 'Некорректный мин. срок подписки',
  invalid_min_subscription_days: 'Некорректный мин. срок подписки (дни)',
  invalid_min_traffic_gb: 'Некорректный мин. трафик',
  invalid_applies_to: 'Недопустимая область применения',
  conflicting_subscription_thresholds: 'Пороги в месяцах и днях конфликтуют',
  subscription_threshold_scope_mismatch: 'Порог подписки не подходит для этой области',
  traffic_threshold_scope_mismatch: 'Порог трафика не подходит для этой области',
  bonus_days_scope_mismatch: 'Бонусные дни работают только для подписки',
  fixed_traffic_scope_mismatch: 'Выдача трафика работает только для подписки',
  fixed_grant_traffic_multiplier_mismatch: 'Множитель трафика нельзя с фикс. бонусом',
  fixed_grant_traffic_threshold_mismatch: 'Порог по трафику нельзя с фикс. бонусом',
  duration_multiplier_scope_mismatch: 'Множитель длительности только для подписки',
  traffic_multiplier_scope_mismatch: 'Множитель трафика - только для трафика',
  hwid_scope_requires_discount: 'Для области HWID нужна скидка %',
  bonus_payment_mode_requires_fixed_grant: 'Режим "при оплате" требует бонус днями или ГБ',
  bonus_threshold_requires_payment_mode: 'С порогом бонус выдаётся только при оплате',
  max_activations_below_current: 'Лимит меньше уже использованных активаций',
  no_changes: 'Нет изменений',
  not_found: 'Промокод не найден',
}

function mapError(raw: string): string {
  const parts = raw.split(',').map((part) => ERROR_TEXTS[part.trim()] || part.trim())
  return parts.join('; ')
}

function validate(): string | null {
  if (!isEdit.value && code.value.trim() && !/^[A-Za-z0-9_-]{1,100}$/.test(code.value.trim())) {
    return 'Код: только латиница, цифры, _ и -'
  }
  if (effectType.value === 'days' && (num(bonusDays.value) ?? 0) <= 0) {
    return 'Укажите бонусные дни (> 0)'
  }
  if (effectType.value === 'traffic' && (num(regularGb.value) ?? 0) <= 0 && (num(premiumGb.value) ?? 0) <= 0) {
    return 'Укажите объём трафика (ГБ)'
  }
  if (effectType.value === 'discount') {
    const d = num(discountPercent.value)
    if (d === null || d <= 0 || d > 100) return 'Скидка: от 0 до 100'
  }
  if (effectType.value === 'duration' && (num(durationMultiplier.value) ?? 0) <= 1) {
    return 'Множитель длительности: больше 1'
  }
  if (effectType.value === 'traffic_x' && (num(trafficMultiplier.value) ?? 0) <= 1) {
    return 'Множитель трафика: больше 1'
  }
  const max = intOrNull(maxActivations.value)
  if (max === null || max < 1) return 'Укажите лимит активаций (>= 1)'
  if (isEdit.value && props.promo && max < props.promo.current_activations) {
    return `Лимит не может быть меньше использованных (${props.promo.current_activations})`
  }
  if (!unlimited.value) {
    const days = intOrNull(validDays.value)
    if (days === null || days < 1) return 'Укажите срок действия в днях или включите "бессрочно"'
  }
  return null
}

function effectPayload() {
  // Тип - взаимоисключающий, как в боте: невыбранные эффекты обнуляем.
  return {
    bonus_days: effectType.value === 'days' ? intOrNull(bonusDays.value) || 0 : 0,
    regular_traffic_gb: effectType.value === 'traffic' ? num(regularGb.value) || 0 : 0,
    premium_traffic_gb: effectType.value === 'traffic' ? num(premiumGb.value) || 0 : 0,
    discount_percent: effectType.value === 'discount' ? num(discountPercent.value) : null,
    duration_multiplier: effectType.value === 'duration' ? num(durationMultiplier.value) : null,
    traffic_multiplier: effectType.value === 'traffic_x' ? num(trafficMultiplier.value) : null,
    bonus_requires_payment: isFixedGrant.value
      ? bonusRequiresPayment.value || paymentModeForced.value
      : false,
  }
}

async function submit() {
  const invalid = validate()
  if (invalid) {
    errorText.value = invalid
    return
  }
  busy.value = true
  errorText.value = ''
  const minSub = intOrNull(minSubValue.value)
  const minSubDays = minSub !== null && minSubUnit.value === 'days' ? minSub : null
  const minSubMonths = minSub !== null && minSubUnit.value === 'months' ? minSub : null
  try {
    if (isEdit.value && props.promo) {
      const body: Record<string, unknown> = {
        ...effectPayload(),
        applies_to: appliesTo.value,
        min_traffic_gb: num(minTrafficGb.value),
        max_activations: intOrNull(maxActivations.value),
        origin: origin.value.trim() || 'admin',
      }
      // Сервер взаимоисключает пороги: присутствие min_subscription_days в теле
      // (даже null) зануляет months, и наоборот - шлём ровно один ключ.
      if (minSub !== null && minSubUnit.value === 'days') {
        body.min_subscription_days = minSub
      } else if (minSub !== null) {
        body.min_subscription_months = minSub
      } else {
        body.min_subscription_days = null // очищает оба порога
      }
      if (unlimited.value) {
        body.clear_valid_until = true
      } else {
        const days = intOrNull(validDays.value) || 0
        body.valid_until = new Date(Date.now() + days * 86400_000).toISOString()
      }
      const res = await call<{ promo: AdminPromo }>(`promos/${props.promo.id}`, {
        method: 'PATCH',
        body,
      })
      emit('saved', res.promo)
    } else {
      const body: Record<string, unknown> = {
        ...effectPayload(),
        code: code.value.trim() || null,
        applies_to: appliesTo.value,
        min_subscription_months: minSubMonths,
        min_subscription_days: minSubDays,
        min_traffic_gb: num(minTrafficGb.value),
        max_activations: intOrNull(maxActivations.value),
        valid_days: unlimited.value ? null : intOrNull(validDays.value),
        origin: origin.value.trim() || 'admin',
      }
      const res = await call<{ promo: AdminPromo }>('promos', { method: 'POST', body })
      emit('saved', res.promo)
    }
    emit('close')
  } catch (e) {
    errorText.value = mapError((e as Error).message || 'request_failed')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AdminModal :open="open" :title="title" @close="emit('close')">
    <div class="promo-form">
      <label v-if="!isEdit" class="admin-field">
        <span>Код (пусто - сгенерируется автоматически)</span>
        <input v-model="code" class="admin-input" placeholder="SALE2026" maxlength="100" />
      </label>
      <template v-else>
        <p class="admin-note">Код изменить нельзя. Активаций уже использовано: {{ promo?.current_activations }}.</p>
      </template>

      <label class="admin-field">
        <span>Тип эффекта</span>
        <AdminSelect v-model="effectType" :items="effectItems" />
      </label>

      <label v-if="effectType === 'days'" class="admin-field">
        <span>Бонусные дни</span>
        <input v-model="bonusDays" class="admin-input" type="number" min="1" step="1" placeholder="7" />
      </label>
      <template v-if="effectType === 'traffic'">
        <label class="admin-field">
          <span>Обычный трафик, ГБ</span>
          <input v-model="regularGb" class="admin-input" type="number" min="0" step="0.001" placeholder="10" />
        </label>
        <label class="admin-field">
          <span>Премиум-трафик, ГБ</span>
          <input v-model="premiumGb" class="admin-input" type="number" min="0" step="0.001" placeholder="0" />
        </label>
      </template>
      <label v-if="effectType === 'discount'" class="admin-field">
        <span>Скидка, %</span>
        <input v-model="discountPercent" class="admin-input" type="number" min="1" max="100" step="0.01" placeholder="20" />
      </label>
      <label v-if="effectType === 'duration'" class="admin-field">
        <span>Множитель длительности (x)</span>
        <input v-model="durationMultiplier" class="admin-input" type="number" min="1" step="0.1" placeholder="2" />
      </label>
      <label v-if="effectType === 'traffic_x'" class="admin-field">
        <span>Множитель трафика (x)</span>
        <input v-model="trafficMultiplier" class="admin-input" type="number" min="1" step="0.1" placeholder="2" />
      </label>

      <label v-if="isFixedGrant" class="admin-check">
        <input v-model="bonusRequiresPayment" type="checkbox" :disabled="paymentModeForced" />
        Бонус выдаётся только при оплате
      </label>
      <p v-if="paymentModeForced" class="admin-note">
        С порогом бонус может выдаваться только при оплате - режим включён принудительно.
      </p>

      <label class="admin-field">
        <span>Область применения</span>
        <AdminSelect v-model="appliesTo" :items="scopeItems" />
      </label>

      <div class="admin-field">
        <span>Мин. срок подписки (пусто - без порога)</span>
        <div class="admin-row">
          <input v-model="minSubValue" class="admin-input" type="number" min="1" step="1" placeholder="3" />
          <AdminSelect v-model="minSubUnit" :items="minSubUnitItems" class="unit-select" />
        </div>
      </div>
      <label class="admin-field">
        <span>Мин. трафик в покупке, ГБ (пусто - без порога)</span>
        <input v-model="minTrafficGb" class="admin-input" type="number" min="0" step="0.001" placeholder="50" />
      </label>

      <label class="admin-field">
        <span>Лимит активаций</span>
        <input v-model="maxActivations" class="admin-input" type="number" min="1" step="1" />
      </label>

      <label class="admin-check">
        <input v-model="unlimited" type="checkbox" />
        Бессрочно
      </label>
      <label v-if="!unlimited" class="admin-field">
        <span>Срок действия, дней (от текущего момента)</span>
        <input v-model="validDays" class="admin-input" type="number" min="1" step="1" placeholder="30" />
      </label>

      <label class="admin-field">
        <span>Источник (origin)</span>
        <input v-model="origin" class="admin-input" maxlength="32" placeholder="admin" />
      </label>

      <p v-if="errorText" class="admin-note admin-error">{{ errorText }}</p>
    </div>
    <template #footer>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="emit('close')">Отмена</button>
      <button type="button" class="admin-btn" :disabled="busy" @click="submit">
        {{ busy ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать' }}
      </button>
    </template>
  </AdminModal>
</template>

<style scoped>
.promo-form {
  display: grid;
  gap: 12px;
}
.admin-field {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
.admin-row .admin-input {
  flex: 1;
}
.unit-select {
  max-width: 110px;
}
</style>
