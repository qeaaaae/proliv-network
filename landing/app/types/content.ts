export type MessageKey = string

export type CountryCode = 'de' | 'ee' | 'fi' | 'gb' | 'kz' | 'nl'

export type LocationId = 'germany' | 'estonia' | 'finland' | 'united-kingdom' | 'netherlands' | 'kazakhstan'

export interface LocationRecord {
  id: LocationId
  countryCode: CountryCode
  nameKey: MessageKey
  cityKey: MessageKey
  lat: number
  lon: number
  portKey?: MessageKey
}

export interface ExperienceRecord {
  id: 'direct' | 'ai' | 'youtube'
  labelKey: MessageKey
  descriptionKey: MessageKey
  route: 'europe' | 'direct'
}

export interface PricingPlan {
  id: 'm1' | 'm3' | 'm6' | 'm12'
  months: number
  durationDays: 30 | 90 | 180 | 365
  priceRub: number
  labelKey: MessageKey
}
