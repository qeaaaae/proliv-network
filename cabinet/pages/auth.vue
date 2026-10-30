<script setup lang="ts">
import { LoaderCircle, Send } from '@lucide/vue'

definePageMeta({ layout: false })
useHead({ title: 'Вход - Proliv Network' })

const config = useRuntimeConfig()
const route = useRoute()
const { push } = useToast()
const { ensure, loaded } = useAuth()
const referral = useReferral()

const pending = ref(false)

// next принимаем только локальный - иначе open redirect после логина
function safeNext(): string {
  const next = route.query.next
  return typeof next === 'string' && next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

async function goNext() {
  // сессия поставилась только что - сбрасываем кэш и подтягиваем /me до перехода
  loaded.value = false
  await ensure()
  referral.clear()
  return navigateTo(safeNext())
}

async function onTelegramAuth(user: Record<string, unknown>) {
  if (pending.value) return
  pending.value = true
  try {
    const referralCode = referral.code()
    await $fetch('/api/auth/telegram', {
      method: 'POST',
      body: { ...user, referralCode: referralCode || undefined },
    })
    await goNext()
  } catch {
    push('Не удалось войти. Попробуйте ещё раз', 'error')
  } finally {
    pending.value = false
  }
}

// Официальный Telegram OIDC code-flow: уходим на /api/auth/telegram/start,
// он редиректит на oauth.telegram.org; callback обменивает code на id_token
// и сам ставит сессию (всё серверно, в браузере секрета нет).
function onTelegramOAuth() {
  const ref = referral.code()
  const params = new URLSearchParams()
  if (ref) params.set('ref', ref)
  const next = safeNext()
  if (next !== '/') params.set('next', next)
  window.location.href = `/api/auth/telegram/start${params.size ? `?${params}` : ''}`
}

const isMiniApp = ref(false)

// Внутри Telegram Mini App входим автоматически по initData
onMounted(async () => {
  // callback OIDC вернул с ошибкой
  if (new URLSearchParams(window.location.search).get('oauth_error')) {
    push('Не удалось войти через Telegram. Попробуйте ещё раз', 'error')
    history.replaceState(null, '', '/auth')
  }
  const initData = (window as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData
  if (!initData || pending.value) return
  isMiniApp.value = true
  pending.value = true
  try {
    const referralCode = referral.code()
    await $fetch('/api/auth/telegram', {
      method: 'POST',
      body: { initData, referralCode: referralCode || undefined },
    })
    await goNext()
  } catch {
    // остаёмся на странице входа - можно войти через виджет
  } finally {
    pending.value = false
  }
})
</script>

<template>
  <div class="auth-screen">
    <BlueprintLayer />

    <header class="auth-screen__brand">
      <a :href="config.public.landingUrl"><ProlivLogo :height="30" /></a>
    </header>

    <div class="auth-wrap">
      <h1>Ваш Network в удобном<br /><span class="accent-mark">личном кабинете</span></h1>

      <div class="auth-card">
        <div class="auth-card__widget">
          <button
            v-if="!isMiniApp"
            class="btn btn--primary btn--block"
            type="button"
            :disabled="pending"
            @click="onTelegramOAuth"
          >
            <LoaderCircle v-if="pending" :size="16" class="spinner" />
            <Send v-else :size="16" />
            Войти через Telegram
          </button>
          <TelegramLogin
            v-else-if="config.public.botUsername"
            :bot-username="config.public.botUsername"
            @auth="onTelegramAuth"
          />
        </div>

        <p class="auth-terms muted" style="margin-top: 16px">
          При входе вы принимаете пользовательское соглашение
          <a class="link" :href="`${config.public.landingUrl}/terms`" target="_blank" rel="noopener">Посмотреть</a>
        </p>
      </div>
    </div>
  </div>
</template>
