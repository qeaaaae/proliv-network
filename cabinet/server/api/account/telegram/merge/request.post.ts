import { requireUser } from '../../../../utils/session'
import { shopFetch } from '../../../../utils/backend'
import { throwEmailAuthError } from '../../../../utils/emailAuth'
import { readTgMergeProof } from '../../../../utils/telegramMerge'

// Шаг 2 merge: код подтверждения на email текущего аккаунта
// (upstream POST /api/account/telegram/merge/request, purpose=merge_telegram).
export default defineEventHandler(async (event) => {
  requireUser(event)
  if (!readTgMergeProof(event)) {
    throw createError({ statusCode: 409, statusMessage: 'Сессия привязки истекла - начните заново' })
  }
  try {
    return await shopFetch<{ ok?: boolean }>(event, '/api/account/telegram/merge/request', {
      method: 'POST',
      body: {},
    })
  } catch (err) {
    throwEmailAuthError(err, 'Не удалось отправить код')
  }
})
