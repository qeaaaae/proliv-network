<script setup lang="ts">
defineProps<{
  title: string
  lead?: string
  updated?: string
}>()
</script>

<template>
  <main class="doc-page">
    <div class="content-frame doc-frame">
      <div class="doc-sheet sheet">
        <header class="doc-head">
          <div class="doc-topline">
            <NuxtLink to="/" class="doc-brand" aria-label="Proliv Network">
              <ProlivLogo />
            </NuxtLink>
            <NuxtLink to="/" class="doc-back">На главную</NuxtLink>
          </div>
          <h1 class="doc-title">{{ title }}</h1>
          <p v-if="lead" class="doc-lead">{{ lead }}</p>
          <p v-if="updated" class="doc-updated">Редакция от {{ updated }}</p>
        </header>
        <article class="doc-body">
          <slot />
        </article>
      </div>
    </div>
  </main>
</template>

<style scoped>
.doc-page {
  flex: 1;
  padding: 40px 0 96px;
}

.doc-frame {
  max-width: 820px;
}

.doc-sheet {
  padding: clamp(24px, 4vw, 48px);
}

.doc-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.doc-brand {
  display: inline-flex;
  color: var(--text);
}

.doc-back {
  color: var(--muted);
  font-size: 14px;
  transition: color 0.18s ease;
}

.doc-back:hover {
  color: var(--accent);
}

.doc-title {
  margin-top: 40px;
  font-family: var(--font-display);
  font-size: clamp(28px, 4vw, 34px);
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

.doc-lead {
  margin-top: 14px;
  color: var(--fg-secondary);
  font-size: 15px;
}

.doc-updated {
  margin-top: 12px;
  color: var(--muted);
  font-size: 14px;
}

.doc-body {
  margin-top: 36px;
}

.doc-body > :deep(:first-child) {
  margin-top: 0;
}

.doc-body :deep(h2) {
  margin-top: 28px;
  margin-bottom: 10px;
  font-size: 19px;
  font-weight: 600;
  line-height: 1.35;
}

.doc-body :deep(p),
.doc-body :deep(li) {
  color: #c8cfd8;
  font-size: 15px;
  line-height: 1.65;
}

.doc-body :deep(p) {
  margin-top: 10px;
}

.doc-body :deep(ul) {
  margin-top: 10px;
  padding-left: 20px;
  list-style: disc;
}

.doc-body :deep(li) {
  margin: 6px 0;
}

.doc-body :deep(li::marker) {
  color: var(--muted);
}

.doc-body :deep(a) {
  color: var(--accent);
  transition: color 0.18s ease;
}

.doc-body :deep(a):hover {
  color: #a5e2fd;
}

.doc-body :deep(strong) {
  color: var(--text);
  font-weight: 600;
}

.doc-body :deep(.doc-draft) {
  margin-top: 0;
  margin-bottom: 8px;
  padding: 12px 16px;
  font-size: 13px;
  color: var(--muted);
  background: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius-control);
}
</style>
