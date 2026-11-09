<script setup lang="ts">
import {
  Bell,
  Check,
  Eye,
  EyeOff,
  Gift,
  KeyRound,
  LoaderCircle,
  LogOut,
  Mail,
  Send,
} from '@lucide/vue'

const { push } = useToast()
const { user, logout, ensure, loaded } = useAuth()
const route = useRoute()

interface Account {
  email: string | null
  hasPassword: boolean
  telegram: { username?: string | null; id: number | null }
  twoFa: boolean
}

interface Settings {
  settings: { notifySystem: boolean; notifyNews: boolean }
}

const { data, status, refresh } = useFetch<Account>('/api/account', { lazy: true })
const { data: settingsData } = useFetch<Settings>('/api/settings', { lazy: true })

const notifications = [
  {
    key: 'notifySystem' as const,
    label: 'Подписка и безопасность',
    hint: 'Окончание подписки, входы в аккаунт, смена ссылки',
  },
  { key: 'notifyNews' as const, label: 'Новости и акции', hint: 'Новые локации, тарифы и бонусы' },
]

async function toggleNotify(
  key: (typeof notifications)[number]['key'],
  value: boolean,
  ev: Event,
) {
  try {
    await $fetch('/api/settings', { method: 'POST', body: { [key]: value } })
    push('Настройка сохранена')
  } catch {
    // откатываем чекбокс - иначе визуально "включено", а в БД "выключено"
    ;(ev.target as HTMLInputElement).checked = !value
    push('Не удалось сохранить', 'error')
  }
}

const promo = ref('')
const promoPending = ref(false)

// Промо-диплинк из Mini App (?startapp=promo_<code>): код ждёт в поле,
// активируем его только по кнопке.
onMounted(async () => {
  const value = Array.isArray(route.query.promo) ? route.query.promo[0] : route.query.promo
  if (typeof value === 'string' && /^[A-Za-z0-9_-]{1,59}$/.test(value)) {
    promo.value = value
    push('Промокод подставлен - нажмите «Применить»')
  }

  // Возврат из OIDC-link flow: ?tg=linked | merge | error&e=<code>
  const tg = route.query.tg
  if (tg === 'linked') {
    push('Telegram привязан')
    loaded.value = false
    await ensure()
    await refresh()
  } else if (tg === 'merge') {
    await openMerge()
  } else if (tg === 'error') {
    const code = String(route.query.e || '')
    push(TG_LINK_ERRORS[code] || 'Не удалось привязать Telegram', 'error')
  }
  if (tg) history.replaceState(null, '', route.path)
})

async function applyPromo() {
  if (!promo.value.trim() || promoPending.value) return
  promoPending.value = true
  try {
    const res = await $fetch<{
      message: string
      requiresCheckout?: boolean
      code?: string
      discountPercent?: number | null
    }>('/api/promocode', {
      method: 'POST',
      body: { code: promo.value },
    })
    if (res.requiresCheckout && res.code) {
      // Код-скидка: применяется на оплате - ведём на покупки с кодом в чекауте
      push(res.message || 'Промокод применится при оплате')
      return navigateTo({
        path: '/purchases',
        query: {
          promo: res.code,
          ...(res.discountPercent ? { pd: String(res.discountPercent) } : {}),
        },
      })
    }
    push(res.message)
    promo.value = ''
  } catch (e) {
    push((e as { data?: { statusMessage?: string } }).data?.statusMessage ?? 'Не удалось применить', 'error')
  } finally {
    promoPending.value = false
  }
}

// ---------- Привязка Telegram ----------
// OIDC-link flow: уходим на /api/auth/telegram/start?purpose=link, callback
// линкует TG к текущему аккаунту. Если TG занят другим аккаунтом - merge:
// подтверждение кодом с почты этого аккаунта (merge-куки tg_merge, 10 мин).
const tgPending = ref(false)
const mergeOpen = ref(false)
const mergeInfo = ref<{ id: number | null; username: string | null; firstName: string | null } | null>(null)
const mergeCode = ref('')
const mergeCodeSent = ref(false)
const mergePending = ref(false)

const TG_LINK_ERRORS: Record<string, string> = {
  account_merge_telegram_conflict: 'К аккаунту уже привязан другой Telegram',
  invalid_auth: 'Не удалось подтвердить Telegram - попробуйте ещё раз',
  banned: 'Доступ к аккаунту ограничен',
  rate_limited: 'Слишком часто - попробуйте чуть позже',
  link_failed: 'Не удалось привязать Telegram - попробуйте позже',
}

function linkTelegram() {
  if (tgPending.value) return
  tgPending.value = true
  window.location.href = '/api/auth/telegram/start?purpose=link&next=/account'
}

async function openMerge() {
  mergeOpen.value = true
  try {
    const st = await $fetch<{
      ok?: boolean
      telegram?: { id: number | null; username: string | null; firstName: string | null }
    }>('/api/account/telegram/merge/status')
    if (!st?.ok) {
      mergeOpen.value = false
      push('Сессия привязки истекла - начните привязку заново', 'error')
      return
    }
    mergeInfo.value = st.telegram ?? null
  } catch {
    // статус только для отображения @username - без него блок тоже рабочий
  }
}

async function requestMergeCode() {
  if (mergePending.value) return
  mergePending.value = true
  try {
    await $fetch('/api/account/telegram/merge/request', { method: 'POST' })
    mergeCodeSent.value = true
    push(`Код отправлен на ${data.value?.email || 'почту'}`)
  } catch (e) {
    push(accountErr(e, 'Не удалось отправить код'), 'error')
  } finally {
    mergePending.value = false
  }
}

async function confirmMerge() {
  if (mergePending.value || !mergeCode.value.trim()) return
  mergePending.value = true
  try {
    await $fetch('/api/account/telegram/merge/confirm', {
      method: 'POST',
      body: { code: mergeCode.value.trim() },
    })
    push('Аккаунты объединены - Telegram привязан')
    mergeOpen.value = false
    mergeCode.value = ''
    mergeCodeSent.value = false
    loaded.value = false
    await ensure()
    await refresh()
  } catch (e) {
    push(accountErr(e, 'Неверный код'), 'error')
  } finally {
    mergePending.value = false
  }
}

function cancelMerge() {
  mergeOpen.value = false
  mergeCode.value = ''
  mergeCodeSent.value = false
}

// ---------- Почта и пароль ----------
// Привязка email и установка пароля подтверждаются кодом из письма
// (SMTP в minishop, Resend). Пароль - минимум 8 символов.
function accountErr(e: unknown, fallback: string): string {
  return (e as { data?: { statusMessage?: string } })?.data?.statusMessage || fallback
}

const linkEmail = ref('')
const linkCode = ref('')
const linkCodeSent = ref(false)
const linkPending = ref(false)

const pwCode = ref('')
const pw1 = ref('')
const pw2 = ref('')
const pwShow = ref(false)
const pwPending = ref(false)
const pwFormOpen = ref(false)

const linkEmailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(linkEmail.value.trim()))

async function requestLinkCode() {
  if (!linkEmailValid.value || linkPending.value) return
  linkPending.value = true
  try {
    await $fetch('/api/account/email/request', {
      method: 'POST',
      body: { email: linkEmail.value.trim() },
    })
    linkCodeSent.value = true
    push('Код отправлен - проверьте почту')
  } catch (e) {
    push(accountErr(e, 'Не удалось отправить код'), 'error')
  } finally {
    linkPending.value = false
  }
}

async function verifyLinkCode() {
  if (!linkCode.value.trim() || linkPending.value) return
  linkPending.value = true
  try {
    await $fetch('/api/account/email/verify', {
      method: 'POST',
      body: { email: linkEmail.value.trim(), code: linkCode.value.trim() },
    })
    push('Почта привязана')
    linkCodeSent.value = false
    linkCode.value = ''
    await refresh()
  } catch (e) {
    push(accountErr(e, 'Неверный код'), 'error')
  } finally {
    linkPending.value = false
  }
}

async function requestPasswordCode() {
  if (pwPending.value) return
  pwPending.value = true
  try {
    await $fetch('/api/account/password/request', { method: 'POST' })
    pwFormOpen.value = true
    push(`Код отправлен на ${data.value?.email || 'почту'}`)
  } catch (e) {
    push(accountErr(e, 'Не удалось отправить код'), 'error')
  } finally {
    pwPending.value = false
  }
}

async function confirmPassword() {
  if (pwPending.value || pw1.value.length < 8 || pw1.value !== pw2.value || !pwCode.value.trim()) return
  pwPending.value = true
  try {
    await $fetch('/api/account/password/confirm', {
      method: 'POST',
      body: { password: pw1.value, passwordConfirm: pw2.value, code: pwCode.value.trim() },
    })
    push(data.value?.hasPassword ? 'Пароль обновлён' : 'Пароль задан')
    pwFormOpen.value = false
    pwCode.value = ''
    pw1.value = ''
    pw2.value = ''
    await refresh()
  } catch (e) {
    push(accountErr(e, 'Не удалось сохранить пароль'), 'error')
  } finally {
    pwPending.value = false
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

    <section v-else-if="status === 'error'" class="panel">
      <FetchError @retry="refresh" />
    </section>

    <template v-else>
    <!-- Данные аккаунта -->
    <section class="panel">
      <div class="row-line" style="border-top: 0">
        <span class="row-line__icon"><Send :size="15" /></span>
        <span class="row-line__body">
          <span class="row-line__label">Telegram</span>
          <span class="row-line__hint">
            {{ data?.telegram.id
              ? `${data.telegram.username ? `@${data.telegram.username}` : 'Привязан'} · ${data.telegram.id}`
              : 'Не привязан' }}
          </span>
        </span>
        <span v-if="data?.telegram.id" class="badge badge--green"><Check :size="11" />Подключён</span>
        <button
          v-else
          class="btn btn--ghost"
          type="button"
          :disabled="tgPending"
          @click="linkTelegram"
        >
          <LoaderCircle v-if="tgPending" :size="15" class="spinner" />
          Привязать
        </button>
      </div>

      <div
        v-if="mergeOpen"
        class="panel--pad"
        style="border-top: 1px dashed var(--line-dash); display: grid; gap: 10px"
      >
        <p class="muted" style="font-size: 13px; margin: 0">
          Telegram{{ mergeInfo?.username ? ` @${mergeInfo.username}` : '' }} уже привязан
          к другому аккаунту. Можно объединить аккаунты - подписка, баланс и устройства
          сохранятся в текущем. Подтверждение - кодом на {{ data?.email || 'почту аккаунта' }}.
        </p>
        <input
          v-if="mergeCodeSent"
          v-model="mergeCode"
          class="input"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
          placeholder="Код из письма"
        />
        <div style="display: flex; gap: 10px; flex-wrap: wrap">
          <button
            class="btn btn--primary"
            type="button"
            :disabled="mergePending || (mergeCodeSent && !mergeCode.trim())"
            @click="mergeCodeSent ? confirmMerge() : requestMergeCode()"
          >
            <LoaderCircle v-if="mergePending" :size="15" class="spinner" />
            {{ mergeCodeSent ? 'Объединить аккаунты' : 'Отправить код' }}
          </button>
          <button class="btn btn--ghost" type="button" :disabled="mergePending" @click="cancelMerge">
            Отмена
          </button>
        </div>
        <button
          v-if="mergeCodeSent"
          type="button"
          class="link"
          :disabled="mergePending"
          @click="requestMergeCode"
        >
          Отправить код ещё раз
        </button>
      </div>
    </section>

    <!-- Почта и пароль: вход без Telegram -->
    <section class="panel">
      <div class="panel__title">
        <Mail :size="17" />
        Почта и пароль
        <small>вход в кабинет без Telegram</small>
      </div>

      <template v-if="data?.email">
        <div class="row-line" style="border-top: 0">
          <span class="row-line__icon"><Mail :size="15" /></span>
          <span class="row-line__body">
            <span class="row-line__label">{{ data.email }}</span>
            <span class="row-line__hint">
              {{ data.hasPassword ? 'Пароль задан - можно входить по почте' : 'Пароль не задан' }}
            </span>
          </span>
          <span class="badge badge--green"><Check :size="11" />Привязана</span>
        </div>
        <div class="panel--pad" style="display: grid; gap: 10px">
          <button v-if="!pwFormOpen" class="btn btn--ghost" :disabled="pwPending" @click="requestPasswordCode">
            <LoaderCircle v-if="pwPending" :size="15" class="spinner" />
            <KeyRound v-else :size="15" />
            {{ data.hasPassword ? 'Сменить пароль' : 'Задать пароль' }}
          </button>
          <template v-else>
            <p class="muted" style="font-size: 13px; margin: 0">Код отправлен на {{ data.email }}</p>
            <input
              v-model="pwCode"
              class="input"
              inputmode="numeric"
              autocomplete="one-time-code"
              maxlength="6"
              placeholder="Код из письма"
            />
            <div class="input-eye">
              <input
                v-model="pw1"
                class="input"
                :type="pwShow ? 'text' : 'password'"
                autocomplete="new-password"
                placeholder="Новый пароль (минимум 8 символов)"
              />
              <button
                type="button"
                class="input-eye__btn"
                :aria-label="pwShow ? 'Скрыть пароль' : 'Показать пароль'"
                @click="pwShow = !pwShow"
              >
                <EyeOff v-if="pwShow" :size="16" />
                <Eye v-else :size="16" />
              </button>
            </div>
            <input
              v-model="pw2"
              class="input"
              type="password"
              autocomplete="new-password"
              placeholder="Повторите пароль"
            />
            <div style="display: flex; gap: 10px">
              <button
                class="btn btn--primary"
                :disabled="pwPending || pw1.length < 8 || pw1 !== pw2 || !pwCode.trim()"
                @click="confirmPassword"
              >
                <LoaderCircle v-if="pwPending" :size="15" class="spinner" />
                Сохранить
              </button>
              <button class="btn btn--ghost" :disabled="pwPending" @click="pwFormOpen = false">
                Отмена
              </button>
            </div>
            <button type="button" class="link" :disabled="pwPending" @click="requestPasswordCode">
              Отправить код ещё раз
            </button>
          </template>
        </div>
      </template>

      <div v-else class="panel--pad" style="display: grid; gap: 10px">
        <p class="muted" style="font-size: 13px; margin: 0">
          Привяжите почту - сможете заходить в кабинет даже когда Telegram недоступен.
        </p>
        <input
          v-model="linkEmail"
          class="input"
          type="email"
          autocomplete="email"
          placeholder="name@example.com"
          :disabled="linkCodeSent"
        />
        <input
          v-if="linkCodeSent"
          v-model="linkCode"
          class="input"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
          placeholder="Код из письма"
        />
        <button
          class="btn btn--primary"
          :disabled="linkPending || !linkEmailValid || (linkCodeSent && !linkCode.trim())"
          @click="linkCodeSent ? verifyLinkCode() : requestLinkCode()"
        >
          <LoaderCircle v-if="linkPending" :size="15" class="spinner" />
          {{ linkCodeSent ? 'Подтвердить' : 'Привязать почту' }}
        </button>
        <div v-if="linkCodeSent" style="display: flex; gap: 16px">
          <button type="button" class="link" :disabled="linkPending" @click="requestLinkCode">
            Отправить код ещё раз
          </button>
          <button type="button" class="link" @click="linkCodeSent = false; linkCode = ''">
            Сменить почту
          </button>
        </div>
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
            @change="toggleNotify(n.key, ($event.target as HTMLInputElement).checked, $event)"
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
