<script setup lang="ts">
interface AdminPartner {
  partner_id: number
  user_id: number | null
  display_label: string
  username?: string | null
  status: string
  kind?: string
  commission_bps: number
  banner_below_stream?: boolean
  banner_on_stream?: boolean
  clients_count?: number
}

const gate = ref<'loading' | 'admin' | 'denied'>('loading')
const search = ref('')
const partners = ref<AdminPartner[]>([])
const selected = ref<AdminPartner | null>(null)
const busy = ref(false)
const notice = ref('')
const noticeError = ref(false)

const createUserId = ref('')
const createKind = ref<'standard' | 'streamer' | 'clipper'>('standard')
const createBelow = ref(false)
const createOn = ref(false)
const createImport = ref(false)
const createRate = ref('30')

const editKind = ref<'standard' | 'streamer' | 'clipper'>('standard')
const editBelow = ref(false)
const editOn = ref(false)
const editRate = ref('')
const editReason = ref('')

const kindLabels: Record<string, string> = {
  standard: 'Партнёр',
  streamer: 'Стример',
  clipper: 'Нарезчик',
}

function msg(text: string, error = false) {
  notice.value = text
  noticeError.value = error
}

async function api(path: string, opts: { method?: string; body?: unknown } = {}) {
  return await $fetch<Record<string, unknown>>(`/api/admin/${path}`, {
    method: (opts.method || 'GET') as 'GET',
    body: opts.body as never,
  })
}

async function checkAdmin() {
  try {
    await api('health')
    gate.value = 'admin'
    await loadPartners()
  } catch {
    gate.value = 'denied'
  }
}

async function loadPartners() {
  busy.value = true
  try {
    const res = await api(
      `partners?limit=10${search.value.trim() ? `&search=${encodeURIComponent(search.value.trim())}` : ''}`,
    )
    partners.value = (res.partners as AdminPartner[]) || []
  } catch (e) {
    msg(`Ошибка загрузки: ${(e as { data?: { error?: string } }).data?.error || 'failed'}`, true)
  } finally {
    busy.value = false
  }
}

function openPartner(p: AdminPartner) {
  selected.value = p
  editKind.value = (p.kind || 'standard') as typeof editKind.value
  editBelow.value = Boolean(p.banner_below_stream)
  editOn.value = Boolean(p.banner_on_stream)
  editRate.value = String(p.commission_bps / 100)
  editReason.value = ''
  notice.value = ''
}

async function createPartner() {
  const uid = Number(createUserId.value)
  if (!uid) return msg('Введите user_id', true)
  busy.value = true
  try {
    const res = await api('partners', {
      method: 'POST',
      body: {
        user_id: uid,
        commission_bps: createKind.value === 'standard' ? Math.round(Number(createRate.value) * 100) : null,
        welcome_message: null,
        kind: createKind.value,
        banner_below_stream: createKind.value === 'streamer' && createBelow.value,
        banner_on_stream: createKind.value === 'streamer' && createOn.value,
      },
    })
    const partner = res.partner as AdminPartner
    if (createImport.value && partner?.partner_id) {
      await api(`partners/${partner.partner_id}/referral-import`, {
        method: 'POST',
        body: { confirm_without_retroactive_commission: true },
      })
    }
    msg(`Партнёр #${partner.partner_id} создан, ставка ${partner.commission_bps / 100}%`)
    createUserId.value = ''
    await loadPartners()
    if (partner?.partner_id) openPartner(partner)
  } catch (e) {
    msg(`Ошибка: ${(e as { data?: { error?: string } }).data?.error || 'failed'}`, true)
  } finally {
    busy.value = false
  }
}

async function saveKind() {
  if (!selected.value) return
  busy.value = true
  try {
    const res = await api(`partners/${selected.value.partner_id}/kind`, {
      method: 'POST',
      body: {
        kind: editKind.value,
        banner_below_stream: editKind.value === 'streamer' ? editBelow.value : false,
        banner_on_stream: editKind.value === 'streamer' ? editOn.value : false,
        reason: editReason.value.trim() || null,
      },
    })
    const partner = res.partner as AdminPartner
    msg(`Сохранено: тип '${kindLabels[partner.kind || 'standard'] || partner.kind}', ставка ${partner.commission_bps / 100}%`)
    selected.value = { ...selected.value, ...partner }
    await loadPartners()
  } catch (e) {
    msg(`Ошибка: ${(e as { data?: { error?: string } }).data?.error || 'failed'}`, true)
  } finally {
    busy.value = false
  }
}

async function saveRate() {
  if (!selected.value) return
  if (!editReason.value.trim()) return msg('Укажите причину смены ставки', true)
  busy.value = true
  try {
    const res = await api(`partners/${selected.value.partner_id}/commission-rate`, {
      method: 'POST',
      body: {
        commission_bps: Math.round(Number(editRate.value) * 100),
        reason: editReason.value.trim(),
      },
    })
    const partner = res.partner as AdminPartner
    msg(`Ставка обновлена: ${partner.commission_bps / 100}%`)
    selected.value = { ...selected.value, ...partner }
    await loadPartners()
  } catch (e) {
    msg(`Ошибка: ${(e as { data?: { error?: string } }).data?.error || 'failed'}`, true)
  } finally {
    busy.value = false
  }
}

onMounted(checkAdmin)
</script>

<template>
  <main class="admin-page">
    <p v-if="gate === 'loading'" class="admin-note">Проверка доступа...</p>
    <div v-else-if="gate === 'denied'" class="admin-card">
      <h1>Нет доступа</h1>
      <p class="admin-note">Этот раздел доступен только администраторам.</p>
    </div>

    <template v-else>
      <h1>Админка · Партнёры</h1>
      <p v-if="notice" class="admin-note" :class="{ 'admin-error': noticeError }">{{ notice }}</p>

      <section class="admin-card">
        <h2>Создать партнёра</h2>
        <label class="admin-field">
          <span>user_id</span>
          <input v-model="createUserId" type="number" placeholder="Внутренний id юзера" />
        </label>
        <label class="admin-field">
          <span>Тип</span>
          <select v-model="createKind">
            <option value="standard">Партнёр</option>
            <option value="streamer">Стример</option>
            <option value="clipper">Нарезчик</option>
          </select>
        </label>
        <label v-if="createKind === 'standard'" class="admin-field">
          <span>Ставка, %</span>
          <input v-model="createRate" type="number" min="0" max="100" step="0.01" />
        </label>
        <template v-if="createKind === 'streamer'">
          <label class="admin-check"><input v-model="createBelow" type="checkbox" /> Баннер под стримом</label>
          <label class="admin-check"><input v-model="createOn" type="checkbox" /> Баннер на стриме</label>
          <p class="admin-note">Ставка выставится автоматически по размещениям (40/50/60%).</p>
        </template>
        <p v-if="createKind === 'clipper'" class="admin-note">Выплаты нарезчику - ручные корректировки за просмотры, ревшара 0%.</p>
        <label class="admin-check"><input v-model="createImport" type="checkbox" /> Импортировать его рефералов в клиенты</label>
        <button class="admin-btn" :disabled="busy" @click="createPartner">Создать</button>
      </section>

      <section class="admin-card">
        <h2>Найти партнёра</h2>
        <div class="admin-row">
          <input v-model="search" placeholder="Имя, @username или user_id" @keyup.enter="loadPartners" />
          <button class="admin-btn" :disabled="busy" @click="loadPartners">Найти</button>
        </div>
        <ul class="admin-list">
          <li v-for="p in partners" :key="p.partner_id">
            <button type="button" class="admin-list-item" @click="openPartner(p)">
              <strong>{{ p.display_label }}</strong>
              <span>{{ p.username ? '@' + p.username : `#${p.user_id}` }} · {{ kindLabels[p.kind || 'standard'] }} · {{ p.commission_bps / 100 }}%</span>
            </button>
          </li>
          <li v-if="!partners.length && !busy" class="admin-note">Никого не найдено</li>
        </ul>
      </section>

      <section v-if="selected" class="admin-card">
        <h2>{{ selected.display_label }} <small>#{{ selected.partner_id }} · {{ selected.status }}</small></h2>
        <label class="admin-field">
          <span>Тип</span>
          <select v-model="editKind">
            <option value="standard">Партнёр</option>
            <option value="streamer">Стример</option>
            <option value="clipper">Нарезчик</option>
          </select>
        </label>
        <template v-if="editKind === 'streamer'">
          <label class="admin-check"><input v-model="editBelow" type="checkbox" /> Баннер под стримом</label>
          <label class="admin-check"><input v-model="editOn" type="checkbox" /> Баннер на стриме</label>
        </template>
        <label class="admin-field">
          <span>Комментарий (для аудита)</span>
          <input v-model="editReason" placeholder="Например: договорились в лс" />
        </label>
        <div class="admin-row">
          <button class="admin-btn" :disabled="busy" @click="saveKind">Сохранить тип</button>
        </div>

        <h3 class="admin-sub">Ставка вручную</h3>
        <div class="admin-row">
          <input v-model="editRate" type="number" min="0" max="100" step="0.01" style="max-width: 90px" />
          <span class="admin-note">%</span>
          <button class="admin-btn" :disabled="busy" @click="saveRate">Сменить ставку</button>
        </div>
        <p class="admin-note">Ручная ставка требует комментарий и действует только на новые платежи.</p>
      </section>
    </template>
  </main>
</template>

<style scoped>
.admin-page {
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 16px 60px;
  display: grid;
  gap: 16px;
  color: var(--text, #e8ecf4);
}
.admin-card {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: 14px;
  background: var(--card, #141a26);
  border: 1px solid var(--border, #232c3d);
}
.admin-field {
  display: grid;
  gap: 6px;
  font-size: 13px;
  color: var(--muted, #8b95a8);
}
.admin-field input,
.admin-field select,
.admin-row input {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border, #232c3d);
  background: var(--bg, #0d1119);
  color: inherit;
  font-size: 14px;
}
.admin-check {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 14px;
}
.admin-btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: 0;
  background: var(--accent, #3b82f6);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.admin-btn:disabled {
  opacity: 0.5;
}
.admin-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.admin-row input {
  flex: 1;
}
.admin-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}
.admin-list-item {
  width: 100%;
  display: grid;
  gap: 2px;
  text-align: left;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid var(--border, #232c3d);
  background: transparent;
  color: inherit;
  cursor: pointer;
}
.admin-list-item:hover {
  border-color: var(--accent, #3b82f6);
}
.admin-list-item span {
  font-size: 12px;
  color: var(--muted, #8b95a8);
}
.admin-note {
  font-size: 12px;
  color: var(--muted, #8b95a8);
  margin: 0;
}
.admin-error {
  color: #f87171;
}
.admin-sub {
  margin: 8px 0 0;
  font-size: 14px;
}
h1 {
  font-size: 20px;
  margin: 0;
}
h2 {
  font-size: 16px;
  margin: 0;
}
h2 small {
  color: var(--muted, #8b95a8);
  font-weight: 400;
}
</style>
