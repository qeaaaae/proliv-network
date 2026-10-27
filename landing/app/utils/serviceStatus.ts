export type ServiceState = 'operational' | 'partial' | 'down' | 'unknown'

interface StatusItem {
  up?: unknown
}

interface StatusGroups {
  locations?: StatusItem[]
  services?: StatusItem[]
}

export function resolveServiceStatus(status: unknown, now = Date.now()): ServiceState {
  if (typeof status !== 'object' || status === null) return 'unknown'

  const { updated_at: updatedAt, all_up: allUp, groups } = status as {
    updated_at?: unknown
    all_up?: unknown
    groups?: StatusGroups
  }

  if (typeof updatedAt !== 'number' || now - updatedAt * 1000 > 300_000 || updatedAt * 1000 - now > 60_000) return 'unknown'
  if (allUp === true) return 'operational'

  const items = [...(groups?.locations ?? []), ...(groups?.services ?? [])]
  const downs = items.filter(item => item && item.up === false).length
  if (items.length && downs === items.length) return 'down'
  if (downs > 0 || allUp === false) return 'partial'
  return 'unknown'
}
