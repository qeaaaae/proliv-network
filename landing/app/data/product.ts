import type { ExperienceRecord, LocationRecord, PricingPlan } from '~/types/content'

export const statusUrl = '/status'
export const telegramBotUrl = 'https://t.me/ProlivNetworkBot'
export const supportUrl = 'https://t.me/prolivnet?direct'
export const supportEmail = 'info@proliv-network.xyz'

export const locations: LocationRecord[] = [
  { id: 'united-kingdom', countryCode: 'gb', nameKey: 'locations.items.unitedKingdom', cityKey: 'locations.cities.unitedKingdom', lat: 51.51, lon: -0.13 },
  { id: 'germany', countryCode: 'de', nameKey: 'locations.items.germany', cityKey: 'locations.cities.germany', lat: 50.11, lon: 8.68 },
  { id: 'estonia', countryCode: 'ee', nameKey: 'locations.items.estonia', cityKey: 'locations.cities.estonia', lat: 59.44, lon: 24.75 },
  { id: 'finland', countryCode: 'fi', nameKey: 'locations.items.finland', cityKey: 'locations.cities.finland', lat: 60.17, lon: 24.94 }
]

export const homeCity = { lat: 55.76, lon: 37.62 }

export const experienceItems: ExperienceRecord[] = [
  { id: 'youtube', labelKey: 'experience.items.youtube.label', descriptionKey: 'experience.items.youtube.description', route: 'europe' },
  { id: 'direct', labelKey: 'experience.items.direct.label', descriptionKey: 'experience.items.direct.description', route: 'direct' },
  { id: 'ai', labelKey: 'experience.items.ai.label', descriptionKey: 'experience.items.ai.description', route: 'europe' }
]

export const pricingPlans: PricingPlan[] = [
  { id: 'm1', months: 1, durationDays: 30, priceRub: 179, labelKey: 'pricing.periods.m1' },
  { id: 'm3', months: 3, durationDays: 90, priceRub: 499, labelKey: 'pricing.periods.m3' },
  { id: 'm6', months: 6, durationDays: 180, priceRub: 949, labelKey: 'pricing.periods.m6' },
  { id: 'm12', months: 12, durationDays: 365, priceRub: 1799, labelKey: 'pricing.periods.m12' }
]
