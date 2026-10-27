import { createHmac, timingSafeEqual } from 'node:crypto'
import { deleteCookie, getCookie, getQuery, sendRedirect } from 'h3'
import { ofetch } from 'ofetch'
import { setSession } from '../../../utils/session'
import { shopApiUrl } from '../../../utils/backend'

// Callback Telegram OIDC: Telegram прислал ?code&state, меняем code на
// id_token (Basic client_id:client_secret, PKCE verifier из куки), затем
// id_token+nonce -> /api/auth/token бэкенда -> сессия -> редирект в кабинет.
const STATE_COOKIE = 'tg_oauth_state'

interface StatePayload {
  state: string
  verifier: string
  nonce: string
  exp: number
}

function readState(event: Parameters<typeof getCookie>[0], secret: string): StatePayload | null {
  const raw = getCookie(event, STATE_COOKIE)
  if (!raw) return null
  const dot = raw.lastIndexOf('.')
  if (dot < 0) return null
  const payload = raw.slice(0, dot)
  const given = Buffer.from(raw.slice(dot + 1))
  const expected = Buffer.from(
    createHmac('sha256', secret).update(payload).digest('base64url'),
  )
  if (given.length !== expected.length || !timingSafeEqual(given, expected)) return null
  try {
    const data = JSON.parse(Buffer.from(payload, 'base64url').toString()) as StatePayload
    if (!data.state || !data.verifier || !data.nonce || !data.exp) return null
    if (data.exp < Date.now()) return null
    return data
  } catch {
    return null
  }
}

function decodeIdTokenSub(token: string): { id?: number; name?: string; username?: string; photo_url?: string } {
  try {
    const part = token.split('.')[1]
    if (!part) return {}
    const p = JSON.parse(Buffer.from(part, 'base64url').toString('utf8')) as Record<string, unknown>
    const sub = typeof p.sub === 'string' ? Number(p.sub) : (p.sub as number | undefined)
    return {
      id: (p.id as number | undefined) ?? (Number.isFinite(sub) ? (sub as number) : undefined),
      name: p.name as string | undefined,
      username: p.preferred_username as string | undefined,
      photo_url: p.picture as string | undefined,
    }
  } catch {
    return {}
  }
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  const backend = shopApiUrl(event)
  const secret = config.sessionSecret || config.botToken || 'dev-insecure-secret'
  const fail = (s: string) => {
    console.error('[tg-oauth] callback failed:', s)
    return sendRedirect(event, `/auth?oauth_error=${s}`, 302)
  }

  deleteCookie(event, STATE_COOKIE, { path: '/' })
  const saved = readState(event, secret)
  const q = getQuery(event)
  const error = String(q.error || '')
  if (error) return fail('cancelled')
  const code = String(q.code || '')
  const state = String(q.state || '')
  if (!code || !saved || state !== saved.state) {
    console.error('[tg-oauth] state check:', { hasCode: !!code, hasSaved: !!saved, match: state === saved?.state })
    return fail('invalid_state')
  }
  if (!backend || !config.telegramOauthClientSecret) return fail('not_configured')

  const proto = getRequestProtocol(event)
  const host = getRequestHost(event)
  const redirectUri = `${proto}://${host}/api/auth/telegram/callback`

  // client_id у Telegram OIDC = числовой id бота - первая часть BOT_TOKEN до ':'
  const effectiveClientId = (config.botToken || '').split(':')[0]
  if (!effectiveClientId) return fail('not_configured')

  const credentials = Buffer.from(`${effectiveClientId}:${config.telegramOauthClientSecret}`).toString('base64')
  let idToken = ''
  try {
    const tokenRes = await ofetch<{ id_token?: string }>('https://oauth.telegram.org/token', {
      method: 'POST',
      headers: {
        Authorization: `Basic ${credentials}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code,
        redirect_uri: redirectUri,
        client_id: effectiveClientId,
        code_verifier: saved.verifier,
      }).toString(),
      timeout: 15000,
    })
    idToken = String(tokenRes?.id_token || '')
    if (!idToken) console.error('[tg-oauth] token response without id_token:', JSON.stringify(tokenRes))
  } catch (err) {
    const e = err as { statusCode?: number; data?: unknown; message?: string }
    console.error('[tg-oauth] token exchange failed:', e.statusCode, JSON.stringify(e.data), e.message)
    return fail('exchange_failed')
  }
  if (!idToken) return fail('exchange_failed')

  let shopRes: { token?: string; csrf_token?: string; telegram_id?: number; user_id?: number }
  try {
    shopRes = await ofetch(`${backend}/api/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept-Encoding': 'identity' },
      body: JSON.stringify({ id_token: idToken, nonce: saved.nonce }),
      timeout: 15000,
    })
  } catch (err) {
    const e = err as { statusCode?: number; data?: unknown }
    console.error('[tg-oauth] backend token failed:', e.statusCode, JSON.stringify(e.data))
    return fail('backend_failed')
  }
  if (!shopRes?.token) return fail('backend_failed')

  const claims = decodeIdTokenSub(idToken)
  setSession(event, {
    id: Number(shopRes.telegram_id ?? claims.id ?? shopRes.user_id ?? 0),
    name: claims.name || 'User',
    username: claims.username,
    photoUrl: claims.photo_url,
    apiToken: shopRes.token,
    apiCsrf: shopRes.csrf_token,
  })
  return sendRedirect(event, '/', 302)
})
