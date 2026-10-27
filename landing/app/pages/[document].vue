<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import LegalDocumentView from '~/components/legal/LegalDocument.vue'
import SiteHeader from '~/components/layout/SiteHeader.vue'
import BlueprintLayer from '~/components/ui/BlueprintLayer.vue'
import { legalDocuments, type LegalDocumentId } from '~/data/legal'

definePageMeta({
  middleware: to => Object.hasOwn(legalDocuments, String(to.params.document)) ? undefined : navigateTo('/', { redirectCode: 302, replace: true })
})

const route = useRoute()
const { t } = useI18n()

const documentId = computed(() => route.params.document as LegalDocumentId)

const legalDocument = computed(() => legalDocuments[documentId.value])

useSeoMeta({
  description: () => legalDocument.value.summary,
  ogType: 'website',
  ogSiteName: () => t('brand.name'),
  ogTitle: () => t('brand.name'),
  ogDescription: () => legalDocument.value.summary,
  ogImageAlt: () => t('seo.imageAlt'),
  ogUrl: () => `https://proliv-network.xyz/${documentId.value}`,
  ogLocale: 'ru_RU',
  twitterTitle: () => t('brand.name'),
  twitterDescription: () => legalDocument.value.summary,
  twitterImageAlt: () => t('seo.imageAlt')
}, { tagPriority: 'critical' })

useHead(() => ({
  title: `Proliv Network | ${legalDocument.value.tabTitle}`,
  link: [{ rel: 'canonical', href: `https://proliv-network.xyz/${documentId.value}` }]
}))
</script>

<template>
  <div class="site-shell">
    <BlueprintLayer />
    <SiteHeader :action-label="t('legal.back')" action-target="/" />
    <LegalDocumentView :document="legalDocument" />
  </div>
</template>
