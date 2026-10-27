import { getRouterParam } from 'h3'
import { requireUser } from '../../../utils/session'
import { hasShopBackend } from '../../../utils/backend'

// Закрытие тикета юзером не поддерживается WebApp API бэкенда
// (закрывает саппорт). Оставлено как понятная ошибка.
export default defineEventHandler((event) => {
  requireUser(event)
  void getRouterParam(event, 'id')
  if (!hasShopBackend(event)) {
    throw createError({ statusCode: 503, statusMessage: 'Backend is not configured' })
  }
  throw createError({ statusCode: 405, statusMessage: 'Закрыть обращение может только поддержка' })
})
