<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { brandLogoUrl } from '~/data/assets'
import BaseButton from '~/components/ui/BaseButton.vue'
import NavigationButton from '~/components/ui/NavigationButton.vue'

defineProps<{ actionLabel: string, actionTarget: string }>()

const { t } = useI18n()
const scrolled = ref(false)

function update() {
  scrolled.value = window.scrollY > 8
}

onMounted(() => {
  update()
  window.addEventListener('scroll', update, { passive: true })
})

onBeforeUnmount(() => window.removeEventListener('scroll', update))
</script>

<template>
  <header class="site-header" :class="{ 'is-scrolled': scrolled }">
    <div class="header-inner">
      <NavigationButton class="header-logo" target="/" :aria-label="t('brand.name')">
        <img :src="brandLogoUrl" alt="" width="124" height="34">
      </NavigationButton>
      <BaseButton class="header-action" :href="actionTarget" variant="secondary" size="small">{{ actionLabel }}</BaseButton>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  z-index: var(--layer-header);
  top: 0;
  height: var(--header-height);
  transition: background-color 320ms var(--ease), border-color 320ms var(--ease), backdrop-filter 320ms var(--ease);
  border-bottom: 1px solid transparent;
}

.site-header.is-scrolled {
  background: rgb(10 12 14 / 72%);
  border-bottom-color: var(--line);
  backdrop-filter: blur(14px) saturate(1.1);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(100% - var(--content-gutter) * 2, var(--content-max));
  height: 100%;
  margin-inline: auto;
}

.header-logo {
  justify-self: start;
}

.header-logo img {
  display: block;
  width: auto;
  height: 34px;
}

.header-action {
  justify-self: end;
}

@media (max-width: 720px) {
  .header-logo img {
    height: 28px;
  }
}
</style>
