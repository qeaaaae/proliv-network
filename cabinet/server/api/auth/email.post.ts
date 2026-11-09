import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { shopApiUrl } from '../../utils/backend'
import {
  setSessionFromShopToken,
  throwEmailAuthError,
  type ShopAuthTokenResponse,
} from '../../utils/emailAuth'

// Вход по email+паролю: upstream POST /api/auth/email/password выдаёт
// Bearer-токен, после чего дотягиваем профиль и ставим сессию.
export default defineEventHandler(async (event) => {
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

  let res: ShopAuthTokenResponse
  try {
    res = await ofetch<ShopAuthTokenResponse>(`${base}/api/auth/email/password`, {
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
    throwEmailAuthError(err, 'Неверная почта или пароль')
  }

  await setSessionFromShopToken(event, res!, email.split('@')[0] || 'User')
  return { ok: true }
})
