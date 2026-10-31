// Обёртка над /api/admin/* (BFF-прокси в server/api/admin/[...].ts).
// Ошибки minishop приходят как { ok:false, error } - мапим в читаемый текст.
export interface AdminApiError extends Error {
  code?: string
}

export function useAdminApi() {
  async function call<T = Record<string, unknown>>(
    path: string,
    opts: { method?: string; body?: unknown; query?: Record<string, unknown> } = {},
  ): Promise<T> {
    const qs = new URLSearchParams()
    for (const [key, value] of Object.entries(opts.query || {})) {
      if (value !== undefined && value !== null && value !== '') qs.set(key, String(value))
    }
    const url: string = `/api/admin/${path}${qs.size ? `?${qs.toString()}` : ''}`
    try {
      return (await $fetch<unknown>(url, {
        method: (opts.method || 'GET') as 'GET',
        body: opts.body === undefined ? undefined : (opts.body as never),
      })) as T
    } catch (err) {
      const data = (err as { data?: { error?: string; message?: string } }).data || {}
      const e: AdminApiError = new Error(data.error || data.message || 'request_failed')
      e.code = data.error
      throw e
    }
  }

  return { call }
}
