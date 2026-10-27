<script setup lang="ts">
import { CheckCircle2, LoaderCircle, XCircle } from '@lucide/vue'

useHead({ title: 'Пробный период - Proliv Network' })

interface TrialResult {
  activated?: boolean
  days_left?: number
  message_key?: string
}

const state = ref<'pending' | 'ok' | 'fail'>('pending')
const message = ref('')

onMounted(async () => {
  try {
    const res = await $fetch<TrialResult>('/api/trial', { method: 'POST' })
    if (res?.activated === false) throw new Error(res.message_key || 'failed')
    state.value = 'ok'
    message.value =
      typeof res?.days_left === 'number'
        ? `Подписка активна - осталось ${res.days_left} дн.`
        : 'Пробный период активирован'
  } catch (e) {
    state.value = 'fail'
    message.value =
      (e as { data?: { statusMessage?: string } }).data?.statusMessage ||
      'Не удалось активировать пробный период'
  }
})
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-kicker">Proliv Network</div>
        <h1>Пробный период</h1>
      </div>
    </div>

    <section class="panel">
      <div class="panel--pad stack" style="align-items: center; text-align: center; padding: 40px 20px">
        <template v-if="state === 'pending'">
          <LoaderCircle :size="28" class="spinner" />
          <p class="muted">Активируем пробный период...</p>
        </template>
        <template v-else-if="state === 'ok'">
          <CheckCircle2 :size="32" style="color: var(--accent)" />
          <h2 style="margin: 0">Триал активирован</h2>
          <p class="muted" style="margin: 0">{{ message }}</p>
          <NuxtLink class="btn btn--primary" to="/">В кабинет</NuxtLink>
        </template>
        <template v-else>
          <XCircle :size="32" style="color: var(--danger, #f87171)" />
          <h2 style="margin: 0">Не получилось</h2>
          <p class="muted" style="margin: 0">{{ message }}</p>
          <NuxtLink class="btn btn--ghost" to="/">В кабинет</NuxtLink>
        </template>
      </div>
    </section>
  </div>
</template>
