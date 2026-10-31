<script setup lang="ts">
interface PartnerOut {
  partner_id: number
  user_id: number | null
  display_label: string
  status: string
  commission_bps: number
  kind: string
}

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  close: []
  created: [partner: PartnerOut]
  notice: [text: string, isError: boolean]
}>()

const { call } = useAdminApi()

const userId = ref('')
const kind = ref('standard')
const bannerBelow = ref(false)
const bannerOn = ref(false)
const ratePct = ref('30')
const importReferrals = ref(false)
const busy = ref(false)
const formError = ref('')

const kindItems = [
  { value: 'standard', label: 'Партнёр' },
  { value: 'streamer', label: 'Стример' },
  { value: 'clipper', label: 'Нарезчик' },
]

watch(
  () => props.open,
  (value) => {
    if (!value) return
    userId.value = ''
    kind.value = 'standard'
    bannerBelow.value = false
    bannerOn.value = false
    ratePct.value = '30'
    importReferrals.value = false
    formError.value = ''
  },
)

function errorText(err: unknown): string {
  const data = (err as { data?: { error?: string; message?: string } }).data || {}
  return data.message || data.error || (err as Error).message || 'request_failed'
}

async function submit() {
  const uid = Number(userId.value)
  if (!Number.isInteger(uid) || uid <= 0) {
    formError.value = 'Укажите корректный user_id'
    return
  }
  let commissionBps: number | null = null
  if (kind.value === 'standard') {
    const pct = Number(ratePct.value)
    if (!Number.isFinite(pct) || pct < 0 || pct > 100) {
      formError.value = 'Ставка должна быть от 0 до 100%'
      return
    }
    commissionBps = Math.round(pct * 100)
  }
  busy.value = true
  formError.value = ''
  try {
    const res = await call<{ partner: PartnerOut }>('partners', {
      method: 'POST',
      body: {
        user_id: uid,
        commission_bps: commissionBps,
        welcome_message: null,
        kind: kind.value,
        banner_below_stream: kind.value === 'streamer' && bannerBelow.value,
        banner_on_stream: kind.value === 'streamer' && bannerOn.value,
      },
    })
    const partner = res.partner
    if (importReferrals.value && partner?.partner_id) {
      try {
        const imp = await call<{ result: { imported: number; existing: number; conflicts: number } }>(
          `partners/${partner.partner_id}/referral-import`,
          { method: 'POST', body: { confirm_without_retroactive_commission: true } },
        )
        emit(
          'notice',
          `Партнёр #${partner.partner_id} создан. Импортировано рефералов: ${imp.result.imported} (конфликтов: ${imp.result.conflicts})`,
          false,
        )
      } catch {
        emit(
          'notice',
          `Партнёр #${partner.partner_id} создан, но импорт рефералов не удался - повторите из карточки`,
          true,
        )
      }
    } else {
      emit('notice', `Партнёр #${partner.partner_id} создан`, false)
    }
    emit('created', partner)
    emit('close')
  } catch (err) {
    formError.value = `Ошибка: ${errorText(err)}`
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AdminModal :open="open" title="Новый партнёр" @close="emit('close')">
    <label class="admin-field">
      <span>user_id</span>
      <input v-model="userId" class="admin-input" type="number" min="1" placeholder="Внутренний id юзера" />
    </label>
    <label class="admin-field">
      <span>Тип</span>
      <AdminSelect v-model="kind" :items="kindItems" />
    </label>
    <template v-if="kind === 'streamer'">
      <label class="admin-check">
        <input v-model="bannerBelow" type="checkbox" />
        Баннер под стримом
      </label>
      <label class="admin-check">
        <input v-model="bannerOn" type="checkbox" />
        Баннер на стриме
      </label>
      <p class="admin-note">Ставка выставится автоматически по размещениям.</p>
    </template>
    <label v-if="kind === 'standard'" class="admin-field">
      <span>Ставка, %</span>
      <input v-model="ratePct" class="admin-input" type="number" min="0" max="100" step="0.01" />
    </label>
    <p v-if="kind === 'clipper'" class="admin-note">
      Выплаты нарезчику - ручные корректировки за просмотры, ревшара 0%.
    </p>
    <label class="admin-check">
      <input v-model="importReferrals" type="checkbox" />
      Импортировать рефералов юзера в клиенты партнёра
    </label>
    <p v-if="importReferrals" class="admin-note">
      Комиссия за уже оплаченные платежи импортированных рефералов не начисляется.
    </p>
    <p v-if="formError" class="admin-note admin-error">{{ formError }}</p>
    <template #footer>
      <button type="button" class="admin-btn ghost" :disabled="busy" @click="emit('close')">Отмена</button>
      <button type="button" class="admin-btn" :disabled="busy" @click="submit">
        {{ busy ? 'Создание...' : 'Создать' }}
      </button>
    </template>
  </AdminModal>
</template>

<style scoped>
.admin-field {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
</style>
