import { createHmac, timingSafeEqual } from 'node:crypto'
import { deleteCookie, getCookie, getRequestProtocol, setCookie, type H3Event } from 'h3'

// Доказательство владения Telegram между шагами merge: OIDC-link вернул
// 409 account_merge_required -> сюда кладём id_token+nonce, confirm шлёт их
// вместе с кодом из письма в upstream /api/account/telegram/merge/confirm.
// TTL 10 минут - как у upstream rw_tg_merge_proof.
const MERGE_COOKIE = 'tg_merge'
const MAX_AGE = 600

export interface TgMergeProof {
  idt: string // Telegram OIDC id_token
  nonce: string
  tgId?: number
  tgUsername?: string
  tgName?: string
  exp: number
}

function secret(event: H3Event): string {
  const config = useRuntimeConfig(event)
  return config.sessionSecret || config.botToken || 'dev-insecure-secret'
}

function sign(payload: string, event: H3Event): string {
  return createHmac('sha256', secret(event)).update(payload).digest('base64url')
}

export function setTgMergeProof(event: H3Event, proof: Omit<TgMergeProof, 'exp'>) {
  const payload = Buffer.from(
    JSON.stringify({ ...proof, exp: Date.now() + MAX_AGE * 1000 }),
  ).toString('base64url')
  setCookie(event, MERGE_COOKIE, `${payload}.${sign(payload, event)}`, {
    httpOnly: true,
    sameSite: 'lax',
    secure: getRequestProtocol(event) === 'https',
    path: '/',
    maxAge: MAX_AGE,
  })
}

export function readTgMergeProof(event: H3Event): TgMergeProof | null {
  const raw = getCookie(event, MERGE_COOKIE)
  if (!raw) return null
  const dot = raw.lastIndexOf('.')
  if (dot < 0) return null
  const payload = raw.slice(0, dot)
  const given = Buffer.from(raw.slice(dot + 1))
  const expected = Buffer.from(sign(payload, event))
  if (given.length !== expected.length || !timingSafeEqual(given, expected)) return null
  try {
    const data = JSON.parse(Buffer.from(payload, 'base64url').toString()) as TgMergeProof
    if (!data.idt || !data.nonce || !data.exp || data.exp < Date.now()) return null
    return data
  } catch {
    return null
  }
}

export function clearTgMergeProof(event: H3Event) {
  deleteCookie(event, MERGE_COOKIE, { path: '/' })
}
