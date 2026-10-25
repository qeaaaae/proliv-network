<script setup lang="ts">
import { onMounted, useTemplateRef } from 'vue'

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')

onMounted(() => {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return

  const render = () => {
    const rect = el.getBoundingClientRect()
    const dpr = Math.min(devicePixelRatio || 1, 2)
    el.width = Math.max(1, Math.round(rect.width * dpr))
    el.height = Math.max(1, Math.round(rect.height * dpr))
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    const w = rect.width
    const h = rect.height
    ctx.clearRect(0, 0, w, h)

    // soft white bloom rising from the bottom edge, like ranteis
    const g = ctx.createRadialGradient(w * 0.5, h * 1.2, 0, w * 0.5, h * 1.2, h * 1.15)
    g.addColorStop(0, 'rgba(255, 255, 255, 0.32)')
    g.addColorStop(0.45, 'rgba(255, 255, 255, 0.12)')
    g.addColorStop(1, 'rgba(255, 255, 255, 0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, w, h)

    const core = ctx.createRadialGradient(w * 0.5, h * 1.02, 0, w * 0.5, h * 1.02, h * 0.55)
    core.addColorStop(0, 'rgba(255, 255, 255, 0.22)')
    core.addColorStop(1, 'rgba(255, 255, 255, 0)')
    ctx.fillStyle = core
    ctx.fillRect(0, 0, w, h)
  }

  render()
  const ro = new ResizeObserver(render)
  ro.observe(el)
})
</script>

<template>
  <canvas ref="canvas" class="light-flare" aria-hidden="true" />
</template>

<style scoped>
.light-flare {
  position: absolute;
  inset: auto 0 0;
  width: 100%;
  height: 65%;
  pointer-events: none;
}
</style>
