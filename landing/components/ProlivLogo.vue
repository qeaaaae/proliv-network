<script setup lang="ts">
import { useId } from 'vue'

withDefaults(defineProps<{ height?: number }>(), { height: 28 })

const VB_W = 116
const VB_H = 32
const uid = useId()
const gradId = `proliv-drop-${uid}`
</script>

<template>
  <svg
    class="proliv-logo"
    :width="(height * VB_W) / VB_H"
    :height="height"
    :viewBox="`0 0 ${VB_W} ${VB_H}`"
    fill="none"
    role="img"
    aria-label="Proliv Network"
  >
    <defs>
      <linearGradient :id="gradId" x1="16" y1="4" x2="16" y2="27" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#a5e2fd" />
        <stop offset="1" stop-color="#38bdf8" />
      </linearGradient>
    </defs>
    <path
      d="M16 4c4.2 5.6 8 10.2 8 15a8 8 0 1 1-16 0c0-4.8 3.8-9.4 8-15z"
      :fill="`url(#${gradId})`"
    />
    <ellipse
      cx="12.6"
      cy="18.2"
      rx="1.7"
      ry="2.7"
      fill="#ffffff"
      opacity="0.35"
      transform="rotate(-18 12.6 18.2)"
    />
    <text x="31" y="22.5" class="proliv-logo__word">Proliv</text>
  </svg>
</template>

<style scoped>
.proliv-logo {
  display: inline-block;
  vertical-align: middle;
}

.proliv-logo__word {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.2px;
  fill: var(--text);
}
</style>
