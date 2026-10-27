export default defineNuxtRouteMiddleware(async (to) => {
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
