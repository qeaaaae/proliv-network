<script setup lang="ts">
import { adminErrorMessage, fmtDateTime } from './format'
import type { AdminLogEntry, AdminLogsResponse } from './types'

const props = defineProps<{ userId: number }>()

const { call } = useAdminApi()

const logs = ref<AdminLogEntry[]>([])
const total = ref(0)
const page = ref(0)
const pageSize = 20
const busy = ref(false)
const error = ref('')
const loaded = ref(false)

async function load(p = 0) {
  busy.value = true
  error.value = ''
  try {
    const res = await call<AdminLogsResponse>('logs', {
      query: { user_id: props.userId, page: p, page_size: pageSize },
    })
    logs.value = res.logs || []
    total.value = res.total || 0
    page.value = res.page || 0
    loaded.value = true
  } catch (e) {
    error.value = adminErrorMessage(e)
  } finally {
    busy.value = false
  }
}

const pages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

watch(
  () => props.userId,
  () => {
    logs.value = []
    total.value = 0
    page.value = 0
    loaded.value = false
    error.value = ''
  },
)
</script>

<template>
  <section class="admin-card">
    <h2>Журнал событий</h2>
    <div class="admin-row">
      <button class="admin-btn ghost" :disabled="busy" @click="load(0)">
        {{ loaded ? 'Обновить' : 'Показать события' }}
      </button>
      <span v-if="loaded" class="admin-note">Всего: {{ total }}</span>
    </div>
    <p v-if="error" class="admin-note admin-error">{{ error }}</p>

    <template v-if="loaded">
      <div v-if="logs.length" class="adm-users-table-wrap">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Событие</th>
              <th>Автор</th>
              <th>Детали</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in logs" :key="entry.log_id">
              <td class="adm-users-nowrap">{{ fmtDateTime(entry.timestamp) }}</td>
              <td>
                {{ entry.event_type || '—' }}
                <AdminBadge v-if="entry.is_admin_event" tone="warning">админ</AdminBadge>
              </td>
              <td>{{ entry.user_label || '—' }}</td>
              <td class="adm-users-log-content">{{ entry.content || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="admin-note">Событий нет.</p>

      <div v-if="pages > 1" class="admin-row adm-users-pager">
        <button class="admin-btn ghost" :disabled="busy || page <= 0" @click="load(page - 1)">Назад</button>
        <span class="admin-note">Страница {{ page + 1 }} из {{ pages }}</span>
        <button class="admin-btn ghost" :disabled="busy || page >= pages - 1" @click="load(page + 1)">Вперёд</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.adm-users-table-wrap {
  overflow-x: auto;
}
.adm-users-nowrap {
  white-space: nowrap;
}
.adm-users-log-content {
  max-width: 320px;
  word-break: break-word;
  white-space: pre-wrap;
}
.adm-users-pager {
  justify-content: center;
}
h2 {
  margin: 0;
  font-size: 15px;
}
</style>
