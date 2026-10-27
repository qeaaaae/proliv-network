import { createHmac, timingSafeEqual } from 'node:crypto'
import { deleteCookie, getCookie, getRequestProtocol, setCookie, type H3Event } from 'h3'

export interface CabinetUser {
  id: number
  name: string
  username?: string
  photoUrl?: string
  // Токены общего бэкенда (minishop WebApp API)
  apiToken?: string
  apiCsrf?: string
}

const COOKIE_NAME = 'proliv_session'
const MAX_AGE = 60 * 60 * 24 * 30

function secret(event: H3Event): string {
  const config = useRuntimeConfig(event)
  if (config.sessionSecret) return config.sessionSecret
  // dev-фолбэк: производный секрет от токена бота, чтобы не хранить отдельный ключ локально
  return createHmac('sha256', 'proliv-cabinet-session')
    .update(config.botToken || 'dev-insecure-secret')
    .digest('hex')
}

function sign(payload: string, event: H3Event): string {
  return createHmac('sha256', secret(event)).update(payload).digest('base64url')
}

export function setSession(event: H3Event, user: CabinetUser) {
  const payload = Buffer.from(JSON.stringify({ ...user, exp: Date.now() + MAX_AGE * 1000 })).toString(
    'base64url',
  )
  setCookie(event, COOKIE_NAME, `${payload}.${sign(payload, event)}`, {
    httpOnly: true,
    sameSite: 'lax',
    secure: getRequestProtocol(event) === 'https',
    path: '/',
    maxAge: MAX_AGE,
  })
}

export function getCabinetSession(event: H3Event): CabinetUser | null {
  const raw = getCookie(event, COOKIE_NAME)
  if (!raw) return null
  const dot = raw.lastIndexOf('.')
  if (dot < 0) return null
  const payload = raw.slice(0, dot)
  const given = Buffer.from(raw.slice(dot + 1))
  const expected = Buffer.from(sign(payload, event))
  if (given.length !== expected.length || !timingSafeEqual(given, expected)) return null
  try {
    const data = JSON.parse(Buffer.from(payload, 'base64url').toString())
    if (typeof data.id !== 'number' || typeof data.name !== 'string') return null
    if (!data.exp || data.exp < Date.now()) return null
    return {
      id: data.id,
      name: data.name,
      username: data.username,
      photoUrl: data.photoUrl,
      apiToken: data.apiToken,
      apiCsrf: data.apiCsrf,
    }
  } catch {
    return null
  }
}

export function clearCabinetSession(event: H3Event) {
  deleteCookie(event, COOKIE_NAME, { path: '/' })
}

export function requireUser(event: H3Event): CabinetUser {
  const user = getCabinetSession(event)
  if (!user) throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })
  return user
}
