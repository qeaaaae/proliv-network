export default defineNuxtRouteMiddleware(async (to) => {
  // ?ref=u<code> с лендинга/рефералки - захватываем до редиректа на /auth
  useReferral().capture(to.query)
  const promoDeeplink = usePromoDeeplink()
  promoDeeplink.capture(to.query)

  const { user, ensure } = useAuth()
  await ensure()

  if (to.path === '/auth') {
    if (user.value) return navigateTo('/')
    return
  }
  if (!user.value) {
    // Magic link из письма (/?login_token=...) - переносим токен на /auth,
    // там он обменяется на сессию. next не ставим - иначе вернёмся на / с
    // уже погашенным токеном.
    const query: Record<string, string> = {}
    const loginToken = to.query.login_token
    if (typeof loginToken === 'string' && loginToken) {
      query.login_token = loginToken
    } else if (to.fullPath !== '/') {
      query.next = to.fullPath
    }
    return navigateTo({ path: '/auth', query })
  }
  // Промо-диплинк (?startapp=promo_<code>): ведём на /account, где код
  // встанет в поле промокода - активирует его юзер кнопкой «Применить».
  if (to.path !== '/account') {
    const code = promoDeeplink.consume()
    if (code) return navigateTo({ path: '/account', query: { promo: code } })
  }
})
