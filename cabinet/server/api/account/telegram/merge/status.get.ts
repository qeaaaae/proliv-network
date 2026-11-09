import { requireUser } from '../../../../utils/session'
import { readTgMergeProof } from '../../../../utils/telegramMerge'

// Статус pending-merge: есть ли подписанная merge-куки после OIDC-link 409.
// Фронт показывает, какой Telegram будет объединён с текущим аккаунтом.
export default defineEventHandler(async (event) => {
  requireUser(event)
  const proof = readTgMergeProof(event)
  if (!proof) return { ok: false as const }
  return {
    ok: true as const,
    telegram: {
      id: proof.tgId ?? null,
      username: proof.tgUsername ?? null,
      firstName: proof.tgName ?? null,
    },
  }
})
