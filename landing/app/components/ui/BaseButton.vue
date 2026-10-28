<script setup lang="ts">
import type { IconName } from '~/data/icons'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{
  href: string
  variant?: 'primary' | 'secondary' | 'ghost' | 'telegram'
  size?: 'regular' | 'small'
  icon?: IconName
  trail?: IconName | false
}>(), {
  variant: 'primary',
  size: 'regular',
  trail: 'arrow-right'
})

const shifts: Partial<Record<IconName, string>> = {
  'arrow-down': 'translateY(3px)',
  'arrow-up-right': 'translate(2px, -2px)'
}

const { navigate } = useTargetNavigation()

function onClick() {
  void navigate(props.href)
}
</script>

<template>
  <button
    type="button"
    class="base-button"
    :class="[`base-button--${variant}`, { 'base-button--small': size === 'small' }]"
    :style="trail && shifts[trail] ? { '--trail-shift': shifts[trail] } : undefined"
    @click="onClick"
  >
    <AppIcon v-if="icon" :name="icon" :size="18" />
    <span><slot /></span>
    <span v-if="trail" class="base-button-trail" aria-hidden="true">
      <AppIcon :name="trail" :size="16" />
    </span>
    <span v-if="variant !== 'telegram'" class="base-button-flight" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="16" height="16">
        <path d="M22 12c0-.8-1.4-1.5-3-1.5h-5L8 2H5l4 8.5H4L2 7H.5l1 5-1 5H2l2-3.5h5L5 22h3l6-8.5h5c1.6 0 3-.7 3-1.5Z" />
      </svg>
    </span>
  </button>
</template>
