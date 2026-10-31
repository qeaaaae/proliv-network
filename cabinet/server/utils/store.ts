// Типы контракта API кабинета. Подписка отдаёт все локации сразу -
// точку выхода юзер выбирает в VPN-клиенте, поэтому переключателя
// локации в кабинете нет.

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

// Локации, которые есть в подписке (флаги в UI).
export const LOCATION_IDS = ['gb', 'ee', 'de', 'fi'] as const

export function fmtNow(): string {
  return new Date().toISOString()
}
