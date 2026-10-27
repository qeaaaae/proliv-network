import { getRouterParam, readBody } from 'h3'
import { requireUser } from '../../../utils/session'
import { hasShopBackend, mapTicketMessage, mapTicketStatus, shopFetch, type ShopTicketMessage, type ShopTicketOut } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const id = (getRouterParam(event, 'id') || '').replace(/^T-/i, '')
  const body = await readBody<{ text?: string }>(event)
  const text = (body?.text || '').trim()
  if (!text) throw createError({ statusCode: 400, statusMessage: 'Пустое сообщение' })

  await shopFetch(event, `/api/support/tickets/${encodeURIComponent(id)}/messages`, {
    method: 'POST',
    body: { body: text.slice(0, 4000) },
  })

  const res = await shopFetch<{ ticket?: ShopTicketOut; messages?: ShopTicketMessage[] }>(
    event,
    `/api/support/tickets/${encodeURIComponent(id)}`,
  ).catch(() => null)
  const t = res?.ticket

  return {
    id: t ? `T-${t.ticket_id}` : `T-${id}`,
    subject: t?.subject ?? '',
    status: t ? mapTicketStatus(t) : 'open',
    createdAt: t?.created_at || '',
    updatedAt: t?.last_message_at || t?.updated_at || new Date().toISOString(),
    messages: (res?.messages ?? []).filter((m) => !m.is_internal_note).map(mapTicketMessage),
  }
})
