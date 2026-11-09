<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import SiteFooter from '~/components/layout/SiteFooter.vue'
import SiteHeader from '~/components/layout/SiteHeader.vue'
import ConnectSection from '~/components/sections/ConnectSection.vue'
import FaqSection from '~/components/sections/FaqSection.vue'
import FinalCta from '~/components/sections/FinalCta.vue'
import HeroSection from '~/components/sections/HeroSection.vue'
import LocationsSection from '~/components/sections/LocationsSection.vue'
import LteSection from '~/components/sections/LteSection.vue'
import PricingSection from '~/components/sections/PricingSection.vue'
import RoutesSection from '~/components/sections/RoutesSection.vue'
import BlueprintLayer from '~/components/ui/BlueprintLayer.vue'
import { pricingPlans, supportEmail, supportUrl, telegramBotUrl } from '~/data/product'
const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string

const { t } = useI18n()

const faqIds = ['trial', 'devices', 'traffic', 'direct', 'locations', 'payment'] as const

const structuredData = computed(() => [
  {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Proliv Network',
    url: 'https://proliv-network.xyz/',
    logo: 'https://proliv-network.xyz/images/logo.svg',
    email: supportEmail,
    sameAs: [telegramBotUrl, supportUrl]
  },
  {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Proliv Network',
    url: 'https://proliv-network.xyz/',
    inLanguage: 'ru-RU'
  },
  {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: 'Proliv Network',
    serviceType: 'VPN',
    url: 'https://proliv-network.xyz/',
    provider: { '@type': 'Organization', name: 'Proliv Network' },
    offers: pricingPlans.map(plan => ({
      '@type': 'Offer',
      name: `${plan.months} мес.`,
      price: plan.priceRub,
      priceCurrency: 'RUB',
      url: 'https://proliv-network.xyz/#pricing'
    }))
  },
  {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqIds.map(id => ({
      '@type': 'Question',
      name: t(`faq.items.${id}.question`),
      acceptedAnswer: { '@type': 'Answer', text: t(`faq.items.${id}.answer`) }
    }))
  }
])

useSeoMeta({
  title: () => t('seo.title'),
  description: () => t('seo.description'),
  ogType: 'website',
  ogSiteName: () => t('brand.name'),
  ogTitle: () => t('seo.title'),
  ogDescription: () => t('seo.description'),
  ogImage: 'https://proliv-network.xyz/images/og-banner.png',
  ogImageWidth: 1200,
  ogImageHeight: 630,
  ogImageAlt: () => t('seo.imageAlt'),
  ogUrl: 'https://proliv-network.xyz/',
  ogLocale: 'ru_RU',
  twitterCard: 'summary_large_image',
  twitterTitle: () => t('seo.title'),
  twitterDescription: () => t('seo.description'),
  twitterImage: 'https://proliv-network.xyz/images/og-banner.png',
  twitterImageAlt: () => t('seo.imageAlt')
}, { tagPriority: 'critical' })

useHead(() => ({
  script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(structuredData.value) }]
}))
</script>

<template>
  <div class="site-shell">
    <BlueprintLayer />
    <SiteHeader :action-label="t('actions.cabinet')" :action-target="cabinetUrl" />
    <main>
      <HeroSection />
      <LocationsSection />
      <LteSection />
      <RoutesSection />
      <PricingSection />
      <ConnectSection />
      <FaqSection />
    </main>
    <SiteFooter>
      <FinalCta />
    </SiteFooter>
  </div>
</template>
