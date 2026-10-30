<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { telegramBotUrl } from '~/data/product'

const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string
import SiteFooter from '~/components/layout/SiteFooter.vue'
import SiteHeader from '~/components/layout/SiteHeader.vue'
import AccentMark from '~/components/ui/AccentMark.vue'
import BaseButton from '~/components/ui/BaseButton.vue'
import BlueprintLayer from '~/components/ui/BlueprintLayer.vue'

// до 59: диплинк ?start=ref_u<code> не должен превысить лимит Telegram в 64 символа
const REFERRAL_PATTERN = /^[A-Za-z0-9_-]{3,59}$/
const benefits = [
  { title: 'invite.benefits.locations.title', text: 'invite.benefits.locations.text' },
  { title: 'invite.benefits.lte.title', text: 'invite.benefits.lte.text' },
  { title: 'invite.benefits.direct.title', text: 'invite.benefits.direct.text' },
  { title: 'invite.benefits.youtube.title', text: 'invite.benefits.youtube.text' }
]

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const referral = computed(() => {
  const value = Array.isArray(route.query.ref) ? route.query.ref[0] : route.query.ref
  return typeof value === 'string' && REFERRAL_PATTERN.test(value) ? value : ''
})
const telegramUrl = computed(() => `${telegramBotUrl}?start=ref_u${referral.value.replace(/^u/, '')}`)

onMounted(async () => {
  await router.isReady()
  if (!referral.value) await navigateTo('/', { replace: true })
})

useSeoMeta({
  description: () => t('invite.seoDescription'),
  robots: 'noindex, follow',
  ogType: 'website',
  ogSiteName: () => t('brand.name'),
  ogTitle: () => t('brand.name'),
  ogDescription: () => t('invite.seoDescription'),
  ogImageAlt: () => t('seo.imageAlt'),
  ogUrl: 'https://proliv-network.xyz/invite',
  ogLocale: 'ru_RU',
  twitterTitle: () => t('brand.name'),
  twitterDescription: () => t('invite.seoDescription'),
  twitterImageAlt: () => t('seo.imageAlt')
}, { tagPriority: 'critical' })

useHead(() => ({
  title: `Proliv Network | ${t('invite.tabTitle')}`,
  link: [{ rel: 'canonical', href: 'https://proliv-network.xyz/invite' }]
}))
</script>

<template>
  <div class="site-shell">
    <BlueprintLayer />
    <SiteHeader :action-label="t('invite.about')" action-target="/" />
    <main>
      <section class="invite" aria-labelledby="invite-title">
        <div class="content-frame invite-grid">
          <div class="invite-copy">
            <h1 id="invite-title" class="invite-title">
              <span class="invite-line" v-reveal>{{ t('invite.titleBefore') }} <span class="plate invite-plate">{{ t('invite.titleAccent') }}</span></span>
              <span class="invite-line invite-line--muted" v-reveal style="--delay: .08s">{{ t('invite.titleAfter') }}</span>
            </h1>
            <p class="invite-lead" v-reveal style="--delay: .16s">{{ t('invite.description') }}</p>
            <div class="invite-actions" v-reveal style="--delay: .24s">
              <BaseButton :href="cabinetUrl">{{ t('actions.startTrial') }}</BaseButton>
              <BaseButton :href="telegramUrl" variant="secondary" :trail="false">{{ t('invite.openTelegram') }}</BaseButton>
            </div>
          </div>

          <div class="ticket" v-reveal style="--delay: .2s">
            <div class="ticket-main plate">
              <p class="ticket-label">{{ t('invite.passTitle') }}</p>
              <p class="ticket-value">
                {{ t('invite.passValue') }}
                <span>{{ t('invite.passValueNote') }}</span>
              </p>
              <p class="ticket-note">{{ t('invite.passNote') }}</p>
            </div>
            <div class="ticket-stub">
              <div>
                <p class="ticket-discount numeric">{{ t('invite.discountValue') }}</p>
                <p class="ticket-stub-note">{{ t('invite.discountNote') }}</p>
              </div>
              <p v-if="referral" class="ticket-code">
                <span class="ticket-code-label">{{ t('invite.codeLabel') }}</span>
                <strong>{{ referral }}</strong>
              </p>
            </div>
          </div>
        </div>
      </section>

      <section class="landing-block" aria-labelledby="invite-benefits-title">
        <div class="content-frame">
          <header class="block-head" v-reveal>
            <h2 id="invite-benefits-title" class="two-tone">
              <span><AccentMark>{{ t('invite.benefitsTitleAccent') }}</AccentMark> {{ t('invite.benefitsTitleAfter') }}</span>
            </h2>
            <p>{{ t('invite.benefitsLead') }}</p>
          </header>
          <ul class="benefits">
            <li
              v-for="(benefit, index) in benefits"
              :key="benefit.title"
              class="benefit card card--live"
              v-reveal
              :style="{ '--delay': `${index * .08}s` }"
            >
              <h3>{{ t(benefit.title) }}</h3>
              <p>{{ t(benefit.text) }}</p>
            </li>
          </ul>
        </div>
      </section>
    </main>
    <SiteFooter />
  </div>
</template>

<style scoped>
.invite {
  display: grid;
  align-content: center;
  min-height: calc(100svh - var(--header-height));
  padding-block: clamp(24px, 4vh, 48px);
}

.invite-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr);
  align-items: center;
  gap: clamp(32px, 5vw, 72px);
}

.invite-copy {
  display: grid;
  justify-items: start;
  gap: clamp(20px, 2.6vw, 28px);
}

.invite-title {
  display: grid;
  justify-items: start;
  gap: .16em;
  font-size: clamp(30px, 4.6vw, 66px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.04em;
}

.invite-line {
  display: block;
  white-space: nowrap;
}

.invite-line--muted {
  color: var(--fg-secondary);
}

.invite-plate {
  display: inline-block;
  padding: .06em .16em .12em;
  border-radius: .14em;
}

.invite-lead {
  max-width: 46ch;
  color: var(--fg-secondary);
  font-size: clamp(15px, 1.4vw, 18px);
  text-wrap: pretty;
}

.invite-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.ticket {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  filter: drop-shadow(0 30px 50px rgb(0 0 0 / 45%));
  transform: rotate(-3deg);
  transition: transform 700ms var(--ease-out);
}

.ticket-main {
  display: grid;
  align-content: space-between;
  gap: 18px;
  min-height: 300px;
  padding: clamp(22px, 3vw, 32px);
  border-radius: var(--radius-card) 0 0 var(--radius-card);
  -webkit-mask: radial-gradient(circle at 100% 0, transparent 14px, #000 14.5px) top / 100% 51% no-repeat, radial-gradient(circle at 100% 100%, transparent 14px, #000 14.5px) bottom / 100% 51% no-repeat;
  mask: radial-gradient(circle at 100% 0, transparent 14px, #000 14.5px) top / 100% 51% no-repeat, radial-gradient(circle at 100% 100%, transparent 14px, #000 14.5px) bottom / 100% 51% no-repeat;
}

.ticket-label {
  color: var(--plate-ink-soft);
  font-size: 13px;
  font-weight: 700;
}

.ticket-value {
  display: grid;
  font-family: var(--font-display);
  font-size: clamp(44px, 4.8vw, 72px);
  white-space: nowrap;
  font-weight: 800;
  line-height: .92;
  letter-spacing: -.05em;
}

.ticket-value span {
  margin-top: 10px;
  font-size: .3em;
  letter-spacing: -.02em;
}

.ticket-note {
  color: var(--plate-ink-soft);
  font-size: 14px;
  font-weight: 600;
}

.ticket-stub {
  position: relative;
  display: grid;
  align-content: space-between;
  gap: 18px;
  padding: clamp(22px, 3vw, 32px);
  background: var(--panel-raised);
  border: 1px solid var(--line-strong);
  border-left: 2px dashed var(--line-dash);
  border-radius: 0 var(--radius-card) var(--radius-card) 0;
}

.ticket-discount {
  font-family: var(--font-display);
  font-size: clamp(36px, 4vw, 54px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.05em;
}

.ticket-stub-note {
  margin-top: 8px;
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 600;
}

.ticket-code {
  display: grid;
  gap: 6px;
}

.ticket-code-label {
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 600;
}

.ticket-code strong {
  overflow: hidden;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.benefits {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.benefit {
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 22px;
}

.benefit h3 {
  padding-bottom: 14px;
  font-size: 20px;
  border-bottom: 1px dashed var(--line-strong);
  font-weight: 700;
  letter-spacing: -.03em;
}

.benefit p {
  color: var(--fg-secondary);
  font-size: 14px;
}

@media (hover: hover) and (pointer: fine) {
  .ticket:hover {
    transform: rotate(0deg) translateY(-4px);
  }
}

@media (max-width: 980px) {
  .invite-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .benefits {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .invite {
    min-height: 0;
  }

  .invite-line {
    white-space: normal;
  }

  .invite-actions {
    width: 100%;
  }

  .invite-actions .base-button {
    flex: 1 1 100%;
  }

  .ticket {
    grid-template-columns: minmax(0, 1fr);
    transform: none;
  }

  .ticket-main {
    min-height: 240px;
    border-radius: var(--radius-card) var(--radius-card) 0 0;
    -webkit-mask: none;
    mask: none;
  }

  .ticket-stub {
    border-left: 1px solid var(--line-strong);
    border-top: 2px dashed var(--line-dash);
    border-radius: 0 0 var(--radius-card) var(--radius-card);
  }

  .benefits {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
