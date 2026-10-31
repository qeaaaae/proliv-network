<script setup lang="ts">
import { adminErrorMessage } from './format'
import type { AdminInternalSquad, AdminPanelSquadOverrides } from './types'

const props = defineProps<{ userId: number; overrides: AdminPanelSquadOverrides | null }>()
const emit = defineEmits<{ updated: []; notice: [text: string, isError: boolean] }>()

const { call } = useAdminApi()
const busy = ref(false)

const managed = computed(() => props.overrides?.managed_internal_squads || [])
const manual = computed(() => props.overrides?.manual_internal_squads || [])
const effective = computed(() => props.overrides?.effective_internal_squad_uuids || [])
const external = computed(() => props.overrides?.external || null)

// Модалка редактирования сквадов
const editOpen = ref(false)
const allSquads = ref<AdminInternalSquad[]>([])
const selected = ref<Set<string>>(new Set())
const externalMode = ref('inherit')
const externalUuid = ref('')
const squadsError = ref('')

function squadLabel(uuid: string): string {
  const fromManaged = managed.value.find((s) => s.uuid === uuid)
  const fromManual = manual.value.find((s) => s.uuid === uuid)
  const fromAll = allSquads.value.find((s) => s.uuid === uuid)
  return fromManaged?.label || fromManual?.label || fromAll?.name || uuid.slice(0, 8)
}

async function openEdit() {
  editOpen.value = true
  squadsError.value = ''
  selected.value = new Set(effective.value)
  externalMode.value = external.value?.mode === 'set' ? 'set' : external.value?.mode === 'cleared' ? 'cleared' : 'inherit'
  externalUuid.value = external.value?.manual_uuid || ''
  if (!allSquads.value.length) {
    try {
      const res = await call<{ squads: AdminInternalSquad[] }>('panel/internal-squads')
      allSquads.value = res.squads || []
    } catch (e) {
      squadsError.value = adminErrorMessage(e)
    }
  }
}

function toggle(uuid: string) {
  const next = new Set(selected.value)
  if (next.has(uuid)) next.delete(uuid)
  else next.add(uuid)
  selected.value = next
}

async function saveSquads() {
  busy.value = true
  squadsError.value = ''
  const current = new Set(effective.value)
  const add = [...selected.value].filter((u) => !current.has(u))
  const remove = [...current].filter((u) => !selected.value.has(u))
  const body: Record<string, unknown> = {
    add_internal_squad_uuids: add,
    remove_internal_squad_uuids: remove,
    sync_panel: true,
  }
  const prevMode = external.value?.mode || 'inherit'
  if (externalMode.value !== prevMode || (externalMode.value === 'set' && externalUuid.value !== external.value?.manual_uuid)) {
    body.external_mode = externalMode.value
    if (externalMode.value === 'set') body.external_squad_uuid = externalUuid.value.trim()
  }
  try {
    await call(`users/${props.userId}/squad-overrides`, { method: 'PATCH', body })
    emit('notice', 'Сквады обновлены', false)
    editOpen.value = false
    emit('updated')
  } catch (e) {
    squadsError.value = adminErrorMessage(e)
  } finally {
    busy.value = false
  }
}

async function refreshSquads() {
  busy.value = true
  try {
    await call(`users/${props.userId}/squad-overrides/refresh`, { method: 'POST', body: {} })
    emit('notice', 'Сквады синхронизированы с панелью', false)
    emit('updated')
  } catch (e) {
    emit('notice', adminErrorMessage(e), true)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <section class="admin-card">
    <div class="admin-row" style="justify-content: space-between">
      <h2>Сквады панели</h2>
      <div class="admin-row">
        <button class="admin-btn ghost" :disabled="busy" @click="refreshSquads">Синхронизировать</button>
        <button class="admin-btn ghost" :disabled="busy" @click="openEdit">Изменить</button>
      </div>
    </div>

    <template v-if="overrides">
      <p v-if="!overrides.panel_snapshot_available" class="admin-note">
        Снапшот панели недоступен - данные могут быть неполными.
      </p>
      <div class="adm-users-fields">
        <AdminUsersFieldRow label="Внутренние сквады">
          <template v-if="effective.length">
            <AdminBadge v-for="uuid in effective" :key="uuid">{{ squadLabel(uuid) }}</AdminBadge>
          </template>
          <template v-else>—</template>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow v-if="manual.length" label="Ручные переопределения">
          <AdminBadge v-for="s in manual" :key="s.uuid" tone="warning">{{ s.label || s.uuid.slice(0, 8) }}</AdminBadge>
        </AdminUsersFieldRow>
        <AdminUsersFieldRow label="Внешний сквад">
          <template v-if="external?.mode === 'set'">
            Вручную: {{ external.manual_uuid || '—' }}
          </template>
          <template v-else-if="external?.mode === 'cleared'">Сброшен</template>
          <template v-else-if="external?.effective_uuid">Наследуется ({{ external.effective_uuid.slice(0, 8) }})</template>
          <template v-else>—</template>
        </AdminUsersFieldRow>
      </div>
    </template>
    <p v-else class="admin-note">Данных о сквадах нет (пользователь не привязан к панели).</p>

    <AdminModal :open="editOpen" title="Сквады пользователя" @close="editOpen = false">
      <p v-if="squadsError" class="admin-note admin-error">{{ squadsError }}</p>
      <template v-if="allSquads.length">
        <p class="admin-note">Внутренние сквады:</p>
        <label v-for="s in allSquads" :key="s.uuid" class="admin-check">
          <input type="checkbox" :checked="selected.has(s.uuid)" @change="toggle(s.uuid)" />
          {{ s.name }} <small class="admin-note">{{ s.uuid.slice(0, 8) }}</small>
        </label>
      </template>
      <p v-else-if="!squadsError" class="admin-note">Загрузка сквадов...</p>

      <div class="adm-users-field-edit">
        <span>Внешний сквад</span>
        <AdminSelect
          v-model="externalMode"
          :items="[
            { value: 'inherit', label: 'Наследовать' },
            { value: 'set', label: 'Задать вручную' },
            { value: 'cleared', label: 'Сбросить' },
          ]"
        />
        <input
          v-if="externalMode === 'set'"
          v-model="externalUuid"
          class="admin-input"
          placeholder="UUID внешнего сквада"
        />
      </div>

      <template #footer>
        <button class="admin-btn ghost" :disabled="busy" @click="editOpen = false">Отмена</button>
        <button class="admin-btn" :disabled="busy" @click="saveSquads">Сохранить</button>
      </template>
    </AdminModal>
  </section>
</template>

<style scoped>
.adm-users-fields {
  display: grid;
  gap: 6px;
}
.adm-users-field-edit {
  display: grid;
  gap: 8px;
  margin-top: 8px;
  font-size: 13px;
  color: var(--adm-muted, #8b95a8);
}
h2 {
  margin: 0;
  font-size: 15px;
}
</style>
