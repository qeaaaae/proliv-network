import { getRouterParam } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, mapTicketMessage, mapTicketStatus, shopFetch, type ShopTicketMessage, type ShopTicketOut } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const id = (getRouterParam(event, 'id') || '').replace(/^T-/i, '')
  if (!id) throw createError({ statusCode: 400, statusMessage: 'Bad ticket id' })

  const res = await shopFetch<{ ticket?: ShopTicketOut; messages?: ShopTicketMessage[] }>(
    event,
    `/api/support/tickets/${encodeURIComponent(id)}`,
  )
  const t = res.ticket
  if (!t) throw createError({ statusCode: 404, statusMessage: 'Обращение не найдено' })

  return {
    id: `T-${t.ticket_id}`,
    subject: t.subject,
    status: mapTicketStatus(t),
    createdAt: t.created_at || '',
    updatedAt: t.last_message_at || t.updated_at || t.created_at || '',
    messages: (res.messages ?? []).filter((m) => !m.is_internal_note).map(mapTicketMessage),
  }
})
