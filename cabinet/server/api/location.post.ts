import { createError, readBody } from 'h3'
import { requireUser } from '../utils/session'
import { getLocation, LOCATION_IDS, setLocation } from '../utils/store'

const LOCATION_NAMES: Record<string, string> = {
  ee: 'Эстония - Таллин',
  gb: 'Великобритания - Лондон',
  de: 'Германия - Франкфурт',
}

// Смена активной локации. Пока хранится локально: прямого эндпоинта
// переключения squad у юзера в API бэкенда нет (TODO: маппинг на
// internal squad Remnawave через расширение бэкенда).
export default defineEventHandler(async (event) => {
  const user = requireUser(event)
  const body = await readBody<{ location?: string }>(event)
  const location = body?.location

  if (!location || !(LOCATION_IDS as readonly string[]).includes(location)) {
    throw createError({ statusCode: 400, statusMessage: 'Локация недоступна в вашем плане' })
  }

  setLocation(user.id, location)
  return { ok: true, location: getLocation(user.id), locationName: LOCATION_NAMES[location] ?? location }
})
