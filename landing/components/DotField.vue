<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const props = withDefaults(defineProps<{ side?: 'left' | 'right' }>(), { side: 'left' })

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null

const GAP = 21
const R = 1.5

// sonar ripples: concentric rings expanding from a point off the viewport edge
function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number, right: boolean) {
  ctx.clearRect(0, 0, w, h)
  const time = t / 1000
  const ex = right ? w + 30 : -30
  const ey = h * 0.42

  for (let y = GAP / 2; y < h; y += GAP) {
    for (let x = GAP / 2; x < w; x += GAP) {
      const d = Math.hypot(x - ex, y - ey)
      const r1 = Math.sin(d * 0.05 - time * 1.3) * 0.5 + 0.5
      const r2 = Math.sin(d * 0.019 - time * 0.55 + 1.7) * 0.5 + 0.5
      const wave = r1 * 0.68 + r2 * 0.32
      // soft fade only at extreme distance so arcs stay readable in narrow margins
      const fade = 0.35 + 0.65 * Math.min(1, 420 / Math.max(d, 60))
      const alpha = (0.12 + wave * 0.5) * fade
      if (alpha < 0.02) continue
      const rad = R + wave * 1.0
      ctx.fillStyle = `rgba(203, 214, 228, ${alpha.toFixed(3)})`
      ctx.beginPath()
      ctx.arc(x, y, rad, 0, Math.PI * 2)
      ctx.fill()
    }
  }
}

onMounted(() => {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return

  const right = props.side === 'right'
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

  const resize = () => {
    const rect = el.getBoundingClientRect()
    const dpr = Math.min(devicePixelRatio || 1, 2)
    el.width = Math.max(1, Math.round(rect.width * dpr))
    el.height = Math.max(1, Math.round(rect.height * dpr))
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    if (reduced) draw(ctx, rect.width, rect.height, 0, right)
  }

  observer = new ResizeObserver(resize)
  observer.observe(el)
  resize()

  if (!reduced) {
    const loop = (t: number) => {
      const rect = el.getBoundingClientRect()
      draw(ctx, rect.width, rect.height, t, right)
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
  <canvas ref="canvas" class="dot-field" :class="`dot-field--${props.side}`" aria-hidden="true" />
</template>

<style scoped>
.dot-field {
  position: fixed;
  top: 0;
  bottom: 0;
  z-index: -1;
  width: min(30vw, 380px);
  pointer-events: none;
}

.dot-field--left {
  left: 0;
}

.dot-field--right {
  right: 0;
}
</style>
