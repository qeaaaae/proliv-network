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
const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string

const { t } = useI18n()

useSeoMeta({
  description: () => t('seo.description'),
  ogType: 'website',
  ogSiteName: () => t('brand.name'),
  ogTitle: () => t('brand.name'),
  ogDescription: () => t('seo.description'),
  ogImageAlt: () => t('seo.imageAlt'),
  ogUrl: 'https://proliv-network.xyz/',
  ogLocale: 'ru_RU',
  twitterTitle: () => t('brand.name'),
  twitterDescription: () => t('seo.description'),
  twitterImageAlt: () => t('seo.imageAlt')
}, { tagPriority: 'critical' })
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
