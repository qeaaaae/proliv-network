import { createHash, createHmac } from 'node:crypto'

export interface TelegramAuthPayload {
  id: number
  first_name?: string
  last_name?: string
  username?: string
  photo_url?: string
  auth_date: number | string
  hash: string
  [key: string]: unknown
}

/**
 * Проверка подписи Telegram Login Widget.
 * https://core.telegram.org/widgets/login#checking-authorization
 */
export function verifyTelegramAuth(payload: TelegramAuthPayload, botToken: string): boolean {
  // check-string = все поля виджета кроме hash, включая auth_date
  // (https://core.telegram.org/widgets/login#checking-authorization).
  // referralCode/startParam инжектит наш фронт - Telegram их не подписывал.
  const { hash, referralCode, startParam, ...fields } = payload
  if (!hash || !fields.auth_date) return false

  const checkString = Object.keys(fields)
    .filter((key) => fields[key] !== undefined && fields[key] !== null && fields[key] !== '')
    .sort()
    .map((key) => `${key}=${fields[key]}`)
    .join('\n')

  const secret = createHash('sha256').update(botToken).digest()
  const expected = createHmac('sha256', secret).update(checkString).digest('hex')
  if (expected !== hash) return false

  const authAge = Math.floor(Date.now() / 1000) - Number(fields.auth_date)
  return authAge >= 0 && authAge < 86400
}
