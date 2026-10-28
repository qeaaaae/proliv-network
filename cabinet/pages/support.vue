<script setup lang="ts">
import { ChevronRight, LifeBuoy, LoaderCircle, Plus } from '@lucide/vue'

const { push } = useToast()
const fmt = useFormat()

interface TicketListItem {
  id: string
  subject: string
  status: 'open' | 'answered' | 'closed'
  updatedAt: string
  lastMessage: string
}

const { data: tickets, status, refresh } = useFetch<TicketListItem[]>('/api/tickets', {
  lazy: true,
})

const formOpen = ref(false)
const subject = ref('')
const text = ref('')
const pending = ref(false)

async function createTicket() {
  if (pending.value) return
  pending.value = true
  try {
    const t = await $fetch<{ id: string }>('/api/tickets', {
      method: 'POST',
      body: { subject: subject.value, text: text.value },
    })
    subject.value = text.value = ''
    formOpen.value = false
    await navigateTo(`/support/${t.id}`)
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Ошибка', 'error')
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-head" style="display: flex; align-items: flex-end; justify-content: space-between; gap: 12px">
      <div>
        <div class="page-kicker">Помощь</div>
        <h1>Поддержка</h1>
      </div>
      <button v-if="tickets?.length" class="btn btn--ghost btn--sm" @click="formOpen = !formOpen">
        <Plus :size="15" />
        Новое обращение
      </button>
    </div>

    <section class="panel">
      <!-- Загрузка -->
      <div v-if="status === 'pending'" class="panel--pad stack" aria-hidden="true">
        <div class="skel" style="height: 15px; width: 60%" />
        <div class="skel" style="height: 12px; width: 80%" />
        <div class="skel" style="height: 15px; width: 45%" />
        <div class="skel" style="height: 12px; width: 70%" />
      </div>

      <template v-else>
      <!-- Форма нового обращения -->
      <div v-if="formOpen || !tickets?.length" class="panel--pad stack" style="border-bottom: 1px solid var(--line)">
        <div class="field">
          <span>Тема</span>
          <input v-model="subject" class="input" placeholder="Например: не подключается локация DE" maxlength="120" />
        </div>
        <div class="field">
          <span>Сообщение</span>
          <textarea v-model="text" class="textarea" placeholder="Опишите проблему или вопрос" maxlength="4000" />
        </div>
        <button
          class="btn btn--primary"
          style="justify-self: start"
          :disabled="pending || !subject.trim() || !text.trim()"
          @click="createTicket"
        >
          <LoaderCircle v-if="pending" :size="15" class="spinner" />
          Отправить обращение
        </button>
      </div>

      <!-- Список -->
      <NuxtLink
        v-for="t in tickets"
        :key="t.id"
        :to="`/support/${t.id}`"
        class="ticket-row"
      >
        <div class="ticket-row__body">
          <div class="ticket-row__subject">{{ t.subject }}</div>
          <div class="ticket-row__meta">
            <span style="display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
              {{ t.lastMessage }}
            </span>
            {{ fmt.dateTime(t.updatedAt) }}
          </div>
        </div>
        <StatusBadge :status="t.status" />
        <ChevronRight :size="16" class="muted" />
      </NuxtLink>

      <div v-if="!tickets?.length" class="empty" style="padding: 30px 20px">
        <div class="empty__icon"><LifeBuoy :size="22" /></div>
        <p style="margin: 0 auto">Обращения из кабинета и из бота прилетают в одно место - ответим и там, и тут.</p>
      </div>
      </template>
    </section>
  </div>
</template>
