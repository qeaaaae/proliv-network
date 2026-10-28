export default defineNuxtRouteMiddleware(async (to) => {
  // ?ref=u<code> с лендинга/рефералки - захватываем до редиректа на /auth
  useReferral().capture(to.query)

  const { user, ensure } = useAuth()
  await ensure()

  if (to.path === '/auth') {
    if (user.value) return navigateTo('/')
    return
  }
  if (!user.value) {
    return navigateTo({ path: '/auth', query: to.fullPath !== '/' ? { next: to.fullPath } : {} })
  }
})
