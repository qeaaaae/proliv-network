<script setup lang="ts">
const props = defineProps<{ target: string }>()

const { navigate } = useTargetNavigation()

function onClick() {
  void navigate(props.target)
}
</script>

<template>
  <button type="button" @click="onClick">
    <slot />
  </button>
</template>
