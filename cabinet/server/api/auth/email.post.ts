import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { setSession } from '../../utils/session'
import { shopApiUrl, type ShopMe } from '../../utils/backend'

interface ShopTokenResponse {
  ok?: boolean
  token?: string
  csrf_token?: string
  user_id?: number
  telegram_id?: number
}

// Вход по email+паролю: upstream POST /api/auth/email/password выдаёт
// Bearer-токен, после чего дотягиваем профиль из /api/me для сессии.
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  // Вход в проде - только через Telegram. Email-логин нужен локальному
  // стенду - открываем его тем же флагом, что и /api/auth/dev.
  if (String(config.public.devAuth) !== '1' && !import.meta.dev) {
    throw createError({ statusCode: 404, statusMessage: 'Not found' })
  }
  const base = shopApiUrl(event)
  if (!base) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ email?: string; password?: string }>(event)
  const email = (body?.email || '').trim()
  const password = body?.password || ''
  if (!email || !password) {
    throw createError({ statusCode: 400, statusMessage: 'Введите email и пароль' })
  }

  let res: ShopTokenResponse
  try {
    res = await ofetch<ShopTokenResponse>(`${base}/api/auth/email/password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'Accept-Encoding': 'identity',
      },
      body: JSON.stringify({ email, password }),
      timeout: 15000,
    })
  } catch (err) {
    const e = err as { statusCode?: number; data?: { detail?: string; message?: string } }
    throw createError({
      statusCode: e.statusCode ?? 502,
      statusMessage: e.data?.detail || e.data?.message || 'Неверный email или пароль',
    })
  }
  if (!res?.token) {
    throw createError({ statusCode: 502, statusMessage: 'Backend did not issue a token' })
  }

  // Профиль для сессии - сразу по новому токену
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
    name: me?.user?.first_name || email.split('@')[0] || 'User',
    username: me?.user?.username ?? undefined,
    photoUrl: me?.user?.telegram_photo_url || undefined,
    apiToken: res.token,
    apiCsrf: res.csrf_token,
  })
  return { ok: true }
})
