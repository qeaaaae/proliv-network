<script setup lang="ts">
import SiteFooter from '~/components/layout/SiteFooter.vue'
import SiteHeader from '~/components/layout/SiteHeader.vue'
import BaseButton from '~/components/ui/BaseButton.vue'
import BlueprintLayer from '~/components/ui/BlueprintLayer.vue'

const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string

// Разовая фича: именная ссылка /pay/igor. Вырезать = удалить этот файл и
// роут из nitro.prerender.routes в nuxt.config.ts.
const displayName = 'Игорю Любимому'

// Сердечки вокруг тикета: [top%, left%, размер px, задержка s, длительность s]
const hearts = [
  { top: -8, left: 6, size: 26, delay: 0, dur: 5.2 },
  { top: -14, left: 78, size: 34, delay: 0.7, dur: 6.1 },
  { top: 30, left: -6, size: 20, delay: 1.2, dur: 4.8 },
  { top: 46, left: 96, size: 24, delay: 0.4, dur: 5.6 },
  { top: 82, left: 84, size: 22, delay: 1.6, dur: 5.0 },
  { top: 90, left: 12, size: 18, delay: 0.9, dur: 6.4 }
]

useSeoMeta({ robots: 'noindex, nofollow' })
useHead(() => ({ title: `Proliv Network | Оплата для ${displayName}` }))
</script>

<template>
  <div class="site-shell">
    <BlueprintLayer />
    <SiteHeader action-label="На главную" action-target="/" />
    <main>
      <section class="pay" aria-labelledby="pay-title">
        <div class="content-frame pay-grid">
          <div class="pay-copy">
            <h1 id="pay-title" class="pay-title">
              <span class="pay-line" v-reveal>Персональная ссылка</span>
              <span class="pay-line" v-reveal style="--delay: .06s"><span class="plate pay-plate">на оплату</span> для</span>
              <span class="pay-line pay-line--name" v-reveal style="--delay: .12s">{{ displayName }}<svg class="pay-heart" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></span>
            </h1>
            <p class="pay-lead" v-reveal style="--delay: .18s">
              Эта ссылка выдана лично. По кнопке — оплата подписки Proliv Network:
              вход через Telegram, выбор тарифа и оплата картой.
            </p>
            <div class="pay-actions" v-reveal style="--delay: .24s">
              <BaseButton :href="`${cabinetUrl}/purchases`">Перейти к оплате</BaseButton>
            </div>
          </div>

          <div class="ticket-wrap" v-reveal style="--delay: .2s">
            <div class="ticket">
              <div class="ticket-main plate">
                <p class="ticket-label">Выдано</p>
                <p class="ticket-value">{{ displayName }}</p>
                <p class="ticket-note">proliv-network.xyz/pay/igor</p>
                <svg class="card-heart card-heart--name" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
              </div>
              <div class="ticket-stub">
                <div>
                  <p class="ticket-discount numeric">Proliv Network</p>
                  <p class="ticket-stub-note">подписка · без привязки к устройству</p>
                </div>
                <svg class="card-heart card-heart--stub" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
              </div>
            </div>
            <svg
              v-for="(heart, index) in hearts"
              :key="index"
              class="floating-heart"
              :style="{
                top: `${heart.top}%`,
                left: `${heart.left}%`,
                width: `${heart.size}px`,
                height: `${heart.size}px`,
                '--hd': `${heart.delay}s`,
                '--ht': `${heart.dur}s`
              }"
              viewBox="0 0 24 24"
              aria-hidden="true"
            ><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          </div>
        </div>
      </section>
    </main>
    <SiteFooter />
  </div>
</template>

<style scoped>
.pay {
  display: grid;
  align-content: center;
  min-height: calc(100svh - var(--header-height));
  padding-block: clamp(24px, 4vh, 48px);
}

.pay-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr);
  align-items: center;
  gap: clamp(32px, 5vw, 72px);
}

.pay-copy {
  display: grid;
  justify-items: start;
  gap: clamp(20px, 2.6vw, 28px);
  min-width: 0;
}

.pay-title {
  display: grid;
  justify-items: start;
  gap: .14em;
  max-width: 100%;
  font-size: clamp(26px, 4.4vw, 60px);
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -.04em;
}

.pay-line {
  display: block;
  max-width: 100%;
}

.pay-line--name {
  display: inline-flex;
  align-items: center;
  gap: .22em;
  color: var(--fg-secondary);
}

.pay-heart {
  flex: none;
  width: .72em;
  height: .72em;
  fill: #ff6d97;
  filter: drop-shadow(0 0 12px rgb(255 109 151 / 65%));
  animation: heart-beat 1.9s ease-in-out infinite;
}

.pay-plate {
  display: inline-block;
  padding: .06em .16em .12em;
  border-radius: .14em;
}

.pay-lead {
  max-width: 46ch;
  color: var(--fg-secondary);
  font-size: clamp(15px, 1.4vw, 18px);
  text-wrap: pretty;
}

.pay-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.ticket-wrap {
  position: relative;
  min-width: 0;
}

.ticket {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  filter: drop-shadow(0 30px 50px rgb(0 0 0 / 45%));
  transform: rotate(-3deg);
  transition: transform 700ms var(--ease-out);
}

.ticket-main {
  position: relative;
  display: grid;
  align-content: space-between;
  gap: 18px;
  min-height: 300px;
  padding: clamp(22px, 3vw, 32px);
  border-radius: var(--radius-card) 0 0 var(--radius-card);
}

.ticket-label {
  color: var(--plate-ink-soft);
  font-size: 13px;
  font-weight: 700;
}

.ticket-value {
  display: grid;
  font-family: var(--font-display);
  font-size: clamp(32px, 3.6vw, 52px);
  font-weight: 800;
  line-height: .98;
  letter-spacing: -.04em;
  word-break: break-word;
}

.ticket-note {
  color: var(--plate-ink-soft);
  font-size: 14px;
  font-weight: 600;
  word-break: break-all;
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
  font-size: clamp(24px, 2.6vw, 40px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -.04em;
}

.ticket-stub-note {
  margin-top: 8px;
  color: var(--fg-secondary);
  font-size: 13px;
  font-weight: 600;
}

.card-heart {
  position: absolute;
  fill: #ff6d97;
  pointer-events: none;
  filter: drop-shadow(0 0 10px rgb(255 109 151 / 55%));
  animation: heart-beat 2.3s ease-in-out infinite;
}

.card-heart--name {
  top: 38%;
  right: 7%;
  width: clamp(40px, 4.5vw, 60px);
  height: clamp(40px, 4.5vw, 60px);
}

.card-heart--stub {
  right: 8%;
  bottom: 16%;
  width: 34px;
  height: 34px;
  animation-delay: .5s;
}

.floating-heart {
  position: absolute;
  fill: #ff6d97;
  opacity: .85;
  pointer-events: none;
  filter: drop-shadow(0 0 8px rgb(255 109 151 / 45%));
  animation: heart-float var(--ht, 5.5s) ease-in-out var(--hd, 0s) infinite alternate;
}

@keyframes heart-float {
  from {
    transform: translateY(0) rotate(-6deg) scale(1);
    opacity: .55;
  }
  to {
    transform: translateY(-14px) rotate(8deg) scale(1.08);
    opacity: 1;
  }
}

@keyframes heart-beat {
  0%, 100% {
    transform: scale(1);
  }
  25% {
    transform: scale(1.18);
  }
  40% {
    transform: scale(1.02);
  }
}

@media (hover: hover) and (pointer: fine) {
  .ticket:hover {
    transform: rotate(0deg) translateY(-4px);
  }
}

@media (max-width: 980px) {
  .pay-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .ticket-wrap {
    max-width: 520px;
  }
}

@media (max-width: 620px) {
  .pay {
    min-height: 0;
    padding-block: 28px 56px;
  }

  .pay-actions {
    width: 100%;
  }

  .pay-actions .base-button {
    flex: 1 1 100%;
  }

  .ticket {
    grid-template-columns: minmax(0, 1fr);
    transform: none;
  }

  .ticket-main {
    min-height: 0;
    gap: 14px;
    border-radius: var(--radius-card) var(--radius-card) 0 0;
  }

  .card-heart--name {
    top: 18px;
    right: 18px;
  }

  .ticket-stub {
    border-left: 1px solid var(--line-strong);
    border-top: 2px dashed var(--line-dash);
    border-radius: 0 0 var(--radius-card) var(--radius-card);
  }

  .floating-heart {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .floating-heart,
  .card-heart,
  .pay-heart {
    animation: none;
  }
}
</style>
