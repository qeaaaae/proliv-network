// Типы контракта API кабинета + локальные предпочтения, которых нет
// на общем бэкенде (выбор локации - наша фича, маппинг на squad'ы
// Remnawave через бэкенд планируется отдельно).

export interface Device {
  id: string
  name: string
  platform: 'ios' | 'android' | 'windows' | 'macos' | 'tvos' | 'linux' | 'other'
  hwid: string
  lastSeen: string
}

export interface Subscription {
  plan: string
  until: string
  trafficUsedGb: number
  trafficLimitGb: number
  resetAt: string
  devices: Device[]
  deviceLimit: number
  locations: string[]
  location: string
  subscriptionUrl: string
}

export interface Order {
  id: string
  title: string
  amount: number
  method: string
  status: 'paid' | 'pending' | 'refunded' | 'failed'
  at: string
  checkoutUrl: string | null
}

export interface TicketMessage {
  from: 'user' | 'support'
  text: string
  at: string
}

export interface Ticket {
  id: string
  subject: string
  status: 'open' | 'answered' | 'closed'
  createdAt: string
  updatedAt: string
  messages: TicketMessage[]
}

export interface BonusEntry {
  id: string
  kind: 'in' | 'out'
  title: string
  amount: number
  at: string
}

// Выбранная локация юзера (in-memory; при рестарте сбрасывается на дефолт).
// TODO: переключение internal squad через бэкенд.
const locations = new Map<number, string>()

export const LOCATION_IDS = ['gb', 'ee', 'de'] as const

export function getLocation(userId: number): string {
  return locations.get(userId) ?? 'ee'
}

export function setLocation(userId: number, location: string): void {
  if ((LOCATION_IDS as readonly string[]).includes(location)) locations.set(userId, location)
}

export function fmtNow(): string {
  return new Date().toISOString()
}
