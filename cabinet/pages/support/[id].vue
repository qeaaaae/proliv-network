<script setup lang="ts">
import { ArrowLeft, CheckCheck, LifeBuoy, LoaderCircle, Send } from '@lucide/vue'

const route = useRoute()
const { push } = useToast()
const fmt = useFormat()

interface Ticket {
  id: string
  subject: string
  status: 'open' | 'answered' | 'closed'
  createdAt: string
  messages: { from: 'user' | 'support'; text: string; at: string }[]
}

const {
  data: ticket,
  refresh,
  status,
  error,
} = useFetch<Ticket>(`/api/tickets/${route.params.id}`, { lazy: true })

const reply = ref('')
const pending = ref(false)
const threadEl = ref<HTMLElement>()

async function scrollDown() {
  await nextTick()
  threadEl.value?.scrollTo({ top: threadEl.value.scrollHeight, behavior: 'smooth' })
}

// Пользовательского закрытия тикета в API бэкенда нет - закрывает поддержка.
async function send() {
  const text = reply.value.trim()
  if (!text || pending.value) return
  pending.value = true
  try {
    await $fetch(`/api/tickets/${route.params.id}/reply`, { method: 'POST', body: { text } })
    reply.value = ''
    await refresh()
    await scrollDown()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Ошибка', 'error')
  } finally {
    pending.value = false
  }
}

onMounted(scrollDown)
watch(() => ticket.value?.messages?.length, scrollDown)
</script>

<template>
  <div v-if="ticket">
    <div class="page-head">
      <NuxtLink to="/support" class="app-top__back" style="margin-bottom: 10px; display: inline-flex">
        <ArrowLeft :size="15" />
        Все обращения
      </NuxtLink>
      <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap">
        <h1 style="font-size: clamp(18px, 3vw, 24px)">{{ ticket.subject }}</h1>
        <StatusBadge :status="ticket.status" />
      </div>
      <p class="muted">{{ ticket.id }} · создано {{ fmt.dateTime(ticket.createdAt) }}</p>
    </div>

    <section class="panel">
      <div ref="threadEl" class="thread" style="max-height: 52dvh; overflow-y: auto">
        <div
          v-for="(m, i) in ticket.messages"
          :key="i"
          class="bubble"
          :class="`bubble--${m.from === 'user' ? 'user' : 'support'}`"
        >
          {{ m.text }}
          <time>{{ m.from === 'user' ? 'Вы' : 'Поддержка' }} · {{ fmt.dateTime(m.at) }}</time>
        </div>
      </div>

      <div class="reply-bar">
        <input
          v-model="reply"
          class="input"
          placeholder="Написать сообщение…"
          maxlength="4000"
          @keydown.enter="send"
        />
        <button class="btn btn--primary" :disabled="pending || !reply.trim()" @click="send">
          <LoaderCircle v-if="pending" :size="15" class="spinner" />
          <Send v-else :size="15" />
        </button>
      </div>
    </section>

    <div v-if="ticket.status === 'closed'" style="margin-top: 14px; text-align: right">
      <span class="muted" style="font-size: 12px">
        <CheckCheck :size="13" style="vertical-align: -2px" /> Обращение закрыто - напишите, чтобы открыть снова
      </span>
    </div>
  </div>

  <div v-else-if="status === 'success' || error" class="panel">
    <div class="empty">
      <div class="empty__icon"><LifeBuoy :size="24" /></div>
      <h2>Обращение не найдено</h2>
      <p>Проверьте ссылку или вернитесь к списку</p>
      <NuxtLink to="/support" class="btn btn--primary">Все обращения</NuxtLink>
    </div>
  </div>

  <section v-else class="panel" aria-hidden="true">
    <div class="panel--pad stack">
      <div class="skel" style="height: 15px; width: 55%" />
      <div class="skel" style="height: 44px; width: 75%" />
      <div class="skel" style="height: 34px; width: 60%; margin-left: auto" />
      <div class="skel" style="height: 44px; width: 70%" />
    </div>
  </section>
</template>
