<script setup lang="ts">
import { Eye, EyeOff, LoaderCircle, Mail, Send } from '@lucide/vue'

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

function errMessage(e: unknown, fallback: string): string {
  return (e as { data?: { statusMessage?: string } })?.data?.statusMessage || fallback
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

// ---------- Email-вход: одноразовый код из письма или пароль ----------
// Регистрации отдельно нет: кодом из письма можно войти и без аккаунта -
// бэкенд создаст его на первом verify. Поэтому код - основной режим,
// пароль задаётся потом в настройках.
const emailMode = ref<'code' | 'password'>('code')
const email = ref('')
const emailPassword = ref('')
const showPassword = ref(false)
const emailCode = ref('')
const codeSent = ref(false)
const emailPending = ref(false)
const resendIn = ref(0)
let resendTimer: ReturnType<typeof setInterval> | undefined

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email.value.trim()))

function startResendCooldown(seconds: number) {
  resendIn.value = seconds
  clearInterval(resendTimer)
  resendTimer = setInterval(() => {
    resendIn.value -= 1
    if (resendIn.value <= 0) clearInterval(resendTimer)
  }, 1000)
}

onBeforeUnmount(() => clearInterval(resendTimer))

async function requestEmailCode() {
  if (!emailValid.value || emailPending.value || resendIn.value > 0) return
  emailPending.value = true
  try {
    const referralCode = referral.code()
    await $fetch('/api/auth/email/request', {
      method: 'POST',
      body: { email: email.value.trim(), referralCode: referralCode || undefined },
    })
    codeSent.value = true
    startResendCooldown(60)
    push('Код отправлен - проверьте почту')
  } catch (e) {
    push(errMessage(e, 'Не удалось отправить код'), 'error')
  } finally {
    emailPending.value = false
  }
}

function resetEmailCode() {
  codeSent.value = false
  emailCode.value = ''
}

async function verifyEmailCode() {
  if (!emailCode.value.trim() || emailPending.value) return
  emailPending.value = true
  try {
    const referralCode = referral.code()
    await $fetch('/api/auth/email/verify', {
      method: 'POST',
      body: {
        email: email.value.trim(),
        code: emailCode.value.trim(),
        referralCode: referralCode || undefined,
      },
    })
    await goNext()
  } catch (e) {
    push(errMessage(e, 'Неверный код'), 'error')
  } finally {
    emailPending.value = false
  }
}

async function loginEmailPassword() {
  if (!emailValid.value || !emailPassword.value || emailPending.value) return
  emailPending.value = true
  try {
    await $fetch('/api/auth/email', {
      method: 'POST',
      body: { email: email.value.trim(), password: emailPassword.value },
    })
    await goNext()
  } catch (e) {
    push(errMessage(e, 'Неверная почта или пароль'), 'error')
  } finally {
    emailPending.value = false
  }
}

function submitEmail() {
  if (emailMode.value === 'password') return loginEmailPassword()
  return codeSent.value ? verifyEmailCode() : requestEmailCode()
}

const isMiniApp = ref(false)

// Внутри Telegram Mini App входим автоматически по initData
onMounted(async () => {
  // callback OIDC вернул с ошибкой
  if (new URLSearchParams(window.location.search).get('oauth_error')) {
    push('Не удалось войти через Telegram. Попробуйте ещё раз', 'error')
    history.replaceState(null, '', '/auth')
  }

  // Magic link из письма: /auth?login_token=... -> сразу обмениваем на сессию
  const loginToken = route.query.login_token
  if (typeof loginToken === 'string' && loginToken) {
    pending.value = true
    try {
      const referralCode = referral.code()
      await $fetch('/api/auth/email/magic', {
        method: 'POST',
        body: { token: loginToken, referralCode: referralCode || undefined },
      })
      await goNext()
      return
    } catch (e) {
      push(errMessage(e, 'Ссылка недействительна или истекла'), 'error')
      history.replaceState(null, '', '/auth')
    } finally {
      pending.value = false
    }
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
    // остаёмся на странице входа - можно войти через виджет или почту
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

        <div class="auth-divider"><span>или по почте</span></div>

        <div class="auth-tabs">
          <span class="auth-tabs__pill" :class="{ 'is-right': emailMode === 'password' }" aria-hidden="true" />
          <button
            class="auth-tab"
            type="button"
            :class="{ 'is-active': emailMode === 'code' }"
            @click="emailMode = 'code'"
          >Код из письма</button>
          <button
            class="auth-tab"
            type="button"
            :class="{ 'is-active': emailMode === 'password' }"
            @click="emailMode = 'password'"
          >Пароль</button>
        </div>

        <form class="stack" style="gap: 12px; text-align: left" @submit.prevent="submitEmail">
          <div class="field">
            <span>Email</span>
            <input
              v-model="email"
              class="input"
              type="email"
              autocomplete="email"
              placeholder="name@example.com"
              :disabled="emailMode === 'code' && codeSent"
            />
          </div>

          <template v-if="emailMode === 'code'">
            <div v-if="codeSent" class="field">
              <span>Код из письма</span>
              <input
                v-model="emailCode"
                class="input"
                inputmode="numeric"
                autocomplete="one-time-code"
                maxlength="6"
                placeholder="123456"
              />
            </div>

            <p v-if="!codeSent" class="muted" style="font-size: 12px; line-height: 1.45">
              Аккаунта ещё нет? Он создастся сам при первом входе -
              отдельная регистрация не нужна.
            </p>

            <button
              class="btn btn--primary btn--block"
              type="submit"
              :disabled="
                emailPending
                || !emailValid
                || (codeSent ? !emailCode.trim() : resendIn > 0)
              "
            >
              <LoaderCircle v-if="emailPending" :size="16" class="spinner" />
              <Mail v-else :size="16" />
              {{ codeSent ? 'Войти' : 'Получить код' }}
            </button>

            <div v-if="codeSent" class="auth-forgot" style="justify-content: space-between">
              <button type="button" class="link" :disabled="resendIn > 0" @click="requestEmailCode">
                Отправить код ещё раз{{ resendIn ? ` (${resendIn} c)` : '' }}
              </button>
              <button type="button" class="link" @click="resetEmailCode">Сменить почту</button>
            </div>
          </template>

          <template v-else>
            <div class="field">
              <span>Пароль</span>
              <div class="input-eye">
                <input
                  v-model="emailPassword"
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

            <p class="muted" style="font-size: 12px; line-height: 1.45">
              Пароля ещё нет? Войдите по коду из письма - пароль можно задать
              потом в настройках аккаунта.
            </p>

            <button
              class="btn btn--primary btn--block"
              type="submit"
              :disabled="emailPending || !emailValid || !emailPassword"
            >
              <LoaderCircle v-if="emailPending" :size="16" class="spinner" />
              <Mail v-else :size="16" />
              Войти по почте
            </button>
          </template>
        </form>

        <p class="auth-terms muted" style="margin-top: 16px">
          При входе вы принимаете пользовательское соглашение
          <a class="link" :href="`${config.public.landingUrl}/terms`" target="_blank" rel="noopener">Посмотреть</a>
        </p>
      </div>
    </div>
  </div>
</template>
