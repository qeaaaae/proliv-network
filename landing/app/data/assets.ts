import brandLogoUrl from '~/assets/images/brand/logo.svg'
import deFlagUrl from '~/assets/images/flags/de.svg'
import eeFlagUrl from '~/assets/images/flags/ee.svg'
import fiFlagUrl from '~/assets/images/flags/fi.svg'
import gbFlagUrl from '~/assets/images/flags/gb.svg'
import kzFlagUrl from '~/assets/images/flags/kz.svg'
import nlFlagUrl from '~/assets/images/flags/nl.svg'
import yookassaLogoUrl from '~/assets/images/payments/yookassa.svg'
import type { CountryCode } from '~/types/content'

export { brandLogoUrl }

export const flagUrls = {
  de: deFlagUrl,
  ee: eeFlagUrl,
  fi: fiFlagUrl,
  gb: gbFlagUrl,
  kz: kzFlagUrl,
  nl: nlFlagUrl
} satisfies Record<CountryCode, string>

export const paymentMarks = [
  { id: 'yookassa', src: yookassaLogoUrl, alt: 'ЮKassa', width: 92, height: 22 }
] as const
