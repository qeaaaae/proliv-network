import { requireUser } from '../../utils/session'
import { hasShopBackend, mapTicket, shopFetch, type ShopTicketOut } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }

  const res = await shopFetch<{ tickets?: ShopTicketOut[] }>(event, '/api/support/tickets')
  return (res.tickets ?? [])
    .map(mapTicket)
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
})
