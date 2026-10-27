export interface AuthUser {
  id: number
  name: string
  username?: string
  photoUrl?: string
}

export function useAuth() {
  const user = useState<AuthUser | null>('auth:user', () => null)
  const loaded = useState<boolean>('auth:loaded', () => false)

  async function ensure() {
    if (loaded.value) return
    try {
      user.value = await $fetch<AuthUser>('/api/auth/me')
    } catch {
      user.value = null
    }
    loaded.value = true
  }

  async function logout() {
    try {
      await $fetch('/api/auth/logout', { method: 'POST' })
    } finally {
      user.value = null
      loaded.value = false
      await navigateTo('/auth')
    }
  }

  return { user, loaded, ensure, logout }
}
