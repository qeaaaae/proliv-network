<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null

// accent-blue glow rising from the bottom edge; slowly breathes and drifts sideways
function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const time = t / 1000
  const sway = Math.sin(time * 0.4) * 0.08
  const breathe = 0.85 + 0.15 * Math.sin(time * 0.55)
  const cx = w * (0.5 + sway)
  const cy = h * 1.2

  const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, h * 1.15 * breathe)
  g.addColorStop(0, 'rgba(125, 211, 252, 0.34)')
  g.addColorStop(0.45, 'rgba(125, 211, 252, 0.13)')
  g.addColorStop(1, 'rgba(125, 211, 252, 0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, w, h)

  // softer white-ish core so it stays airy, not a neon blob
  const core = ctx.createRadialGradient(cx, h * 1.02, 0, cx, h * 1.02, h * 0.5 * breathe)
  core.addColorStop(0, 'rgba(214, 240, 254, 0.2)')
  core.addColorStop(1, 'rgba(125, 211, 252, 0)')
  ctx.fillStyle = core
  ctx.fillRect(0, 0, w, h)
}

onMounted(() => {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

  const resize = () => {
    const rect = el.getBoundingClientRect()
    const dpr = Math.min(devicePixelRatio || 1, 2)
    el.width = Math.max(1, Math.round(rect.width * dpr))
    el.height = Math.max(1, Math.round(rect.height * dpr))
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    if (reduced) draw(ctx, rect.width, rect.height, 0)
  }

  observer = new ResizeObserver(resize)
  observer.observe(el)
  resize()

  if (!reduced) {
    const loop = (t: number) => {
      const rect = el.getBoundingClientRect()
      draw(ctx, rect.width, rect.height, t)
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
  }
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  observer?.disconnect()
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
