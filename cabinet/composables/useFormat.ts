export function useFormat() {
  const rub = (n: number) => `${new Intl.NumberFormat('ru-RU').format(n)} ₽`

  const parseDate = (iso: string | null | undefined): number | null => {
    const t = new Date(iso || '').getTime()
    return Number.isFinite(t) ? t : null
  }

  const date = (iso: string) => {
    const t = parseDate(iso)
    return t === null
      ? '—'
      : new Date(t).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
  }

  const dateTime = (iso: string) => {
    const t = parseDate(iso)
    return t === null
      ? '—'
      : new Date(t).toLocaleString('ru-RU', {
          day: 'numeric',
          month: 'long',
          hour: '2-digit',
          minute: '2-digit',
        })
  }

  const daysLeft = (iso: string) => {
    const t = parseDate(iso)
    if (t === null) return 0
    return Math.max(0, Math.ceil((t - Date.now()) / 86400_000))
  }

  // 0/пусто в контракте бэкенда = безлимит устройств; показываем словами, не значком
  const deviceUsage = (count: number, limit: number | null | undefined) =>
    limit && limit > 0 ? `${count} / ${limit}` : `${count} · без лимита`

  const plural = (n: number, one: string, few: string, many: string) => {
    const mod10 = n % 10
    const mod100 = n % 100
    if (mod10 === 1 && mod100 !== 11) return one
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
    return many
  }

  return { rub, date, dateTime, daysLeft, plural, deviceUsage }
}
