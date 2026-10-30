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
    return navigateTo({ path: '/auth', query: to.fullPath !== '/' ? { next: to.fullPath } : {} })
  }
  // Промо-диплинк (?startapp=promo_<code>): ведём на /account, где код
  // встанет в поле промокода - активирует его юзер кнопкой «Применить».
  if (to.path !== '/account') {
    const code = promoDeeplink.consume()
    if (code) return navigateTo({ path: '/account', query: { promo: code } })
  }
})
