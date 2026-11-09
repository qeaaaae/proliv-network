import { readBody } from 'h3'
import { requireUser } from '../../../utils/session'
import { shopFetch } from '../../../utils/backend'
import { throwEmailAuthError } from '../../../utils/emailAuth'

// Установка/смена пароля: код из письма + новый пароль дважды
// (upstream POST /api/account/password/confirm, минимум 8 символов).
export default defineEventHandler(async (event) => {
  requireUser(event)
  const body = await readBody<{ password?: string; passwordConfirm?: string; code?: string }>(event)
  const password = body?.password || ''
  const passwordConfirm = body?.passwordConfirm || ''
  const code = (body?.code || '').trim()
  if (password.length < 8) {
    throw createError({ statusCode: 400, statusMessage: 'Пароль - минимум 8 символов' })
  }
  if (password !== passwordConfirm) {
    throw createError({ statusCode: 400, statusMessage: 'Пароли не совпадают' })
  }
  if (!code) {
    throw createError({ statusCode: 400, statusMessage: 'Введите код из письма' })
  }
  try {
    return await shopFetch<{ ok?: boolean; password_auth_enabled?: boolean }>(
      event,
      '/api/account/password/confirm',
      {
        method: 'POST',
        body: { password, password_confirm: passwordConfirm, code },
      },
    )
  } catch (err) {
    throwEmailAuthError(err, 'Не удалось сохранить пароль')
  }
})
