import { readBody } from 'h3'
import { requireUser } from '../../utils/session'
import { hasShopBackend, mapTicket, mapTicketStatus, shopFetch, type ShopTicketOut } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  const body = await readBody<{ subject?: string; text?: string }>(event)
  const subject = (body?.subject || '').trim()
  const text = (body?.text || '').trim()
  if (!subject || !text) {
    throw createError({ statusCode: 400, statusMessage: 'Заполните тему и сообщение' })
  }

  const res = await shopFetch<{ ticket?: ShopTicketOut; ok?: boolean }>(event, '/api/support/tickets', {
    method: 'POST',
    body: { subject: subject.slice(0, 120), body: text.slice(0, 4000) },
  })
  const t = res.ticket
  if (!t) throw createError({ statusCode: 502, statusMessage: 'Ticket not created' })

  const mapped = mapTicket(t)
  return {
    ...mapped,
    status: mapTicketStatus(t),
    messages: [{ from: 'user' as const, text: text.slice(0, 4000), at: t.created_at || new Date().toISOString() }],
  }
})
