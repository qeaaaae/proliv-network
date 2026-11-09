import { requireUser } from '../../../utils/session'
import { shopFetch } from '../../../utils/backend'
import { throwEmailAuthError } from '../../../utils/emailAuth'

// Код подтверждения для установки/смены пароля - уходит на уже привязанную
// почту (upstream POST /api/account/password/request). Тело обязано быть
// JSON - upstream отклоняет запросы без тела.
export default defineEventHandler(async (event) => {
  requireUser(event)
  try {
    return await shopFetch<{ ok?: boolean }>(event, '/api/account/password/request', {
      method: 'POST',
      body: {},
    })
  } catch (err) {
    throwEmailAuthError(err, 'Не удалось отправить код')
  }
})
