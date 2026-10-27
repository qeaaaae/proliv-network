<script setup lang="ts">
import { Eye, EyeOff, LoaderCircle, Send } from '@lucide/vue'

definePageMeta({ layout: false })
useHead({ title: 'Вход - Proliv Network' })

const config = useRuntimeConfig()
const route = useRoute()
const { push } = useToast()
const { ensure, loaded } = useAuth()

const mode = ref<'login' | 'register'>('login')
const pending = ref(false)

const login = ref('')
const password = ref('')
const showPassword = ref(false)

async function goNext() {
  // сессия поставилась только что - сбрасываем кэш и подтягиваем /me до перехода
  loaded.value = false
  await ensure()
  return navigateTo(typeof route.query.next === 'string' ? route.query.next : '/')
}

async function onTelegramAuth(user: Record<string, unknown>) {
  if (pending.value) return
  pending.value = true
  try {
    await $fetch('/api/auth/telegram', { method: 'POST', body: user })
    await goNext()
  } catch {
    push('Не удалось войти. Попробуйте ещё раз', 'error')
  } finally {
    pending.value = false
  }
}

// Telegram OIDC (oauth.telegram.org): открываем попап, получаем id_token
// через postMessage, меняем на сессию через наш BFF. nonce приходит с бэкенда.
const oauthPending = ref(false)

function waitForOAuthMessage(popup: Window | null): Promise<{ id_token?: string; error?: string }> {
  return new Promise((resolve, reject) => {
    const timer = window.setInterval(() => {
      if (popup?.closed) {
        cleanup()
        reject(new Error('popup_closed'))
      }
    }, 500)
    const onMessage = (ev: MessageEvent) => {
      if (ev.origin !== 'https://oauth.telegram.org') return
      cleanup()
      resolve(ev.data as { id_token?: string; error?: string })
    }
    const cleanup = () => {
      window.clearInterval(timer)
      window.removeEventListener('message', onMessage)
    }
    window.addEventListener('message', onMessage)
  })
}

async function onTelegramOAuth() {
  if (pending.value || oauthPending.value) return
  oauthPending.value = true
  try {
    const res = await $fetch<{ nonce?: string; client_id?: number | string; request_access?: string[] }>(
      '/api/auth/telegram/nonce',
      { method: 'POST' },
    )
    if (!res?.nonce || !res?.client_id) throw new Error('oauth_not_configured')

    const scopes = ['openid', 'profile']
    for (const access of res.request_access ?? []) {
      if (access === 'phone') scopes.push('phone')
      if (access === 'write') scopes.push('telegram:bot_access')
    }

    const authUrl = new URL('https://oauth.telegram.org/auth')
    authUrl.searchParams.set('response_type', 'post_message')
    authUrl.searchParams.set('client_id', String(res.client_id))
    authUrl.searchParams.set('redirect_uri', `${window.location.origin}/auth`)
    authUrl.searchParams.set('scope', scopes.join(' '))
    authUrl.searchParams.set('nonce', res.nonce)
    authUrl.searchParams.set('lang', 'ru')

    const popup = window.open(authUrl.toString(), 'tg_oauth', 'width=550,height=650,popup=true')
    const data = await waitForOAuthMessage(popup)
    if (!data?.id_token) throw new Error(data?.error || 'oauth_failed')

    await $fetch('/api/auth/telegram', {
      method: 'POST',
      body: { idToken: data.id_token, nonce: res.nonce },
    })
    await goNext()
  } catch {
    push('Не удалось войти через Telegram. Попробуйте ещё раз', 'error')
  } finally {
    oauthPending.value = false
  }
}

const isMiniApp = ref(false)

// Внутри Telegram Mini App входим автоматически по initData
onMounted(async () => {
  const initData = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData
  if (!initData || pending.value) return
  isMiniApp.value = true
  pending.value = true
  try {
    await $fetch('/api/auth/telegram', { method: 'POST', body: { initData } })
    await goNext()
  } catch {
    // остаёмся на странице входа - можно войти через виджет
  } finally {
    pending.value = false
  }
})

async function submit() {
  if (mode.value === 'register') {
    push('Регистрация откроется после подключения бэкенда - пока войдите через Telegram', 'error')
    return
  }
  if (pending.value || !login.value || !password.value) return
  pending.value = true
  try {
    // Сначала настоящий email-вход бэкенда; dev-логин (admin/admin) - фолбэк
    // для стенда, роут сам отвечает 404, когда выключен.
    const isDevLogin = login.value.trim() === 'admin'
    try {
      await $fetch('/api/auth/email', {
        method: 'POST',
        body: { email: login.value, password: password.value },
      })
    } catch (err) {
      if (!isDevLogin) throw err
      await $fetch('/api/auth/dev', {
        method: 'POST',
        body: { login: login.value, password: password.value },
      })
    }
    await goNext()
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Ошибка входа', 'error')
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="auth-screen">
    <DotField side="left" />
    <DotField side="right" />

    <header class="auth-screen__brand">
      <a :href="config.public.landingUrl"><ProlivLogo :height="30" /></a>
    </header>

    <div class="auth-wrap">
      <h1>Ваш Network в удобном<br /><span class="accent-mark">личном кабинете</span></h1>
      <p class="auth-wrap__sub">Войдите по email или через Telegram</p>

      <div class="auth-card">
        <div class="auth-tabs">
          <span class="auth-tabs__pill" :class="{ 'is-right': mode === 'register' }" aria-hidden="true" />
          <button class="auth-tab" :class="{ 'is-active': mode === 'login' }" @click="mode = 'login'">Вход</button>
          <button class="auth-tab" :class="{ 'is-active': mode === 'register' }" @click="mode = 'register'">Регистрация</button>
        </div>

        <form class="stack" style="gap: 12px; text-align: left" @submit.prevent="submit">
          <div class="field">
            <span>Email</span>
            <input v-model="login" class="input" autocomplete="username" placeholder="name@example.com" />
          </div>
          <div class="field">
            <span>Пароль</span>
            <div class="input-eye">
              <input
                v-model="password"
                class="input"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
              />
              <button
                type="button"
                class="input-eye__btn"
                :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" :size="16" />
                <Eye v-else :size="16" />
              </button>
            </div>
          </div>

          <div class="auth-forgot">
            <button type="button" class="link" @click="push('Восстановление появится после подключения бэкенда')">
              Забыли пароль?
            </button>
          </div>

          <p class="auth-terms muted">
            При входе вы принимаете пользовательское соглашение
            <a class="link" :href="`${config.public.landingUrl}/terms`" target="_blank" rel="noopener">Посмотреть</a>
          </p>

          <button class="btn btn--primary btn--block" type="submit" :disabled="pending || !login || !password">
            <LoaderCircle v-if="pending" :size="16" class="spinner" />
            {{ mode === 'login' ? 'Войти' : 'Зарегистрироваться' }}
          </button>
        </form>

        <div class="auth-divider"><span>или</span></div>

        <div class="auth-card__widget">
          <button
            v-if="!isMiniApp"
            class="btn btn--ghost btn--block"
            type="button"
            :disabled="pending || oauthPending"
            @click="onTelegramOAuth"
          >
            <LoaderCircle v-if="oauthPending" :size="16" class="spinner" />
            <Send v-else :size="16" />
            Войти через Telegram
          </button>
          <TelegramLogin
            v-else-if="config.public.botUsername"
            :bot-username="config.public.botUsername"
            @auth="onTelegramAuth"
          />
        </div>
      </div>
    </div>
  </div>
</template>
