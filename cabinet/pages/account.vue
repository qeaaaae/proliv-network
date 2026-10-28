<script setup lang="ts">
import {
  Bell,
  Check,
  Gift,
  LoaderCircle,
  LogOut,
  Send,
} from '@lucide/vue'

const { push } = useToast()
const { user, logout } = useAuth()

interface Account {
  email: string | null
  hasPassword: boolean
  telegram: { username?: string; id: number }
  twoFa: boolean
}

interface Settings {
  settings: { notifySystem: boolean; notifyNews: boolean }
}

const { data, status } = useFetch<Account>('/api/account', { lazy: true })
const { data: settingsData } = useFetch<Settings>('/api/settings', { lazy: true })

const notifications = [
  {
    key: 'notifySystem' as const,
    label: 'Подписка и безопасность',
    hint: 'Окончание подписки, входы в аккаунт, смена ссылки',
  },
  { key: 'notifyNews' as const, label: 'Новости и акции', hint: 'Новые локации, тарифы и бонусы' },
]

async function toggleNotify(key: (typeof notifications)[number]['key'], value: boolean) {
  try {
    await $fetch('/api/settings', { method: 'POST', body: { [key]: value } })
    push('Настройка сохранена')
  } catch {
    push('Не удалось сохранить', 'error')
  }
}

const promo = ref('')
const promoPending = ref(false)

async function applyPromo() {
  if (!promo.value.trim() || promoPending.value) return
  promoPending.value = true
  try {
    const res = await $fetch<{ message: string }>('/api/promocode', {
      method: 'POST',
      body: { code: promo.value },
    })
    push(res.message)
    promo.value = ''
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось применить', 'error')
  } finally {
    promoPending.value = false
  }
}


</script>

<template>
  <div>
    <div class="page-head">
      <div class="page-kicker">Аккаунт</div>
      <h1>Настройки входа</h1>
    </div>

    <!-- Загрузка -->
    <section v-if="status === 'pending'" class="panel" aria-hidden="true">
      <div class="panel--pad stack">
        <div class="skel" style="height: 15px; width: 50%" />
        <div class="skel" style="height: 12px; width: 35%" />
        <div class="skel" style="height: 44px" />
        <div class="skel" style="height: 12px; width: 60%" />
      </div>
    </section>

    <template v-else>
    <!-- Данные аккаунта -->
    <section class="panel">
      <div class="row-line" style="border-top: 0">
        <span class="row-line__icon"><Send :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">Telegram</span>
          <span class="row-line__hint">
            {{ data?.telegram.username ? `@${data.telegram.username}` : 'Привязан' }} ·
            {{ data?.telegram.id }}
          </span>
        </span>
        <span class="badge badge--green"><Check :size="11" />Подключён</span>
      </div>
    </section>

    <!-- Промокод -->
    <section class="panel">
      <div class="panel__title">
        <Gift :size="17" />
        Активировать промокод
        <small>каждый код можно применить один раз</small>
      </div>
      <div class="panel--pad" style="display: flex; gap: 10px">
        <input
          v-model="promo"
          class="input"
          style="flex: 1; text-transform: uppercase"
          placeholder="PROLIV2026"
          @keydown.enter="applyPromo"
        />
        <button class="btn btn--primary" :disabled="promoPending || !promo.trim()" @click="applyPromo">
          <LoaderCircle v-if="promoPending" :size="15" class="spinner" />
          Применить
        </button>
      </div>
    </section>

    <!-- Уведомления -->
    <section class="panel">
      <div class="panel__title">
        <Bell :size="17" />
        Уведомления
        <small>работают в кабинете и в боте</small>
      </div>
      <div v-for="n in notifications" :key="n.key" class="row-line">
        <span class="row-line__icon"><Bell :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">{{ n.label }}</span>
          <span class="row-line__hint">{{ n.hint }}</span>
        </span>
        <label class="check">
          <input
            type="checkbox"
            :checked="settingsData?.settings[n.key]"
            @change="toggleNotify(n.key, ($event.target as HTMLInputElement).checked)"
          />
          <span class="check__box"><Check :size="13" :stroke-width="3" /></span>
        </label>
      </div>
    </section>

    <!-- Выход -->
    <section class="panel">
      <button class="row-line row-line--clickable" style="width: 100%; text-align: left; border-top: 0" @click="logout">
        <span class="row-line__icon"><LogOut :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">Выйти из аккаунта</span>
          <span class="row-line__hint">{{ user?.username ? `@${user.username}` : '' }}</span>
        </span>
      </button>
    </section>
    </template>
  </div>
</template>
