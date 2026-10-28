<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { supportUrl } from '~/data/product'
import AccentMark from '~/components/ui/AccentMark.vue'
import BaseButton from '~/components/ui/BaseButton.vue'

const { t } = useI18n()
const questions = [
  { question: 'faq.items.trial.question', answer: 'faq.items.trial.answer' },
  { question: 'faq.items.devices.question', answer: 'faq.items.devices.answer' },
  { question: 'faq.items.traffic.question', answer: 'faq.items.traffic.answer' },
  { question: 'faq.items.direct.question', answer: 'faq.items.direct.answer' },
  { question: 'faq.items.locations.question', answer: 'faq.items.locations.answer' },
  { question: 'faq.items.payment.question', answer: 'faq.items.payment.answer' }
]
</script>

<template>
  <section id="faq" class="landing-block" aria-labelledby="faq-title">
    <div class="content-frame faq">
      <header class="faq-head" v-reveal>
        <h2 id="faq-title" class="two-tone faq-title">
          <span>{{ t('faq.titleBefore') }}</span>
          <span><AccentMark>{{ t('faq.titleAccent') }}</AccentMark></span>
        </h2>
        <BaseButton :href="supportUrl" variant="secondary" trail="arrow-up-right">{{ t('footer.links.support') }}</BaseButton>
      </header>

      <div class="faq-list" v-reveal style="--delay: .08s">
        <details v-for="question in questions" :key="question.question" class="faq-item" name="faq">
          <summary>
            <span>{{ t(question.question) }}</span>
            <i aria-hidden="true" />
          </summary>
          <p>{{ t(question.answer) }}</p>
        </details>
      </div>
    </div>
  </section>
</template>

<style scoped>
.faq {
  display: grid;
  grid-template-columns: minmax(0, .7fr) minmax(0, 1.3fr);
  align-items: start;
  gap: clamp(28px, 5vw, 72px);
}

.faq-head {
  position: sticky;
  top: calc(var(--header-height) + 24px);
  display: grid;
  justify-items: start;
  gap: 24px;
}

.faq-title {
  justify-items: start;
}

.faq-list {
  display: grid;
  gap: 8px;
}

.faq-item {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 18px;
  transition: border-color 260ms var(--ease), background-color 260ms var(--ease);
}

.faq-item[open] {
  background: var(--panel-raised);
  border-color: var(--line-dash);
  border-style: dashed;
}

.faq-item::details-content {
  block-size: 0;
  overflow: clip;
  transition: block-size 420ms var(--ease-out), content-visibility 420ms allow-discrete;
}

.faq-item[open]::details-content {
  block-size: auto;
  block-size: calc-size(auto, size);
}

.faq-item summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 20px 22px;
  font-family: var(--font-display);
  font-size: clamp(15px, 1.4vw, 18px);
  font-weight: 650;
  letter-spacing: -.02em;
  cursor: pointer;
  list-style: none;
}

.faq-item summary::-webkit-details-marker {
  display: none;
}

.faq-item summary i {
  position: relative;
  flex: none;
  width: 30px;
  height: 30px;
  border: 1px dashed var(--line-dash);
  border-radius: 50%;
  transition: transform 420ms var(--ease-out), background-color 260ms var(--ease), border-color 260ms var(--ease);
}

.faq-item summary i::before,
.faq-item summary i::after {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 12px;
  height: 1.5px;
  content: '';
  background: var(--fg);
  border-radius: 1px;
  transform: translate(-50%, -50%);
  transition: background-color 260ms var(--ease);
}

.faq-item summary i::after {
  transform: translate(-50%, -50%) rotate(90deg);
}

.faq-item[open] summary i {
  background: var(--plate);
  border-color: var(--plate);
  transform: rotate(135deg);
}

.faq-item[open] summary i::before,
.faq-item[open] summary i::after {
  background: var(--plate-ink);
}

.faq-item p {
  max-width: 62ch;
  padding: 0 22px 22px;
  color: var(--fg-secondary);
  font-size: 15px;
  text-wrap: pretty;
}

@media (hover: hover) and (pointer: fine) {
  .faq-item:not([open]):hover {
    border-color: var(--line-strong);
  }

  .faq-item:not([open]):hover summary i {
    border-color: rgb(255 255 255 / 72%);
    transform: rotate(90deg);
  }
}

@media (max-width: 860px) {
  .faq {
    grid-template-columns: minmax(0, 1fr);
  }

  .faq-head {
    position: static;
  }
}
</style>
