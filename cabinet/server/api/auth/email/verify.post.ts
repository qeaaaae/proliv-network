import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { shopApiUrl } from '../../../utils/backend'
import {
  setSessionFromShopToken,
  throwEmailAuthError,
  type ShopAuthTokenResponse,
} from '../../../utils/emailAuth'

// Проверка кода из письма (upstream POST /api/auth/email/verify). Новому
// email пользователю создаёт аккаунт, дальше - обычная сессия minishop.
export default defineEventHandler(async (event) => {
  const base = shopApiUrl(event)
  if (!base) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{
    email?: string
    code?: string
    referralCode?: string
    startParam?: string
  }>(event)
  const email = (body?.email || '').trim()
  const code = (body?.code || '').trim()
  if (!email || !code) {
    throw createError({ statusCode: 400, statusMessage: 'Введите email и код' })
  }

  let res: ShopAuthTokenResponse
  try {
    res = await ofetch<ShopAuthTokenResponse>(`${base}/api/auth/email/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'Accept-Encoding': 'identity',
      },
      body: JSON.stringify({
        email,
        code,
        referral_code: body?.referralCode || undefined,
        start_param: body?.startParam || undefined,
      }),
      timeout: 15000,
    })
  } catch (err) {
    throwEmailAuthError(err, 'Неверный код')
  }

  await setSessionFromShopToken(event, res!, email.split('@')[0] || 'User')
  return { ok: true }
})
