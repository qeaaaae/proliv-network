import { getQuery, readBody } from 'h3'
import { requireUser } from '../../utils/session'
import { shopFetch } from '../../utils/backend'

// Прокси на minishop admin API (/api/admin/*). Авторизация - тот же Bearer
// apiToken юзера, что и в ЛК; admin-роль проверяет сам minishop (403 для
// не-админов), мы лишь требуем живую сессию.
export default defineEventHandler(async (event) => {
  requireUser(event)

  const splat = String(event.context.params?._ || '')
  const query = getQuery(event)
  const qs = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) qs.set(key, String(value))
  }

  const method = event.method.toUpperCase()
  const body = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)
    ? await readBody(event).catch(() => undefined)
    : undefined

  const path = `/api/admin/${splat}${qs.size ? `?${qs.toString()}` : ''}`
  return await shopFetch(event, path, { method, body })
})
