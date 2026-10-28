<script setup lang="ts">
import type { LegalDocument } from '~/data/legal'

defineProps<{
  document: LegalDocument
}>()
</script>

<template>
  <main class="legal-page">
    <div class="legal-page__frame">
      <header
        class="legal-intro"
        :class="{ 'legal-intro--long': document.id === 'personal-data' || document.id === 'privacy' }"
      >
        <h1 v-reveal>{{ document.label }}</h1>
        <p class="legal-intro__summary" v-reveal style="--delay: .08s">{{ document.summary }}</p>
        <p class="legal-intro__updated label" v-reveal style="--delay: .16s">{{ document.updated }}</p>
      </header>

      <div class="legal-layout card" v-reveal style="--delay: .24s">
        <article class="legal-document">
          <section
            v-for="section in document.sections"
            :id="section.id"
            :key="section.id"
            class="legal-section"
          >
            <h2>{{ section.title }}</h2>
            <p v-for="paragraph in section.paragraphs" :key="paragraph">
              {{ paragraph }}
            </p>
            <ul v-if="section.bullets?.length">
              <li v-for="bullet in section.bullets" :key="bullet">
                {{ bullet }}
              </li>
            </ul>
          </section>
        </article>
      </div>
    </div>
  </main>
</template>

<style scoped>
.legal-page {
  position: relative;
  padding: clamp(40px, 6vw, 72px) var(--content-gutter) 96px;
}

.legal-page__frame {
  width: min(100%, 880px);
  margin-inline: auto;
}

.legal-intro {
  display: grid;
  gap: 14px;
}

.legal-intro h1 {
  color: var(--fg);
  font-size: clamp(28px, 4vw, 46px);
  font-weight: 800;
  line-height: 1.06;
  letter-spacing: -.04em;
  text-wrap: balance;
}

.legal-intro--long h1 {
  font-size: clamp(24px, 3.2vw, 38px);
}

.legal-intro__summary {
  max-width: 62ch;
  color: var(--fg-secondary);
  font-size: clamp(15px, 1.6vw, 17px);
  line-height: 1.6;
}

.legal-layout {
  margin-top: 32px;
  padding: clamp(24px, 4vw, 48px);
}

.legal-section {
  padding-bottom: 34px;
  scroll-margin-top: calc(var(--header-height) + 16px);
}

.legal-section + .legal-section {
  padding-top: 34px;
  border-top: 1px dashed var(--line-strong);
}

.legal-section:last-child {
  padding-bottom: 0;
}

.legal-section h2 {
  color: var(--fg);
  font-size: clamp(17px, 2vw, 22px);
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -.03em;
  text-wrap: balance;
}

.legal-section p,
.legal-section li {
  color: var(--fg-secondary);
  font-size: 16px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.legal-section p {
  margin-top: 14px;
}

.legal-section ul {
  display: grid;
  gap: 10px;
  margin-top: 16px;
  padding-left: 1.2em;
  list-style: square;
}

.legal-section li::marker {
  color: var(--fg-tertiary);
}

@media (max-width: 540px) {
  .legal-section p,
  .legal-section li {
    font-size: 15px;
    line-height: 1.72;
  }
}
</style>
