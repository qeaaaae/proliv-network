import { createHmac, randomBytes } from 'node:crypto'
import { getQuery, getRequestHost, getRequestProtocol, setCookie, sendRedirect } from 'h3'
import { ofetch } from 'ofetch'
import { shopApiUrl } from '../../../utils/backend'

// Telegram OIDC authorization code flow (официальный, с PKCE):
// генерим code_verifier/state, забираем backend-nonce, редиректим браузер
// на oauth.telegram.org/auth. Callback: /api/auth/telegram/callback.
const STATE_COOKIE = 'tg_oauth_state'
const STATE_TTL = 600 // 10 минут

function base64url(buf: Buffer): string {
  return buf.toString('base64url')
}

function signState(payload: string, secret: string): string {
  return createHmac('sha256', secret).update(payload).digest('base64url')
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  const backend = shopApiUrl(event)
  if (!backend || !config.telegramOauthClientSecret) {
    throw createError({ statusCode: 503, statusMessage: 'Telegram OAuth is not configured' })
  }

  // backend выдаёт подписанный nonce - minishop проверит его при обмене id_token
  const nonceRes = await ofetch<{ nonce?: string; client_id?: number | string }>(
    `${backend}/api/auth/telegram/nonce`,
    { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept-Encoding': 'identity' }, body: '{}', timeout: 15000 },
  )
  if (!nonceRes?.nonce || !nonceRes?.client_id) {
    throw createError({ statusCode: 502, statusMessage: 'Backend auth failed' })
  }

  const proto = getRequestProtocol(event)
  const host = getRequestHost(event)
  const redirectUri = `${proto}://${host}/api/auth/telegram/callback`

  const codeVerifier = base64url(randomBytes(32))
  const challenge = Buffer.from(
    await crypto.subtle.digest('SHA-256', new TextEncoder().encode(codeVerifier)),
  ).toString('base64url')
  const state = base64url(randomBytes(16))

  // Реферальный код из ?ref= проносим через подписанный state - в callback
  // уйдёт в /api/auth/token как referral_code (лендинг терял его раньше)
  const ref = String(getQuery(event).ref || '').slice(0, 64)

  const statePayload = base64url(Buffer.from(JSON.stringify({
    state,
    verifier: codeVerifier,
    nonce: nonceRes.nonce,
    ref: ref || undefined,
    exp: Date.now() + STATE_TTL * 1000,
  })))
  const sessionSecret = config.sessionSecret || config.botToken || 'dev-insecure-secret'
  setCookie(event, STATE_COOKIE, `${statePayload}.${signState(statePayload, sessionSecret)}`, {
    httpOnly: true,
    sameSite: 'lax',
    secure: proto === 'https',
    path: '/',
    maxAge: STATE_TTL,
  })

  const authUrl = new URL('https://oauth.telegram.org/auth')
  authUrl.searchParams.set('response_type', 'code')
  authUrl.searchParams.set('client_id', String(nonceRes.client_id))
  authUrl.searchParams.set('redirect_uri', redirectUri)
  authUrl.searchParams.set('scope', 'openid profile')
  authUrl.searchParams.set('state', state)
  authUrl.searchParams.set('nonce', nonceRes.nonce)
  authUrl.searchParams.set('code_challenge', challenge)
  authUrl.searchParams.set('code_challenge_method', 'S256')
  authUrl.searchParams.set('lang', 'ru')

  return sendRedirect(event, authUrl.toString(), 302)
})
