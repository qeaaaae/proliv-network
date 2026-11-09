import { readBody } from 'h3'
import { requireUser } from '../../../../utils/session'
import { shopFetch } from '../../../../utils/backend'
import {
  setSessionFromShopToken,
  throwEmailAuthError,
  type ShopAuthTokenResponse,
} from '../../../../utils/emailAuth'
import { clearTgMergeProof, readTgMergeProof } from '../../../../utils/telegramMerge'

// Шаг 3 merge: код из письма + сохранённые id_token/nonce ->
// upstream POST /api/account/telegram/merge/confirm. Аккаунты сливаются
// в текущий (email-only), TG-аккаунт со своей подпиской переезжает сюда.
export default defineEventHandler(async (event) => {
  requireUser(event)
  const proof = readTgMergeProof(event)
  if (!proof) {
    throw createError({ statusCode: 410, statusMessage: 'Сессия привязки истекла - начните заново' })
  }
  const body = await readBody<{ code?: string }>(event)
  const code = (body?.code || '').trim()
  if (!code) {
    throw createError({ statusCode: 400, statusMessage: 'Введите код из письма' })
  }

  let res: ShopAuthTokenResponse
  try {
    res = await shopFetch<ShopAuthTokenResponse>(event, '/api/account/telegram/merge/confirm', {
      method: 'POST',
      body: { email_code: code, id_token: proof.idt, nonce: proof.nonce },
    })
  } catch (err) {
    throwEmailAuthError(err, 'Не удалось объединить аккаунты')
  }

  clearTgMergeProof(event)
  await setSessionFromShopToken(event, res!, 'User')
})
