// Ленивая проверка 'этот аккаунт - админ в minishop': один запрос на
// /api/admin/health, результат кешируется в useState на сессию страницы.
// minishop сам решает, кто админ (is_admin / ADMIN_IDS на бэкенде).
export function useAdmin() {
  const isAdmin = useState<boolean>('admin:is', () => false)
  const checked = useState<boolean>('admin:checked', () => false)

  async function ensure() {
    if (checked.value) return
    checked.value = true
    try {
      await $fetch('/api/admin/health')
      isAdmin.value = true
    } catch {
      isAdmin.value = false
    }
  }

  return { isAdmin, checked, ensure }
}
