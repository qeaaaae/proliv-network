<script setup lang="ts">
import { Icon } from '@iconify/vue'
import { icons, type IconName } from '~/data/icons'

withDefaults(defineProps<{
  name: IconName
  size?: number | string
}>(), {
  size: 20
})
</script>

<template>
  <Icon
    class="app-icon"
    :ssr="true"
    :icon="icons[name]"
    :width="size"
    :height="size"
    aria-hidden="true"
  />
</template>

<style scoped>
.app-icon {
  display: block;
  flex: 0 0 auto;
}
</style>
