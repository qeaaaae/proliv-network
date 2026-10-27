import { createError, getRequestHeader, setResponseHeaders, setResponseStatus } from 'h3'
import { ofetch } from 'ofetch'
import { requireUser } from '../../utils/session'
import { shopApiUrl } from '../../utils/backend'

// Аватар аккаунта: upstream /api/me отдаёт telegram_photo_url относительным
// путём (/api/account/avatar[?v=...]) - проксируем его под тем же путём на
// нашем домене, чтобы <img> работал без прямого доступа к бэкенду.
// GET /api/account/avatar -> image/jpeg|png|webp, ETag/304 поддерживаются.
export default defineEventHandler(async (event) => {
  const session = requireUser(event)
  const base = shopApiUrl(event)
  if (!base || !session.apiToken) {
    throw createError({ statusCode: 404, statusMessage: 'No avatar' })
  }

  const headers: Record<string, string> = {
    Accept: 'image/*,*/*;q=0.8',
    'Accept-Encoding': 'identity',
    Authorization: `Bearer ${session.apiToken}`,
  }
  const inm = getRequestHeader(event, 'if-none-match')
  if (inm) headers['If-None-Match'] = inm

  // upstream использует ?v=<version> для cache-busting - проксируем как есть
  const qs = event.path.includes('?') ? event.path.slice(event.path.indexOf('?')) : ''
  let res
  try {
    res = await ofetch.raw(`${base}/api/account/avatar${qs}`, {
      method: 'GET',
      headers,
      responseType: 'arrayBuffer',
      ignoreResponseError: true,
      timeout: 15000,
    })
  } catch {
    throw createError({ statusCode: 502, statusMessage: 'Backend request failed' })
  }

  const out: Record<string, string> = {}
  for (const h of ['content-type', 'etag', 'cache-control'] as const) {
    const v = res.headers.get(h)
    if (v) out[h] = v
  }
  if (!out['content-type']?.startsWith('image/')) out['content-type'] = 'image/jpeg'
  setResponseHeaders(event, out)
  setResponseStatus(event, res.status)
  if (res.status === 304 || res._data === undefined || res._data === null) return null
  return Buffer.from(res._data as ArrayBuffer)
})
