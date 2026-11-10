import { createError, type H3Event } from 'h3'
import { ofetch } from 'ofetch'
import { setSession } from './session'
import { shopApiUrl, type ShopMe } from './backend'

export interface ShopAuthTokenResponse {
  ok?: boolean
  token?: string
  csrf_token?: string
  user_id?: number
  telegram_id?: number | null
}

// Коды ошибок upstream email-auth -> русские тексты для тостов.
const EMAIL_ERRORS: Record<string, string> = {
  invalid_email: 'Проверьте адрес почты',
  disposable_email: 'Этот почтовый сервис не поддерживается',
  invalid_code: 'Неверный код',
  expired_code: 'Код истёк - запросите новый',
  too_many_attempts: 'Слишком много попыток - запросите новый код',
  rate_limited: 'Слишком часто - попробуйте чуть позже',
  email_auth_not_configured: 'Вход по почте временно недоступен',
  email_send_failed: 'Не удалось отправить письмо - попробуйте позже',
  password_login_failed: 'Неверная почта или пароль',
  invalid_token: 'Ссылка для входа недействительна',
  expired_token: 'Ссылка для входа истекла - запросите новую',
  account_merge_required: 'Эта почта уже привязана к другому аккаунту',
  banned: 'Доступ к аккаунту ограничен',
  email_not_linked: 'К аккаунту не привязана почта',
  password_mismatch: 'Пароли не совпадают',
  email_change_requires_current_confirmation: 'Сначала подтвердите текущую почту',
  registration_invite_required: 'Регистрация доступна только по приглашению',
  account_merge_not_required: 'Этот Telegram уже привязан к текущему аккаунту',
  account_merge_telegram_conflict: 'К аккаунту уже привязан другой Telegram',
  verified_email_required: 'Сначала подтвердите почту аккаунта',
  telegram_disabled: 'Вход через Telegram временно недоступен',
  invalid_auth: 'Не удалось подтвердить Telegram - попробуйте ещё раз',
  link_failed: 'Не удалось привязать Telegram - попробуйте позже',
  account_merge_failed: 'Не удалось объединить аккаунты - попробуйте позже',
  account_merge_proof_expired: 'Сессия привязки истекла - начните заново',
}

export function emailAuthMessage(code: string | undefined, fallback: string): string {
  return (code && EMAIL_ERRORS[code]) || fallback
}

// Пробрасывает ошибку upstream/shopFetch как h3-ошибку с русским текстом.
// Работает и с сырым ofetch-ответом, и с createError из shopFetch
// (там upstream-payload лежит в err.data).
export function throwEmailAuthError(err: unknown, fallback = 'Ошибка входа по почте'): never {
  const e = err as {
    statusCode?: number
    data?: {
      error?: string
      detail?: string
      message?: string
      retry_after?: number
    }
  }
  const data = e?.data
  throw createError({
    statusCode: e?.statusCode ?? 502,
    statusMessage: emailAuthMessage(data?.error, data?.detail || data?.message || fallback),
    data: { error: data?.error, retryAfter: data?.retry_after },
  })
}

// Общий хвост всех email-логинов: upstream выдал token -> дотягиваем профиль
// и ставим cabinet-сессию. У email-only аккаунта telegram_id = null,
// тогда id сессии = внутренний user_id minishop.
export async function setSessionFromShopToken(
  event: H3Event,
  res: ShopAuthTokenResponse,
  fallbackName: string,
): Promise<void> {
  if (!res?.token) {
    throw createError({ statusCode: 502, statusMessage: 'Backend did not issue a token' })
  }
  const base = shopApiUrl(event)
  const me = await ofetch<ShopMe>(`${base}/api/me`, {
    headers: {
      Accept: 'application/json',
      'Accept-Encoding': 'identity',
      Authorization: `Bearer ${res.token}`,
    },
    timeout: 15000,
  }).catch(() => null)

  setSession(event, {
    id: Number(res.telegram_id ?? me?.user?.telegram_id ?? res.user_id ?? 0),
    name: me?.user?.first_name || me?.user?.username || me?.user?.email?.split('@')[0] || fallbackName,
    username: me?.user?.username ?? undefined,
    photoUrl: me?.user?.telegram_photo_url || undefined,
    apiToken: res.token,
    apiCsrf: res.csrf_token,
  })
}
