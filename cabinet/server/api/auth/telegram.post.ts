import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { setSession } from '../../utils/session'
import { verifyTelegramAuth, type TelegramAuthPayload } from '../../utils/telegram'
import { shopApiUrl } from '../../utils/backend'

interface ShopTokenResponse {
  ok?: boolean
  token?: string
  csrf_token?: string
  user_id?: number
  telegram_id?: number
}

// Обмен Telegram-авторизации на токен общего бэкенда (minishop WebApp API).
// Принимает либо initData из Mini App ({ initData }), либо поля Telegram Login Widget.
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  const body = await readBody<TelegramAuthPayload & {
    initData?: string
    idToken?: string
    id_token?: string
    nonce?: string
    referralCode?: string
    startParam?: string
  }>(event)

  const backend = shopApiUrl(event)

  // Telegram OIDC (oauth.telegram.org): попап вернул id_token, nonce выдала
  // наша BFF-ручка /api/auth/telegram/nonce. Бэкенд верифицирует по JWKS.
  const idToken = body?.idToken || body?.id_token
  if (idToken && body?.nonce) {
    if (!backend) {
      throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
    }
    const res = await exchangeToken(event, {
      id_token: idToken,
      nonce: body.nonce,
      referral_code: body.referralCode,
      start_param: body.startParam,
    })
    const claims = decodeIdToken(idToken)
    setSession(event, {
      id: Number(res.telegram_id ?? claims.id ?? res.user_id ?? 0),
      name: claims.name || 'User',
      username: claims.username,
      photoUrl: claims.photo_url,
      apiToken: res.token,
      apiCsrf: res.csrf_token,
    })
    return { ok: true }
  }

  // Mini App: initData уже подписан Telegram, бэкенд верифицирует его сам
  if (body?.initData) {
    if (!backend) {
      throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
    }
    const res = await exchangeToken(event, { init_data: body.initData, referral_code: body.referralCode, start_param: body.startParam })
    // user=%7B...%7D в initData - urlencoded JSON с профилем Telegram
    const tgUser = parseInitDataUser(body.initData)
    setSession(event, {
      id: Number(res.telegram_id ?? tgUser.id ?? res.user_id ?? 0),
      name: tgUser.name || 'User',
      username: tgUser.username,
      photoUrl: tgUser.photo_url,
      apiToken: res.token,
      apiCsrf: res.csrf_token,
    })
    return { ok: true }
  }

  // Telegram Login Widget (браузер): подпись проверяем сами, затем передаём auth_data бэкенду
  if (!config.botToken) {
    throw createError({ statusCode: 503, statusMessage: 'Telegram auth is not configured' })
  }
  if (!body?.id || !verifyTelegramAuth(body, config.botToken)) {
    throw createError({ statusCode: 401, statusMessage: 'Invalid Telegram signature' })
  }

  const name = [body.first_name, body.last_name].filter(Boolean).join(' ') || 'User'

  if (!backend) {
    setSession(event, {
      id: Number(body.id),
      name,
      username: body.username,
      photoUrl: body.photo_url,
    })
    return { ok: true, mode: 'local' }
  }

  const res = await exchangeToken(event, {
    auth_data: {
      id: body.id,
      first_name: body.first_name,
      last_name: body.last_name,
      username: body.username,
      photo_url: body.photo_url,
      auth_date: body.auth_date,
      hash: body.hash,
    },
    referral_code: body.referralCode,
    start_param: body.startParam,
  })
  setSession(event, {
    id: Number(res.telegram_id ?? body.id),
    name,
    username: body.username,
    photoUrl: body.photo_url,
    apiToken: res.token,
    apiCsrf: res.csrf_token,
  })
  return { ok: true }
})

// id_token - JWT от oauth.telegram.org; подпись проверяет бэкенд (JWKS),
// нам нужны только отображаемые поля профиля (name/username/picture).
function decodeIdToken(token: string): { id?: number; name?: string; username?: string; photo_url?: string } {
  try {
    const part = token.split('.')[1]
    if (!part) return {}
    const payload = JSON.parse(
      Buffer.from(part.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8'),
    ) as { sub?: string | number; name?: string; preferred_username?: string; picture?: string; id?: number }
    const sub = typeof payload.sub === 'string' ? Number(payload.sub) : payload.sub
    return {
      id: payload.id ?? (Number.isFinite(sub) ? sub : undefined),
      name: payload.name,
      username: payload.preferred_username,
      photo_url: payload.picture,
    }
  } catch {
    return {}
  }
}

function parseInitDataUser(initData: string): { id?: number; name?: string; username?: string; photo_url?: string } {
  try {
    const raw = new URLSearchParams(initData).get('user')
    if (!raw) return {}
    const u = JSON.parse(raw) as {
      id?: number
      first_name?: string
      last_name?: string
      username?: string
      photo_url?: string
    }
    return {
      id: u.id,
      name: [u.first_name, u.last_name].filter(Boolean).join(' ') || undefined,
      username: u.username,
      photo_url: u.photo_url,
    }
  } catch {
    return {}
  }
}

async function exchangeToken(
  event: Parameters<typeof shopApiUrl>[0],
  payload: Record<string, unknown>,
): Promise<ShopTokenResponse> {
  const base = shopApiUrl(event)!
  const url: string = `${base}/api/auth/token`
  let res: ShopTokenResponse
  try {
    res = await ofetch<ShopTokenResponse>(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept-Encoding': 'identity' },
      body: JSON.stringify(payload),
      timeout: 15000,
    })
  } catch (err) {
    const e = err as { statusCode?: number; data?: { detail?: string } }
    throw createError({
      statusCode: e.statusCode ?? 502,
      statusMessage: e.data?.detail || 'Backend auth failed',
    })
  }
  if (!res?.token) {
    throw createError({ statusCode: 502, statusMessage: 'Backend did not issue a token' })
  }
  return res
}
