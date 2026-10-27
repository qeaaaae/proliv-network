<script setup lang="ts">
import {
  Bell,
  Check,
  Gift,
  KeyRound,
  LoaderCircle,
  LogOut,
  Mail,
  Send,
  ShieldCheck,
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
  settings: { notifyExpiry: boolean; notifyNews: boolean; notifySecurity: boolean }
}

const { data } = await useFetch<Account>('/api/account')
const { data: settingsData } = await useFetch<Settings>('/api/settings')

const notifications = [
  { key: 'notifyExpiry' as const, label: 'Окончание подписки', hint: 'Напомним за 3 дня и в день окончания' },
  { key: 'notifyNews' as const, label: 'Новости и акции', hint: 'Новые локации, тарифы и бонусы' },
  { key: 'notifySecurity' as const, label: 'Безопасность', hint: 'Входы в аккаунт и смена ссылки подписки' },
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

const soon = () => push('Появится после подключения общего бэкенда')
</script>

<template>
  <div>
    <div class="page-head">
      <div class="page-kicker">Аккаунт</div>
      <h1>Настройки входа</h1>
    </div>

    <!-- Данные аккаунта -->
    <section class="panel">
      <div class="row-line" style="border-top: 0">
        <span class="row-line__icon"><Mail :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">Email</span>
          <span class="row-line__hint">{{ data?.email ?? 'Почта не привязана' }}</span>
        </span>
        <button class="btn btn--ghost btn--sm" @click="soon">Добавить почту</button>
      </div>
      <div class="row-line">
        <span class="row-line__icon"><KeyRound :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">Пароль</span>
          <span class="row-line__hint">
            {{ data?.email ? 'Пароль не задан' : 'Сначала подтвердите почту' }}
          </span>
        </span>
        <button class="btn btn--ghost btn--sm" :disabled="!data?.email" @click="soon">Задать пароль</button>
      </div>
      <div class="row-line">
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
      <div class="row-line">
        <span class="row-line__icon"><ShieldCheck :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">Двухфакторная аутентификация</span>
          <span class="row-line__hint">
            {{ data?.hasPassword ? 'Выключена' : 'Сначала задайте пароль' }}
          </span>
        </span>
        <button class="btn btn--ghost btn--sm" :disabled="!data?.hasPassword" @click="soon">
          Включить
        </button>
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
  </div>
</template>
