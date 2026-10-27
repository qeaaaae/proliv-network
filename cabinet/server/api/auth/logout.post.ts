import { clearCabinetSession } from '../../utils/session'
import { hasShopBackend, shopFetch } from '../../utils/backend'

export default defineEventHandler(async (event) => {
  if (hasShopBackend(event)) {
    await shopFetch(event, '/api/auth/logout', { method: 'POST', body: {} }).catch(() => undefined)
  }
  clearCabinetSession(event)
  return { ok: true }
})
