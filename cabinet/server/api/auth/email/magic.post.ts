import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { shopApiUrl } from '../../../utils/backend'
import {
  setSessionFromShopToken,
  throwEmailAuthError,
  type ShopAuthTokenResponse,
} from '../../../utils/emailAuth'

// Magic link из письма (upstream POST /api/auth/email/magic). Ссылку
// ?login_token=... ловит страница /auth и приходит сюда за сессией.
export default defineEventHandler(async (event) => {
  const base = shopApiUrl(event)
  if (!base) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{
    token?: string
    referralCode?: string
    startParam?: string
  }>(event)
  const token = (body?.token || '').trim()
  if (!token) {
    throw createError({ statusCode: 400, statusMessage: 'Недействительная ссылка' })
  }

  let res: ShopAuthTokenResponse
  try {
    res = await ofetch<ShopAuthTokenResponse>(`${base}/api/auth/email/magic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        'Accept-Encoding': 'identity',
      },
      body: JSON.stringify({
        token,
        referral_code: body?.referralCode || undefined,
        start_param: body?.startParam || undefined,
      }),
      timeout: 15000,
    })
  } catch (err) {
    throwEmailAuthError(err, 'Ссылка недействительна или истекла')
  }

  await setSessionFromShopToken(event, res!, 'User')
  return { ok: true }
})
