import { clearCabinetSession, getCabinetSession } from '../../utils/session'
import { shopFetch, type ShopMe } from '../../utils/backend'

// Сессионный юзер. Если есть токен бэкенда - дотягиваем /api/me, чтобы имя и
// аватар были настоящими. telegram_photo_url приходит относительным путём
// (/api/account/avatar) - он же у нас проксируется, отдаём как есть.
// apiToken/apiCsrf из ответа не отдаём: httpOnly-кука хранит их на сервере.
export default defineEventHandler(async (event) => {
  const user = getCabinetSession(event)
  if (!user) throw createError({ statusCode: 401, statusMessage: 'Unauthorized' })

  const safe = { id: user.id, name: user.name, username: user.username, photoUrl: user.photoUrl }
  if (!user.apiToken) return safe

  try {
    const me = await shopFetch<ShopMe>(event, '/api/me')
    const photo = me.user?.telegram_photo_url
    return {
      id: safe.id,
      name: me.user?.first_name || safe.name,
      username: me.user?.username ?? safe.username,
      photoUrl: photo
        ? photo.startsWith('/api/')
          ? photo
          : '/api/account/avatar'
        : safe.photoUrl,
    }
  } catch (e) {
    // Токен бэкенда протух - сбрасываем куку, чтобы юзер мог перелогиниться
    // (иначе middleware считает сессию живой, а все запросы идут в 401)
    if ((e as { statusCode?: number }).statusCode === 401) {
      clearCabinetSession(event)
      throw createError({ statusCode: 401, statusMessage: 'Backend session expired' })
    }
    return safe
  }
})
