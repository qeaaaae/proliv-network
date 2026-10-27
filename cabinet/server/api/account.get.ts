import { requireUser } from '../utils/session'
import { hasShopBackend, shopFetch, type ShopMe } from '../utils/backend'

export default defineEventHandler(async (event) => {
  const user = requireUser(event)
  if (!hasShopBackend(event)) {
    return {
      email: null as string | null,
      hasPassword: false,
      telegram: { username: user.username, id: user.id },
      twoFa: false,
    }
  }

  const me = await shopFetch<ShopMe>(event, '/api/me')
  const u = me.user ?? {}
  return {
    email: u.email ?? null,
    hasPassword: u.password_auth_enabled ?? false,
    telegram: { username: u.username ?? user.username, id: u.telegram_id ?? user.id },
    twoFa: false,
  }
})
