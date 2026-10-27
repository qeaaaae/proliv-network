import { createHmac } from 'node:crypto'
import { readBody } from 'h3'
import { ofetch } from 'ofetch'
import { setSession } from '../../utils/session'
import { shopApiUrl } from '../../utils/backend'

// Dev-вход admin/admin: при настроенном бэкенде подписывает синтетический
// initData токеном бота и получает настоящую сессию minishop. Иначе -
// локальная stub-сессия. Доступен при NUXT_PUBLIC_DEV_AUTH=1 или в dev-режиме.
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  if (String(config.public.devAuth) !== '1' && !import.meta.dev) {
    throw createError({ statusCode: 404, statusMessage: 'Not found' })
  }

  const body = await readBody<{ login?: string; password?: string }>(event)
  if (body?.login !== 'admin' || body?.password !== 'admin') {
    throw createError({ statusCode: 401, statusMessage: 'Неверный логин или пароль' })
  }

  const devUser = { id: 880994961, name: 'Рафаэль', username: 'qeaaaceo' }
  const backend = shopApiUrl(event)

  if (!backend || !config.botToken) {
    setSession(event, { ...devUser, photoUrl: undefined })
    return { ok: true, mode: 'local' }
  }

  // Подписываем initData как это делает Telegram (HMAC-SHA256, ключ "WebAppData")
  const authDate = Math.floor(Date.now() / 1000)
  const userJson = JSON.stringify({ id: devUser.id, first_name: devUser.name, username: devUser.username })
  const checkString = `auth_date=${authDate}\nuser=${userJson}`
  const secret = createHmac('sha256', 'WebAppData').update(config.botToken).digest()
  const hash = createHmac('sha256', secret).update(checkString).digest('hex')
  const initData = `auth_date=${authDate}&hash=${hash}&user=${encodeURIComponent(userJson)}`

  const tokenUrl: string = `${backend}/api/auth/token`
  let res: { token?: string; csrf_token?: string; telegram_id?: number; user_id?: number } | null =
    null
  try {
    res = await ofetch(tokenUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept-Encoding': 'identity' },
      body: JSON.stringify({ init_data: initData }),
      timeout: 15000,
    })
  } catch {
    // TG-auth выключен на локальном стенде - идём в email/password
  }

  if (!res?.token) {
    const emailUrl: string = `${backend}/api/auth/email/password`
    try {
      res = await ofetch(emailUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept-Encoding': 'identity' },
        body: JSON.stringify({ email: 'dev@proliv.dev', password: 'admin12345' }),
        timeout: 15000,
      })
    } catch (err) {
      const e = err as { statusCode?: number; data?: { detail?: string; message?: string } }
      throw createError({
        statusCode: e.statusCode ?? 502,
        statusMessage: e.data?.detail || e.data?.message || 'Backend auth failed',
      })
    }
  }
  if (!res?.token) {
    throw createError({ statusCode: 502, statusMessage: 'Backend did not issue a token' })
  }

  setSession(event, {
    ...devUser,
    photoUrl: undefined,
    apiToken: res.token,
    apiCsrf: res.csrf_token,
  })
  return { ok: true, mode: 'backend' }
})
