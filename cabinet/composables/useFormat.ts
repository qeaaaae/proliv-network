export function useFormat() {
  const rub = (n: number) => `${new Intl.NumberFormat('ru-RU').format(n)} ₽`

  const date = (iso: string) =>
    new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })

  const dateTime = (iso: string) =>
    new Date(iso).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'long',
      hour: '2-digit',
      minute: '2-digit',
    })

  const daysLeft = (iso: string) => {
    const ms = new Date(iso).getTime() - Date.now()
    return Math.max(0, Math.ceil(ms / 86400_000))
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
