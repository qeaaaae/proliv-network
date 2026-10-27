import { shopApiUrl } from '../../../utils/backend'
import { ofetch } from 'ofetch'

// OIDC-вход через oauth.telegram.org (post_message flow):
// бэкенд выдаёт подписанный nonce + client_id бота; фронт открывает попап
// Telegram OAuth с этим nonce, получает id_token и обменивает его
// через POST /api/auth/token (см. telegram.post.ts).
export default defineEventHandler(async (event) => {
  const base = shopApiUrl(event)
  if (!base) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  try {
    return await ofetch(`${base}/api/auth/telegram/nonce`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept-Encoding': 'identity' },
      body: '{}',
      timeout: 15000,
    })
  } catch (err) {
    const e = err as { statusCode?: number; data?: { detail?: string } }
    throw createError({
      statusCode: e.statusCode ?? 502,
      statusMessage: e.data?.detail || 'Backend auth failed',
    })
  }
})
