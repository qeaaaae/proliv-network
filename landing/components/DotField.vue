<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null

const GAP = 22
const R = 1.5

// sonar ripples: concentric rings expanding from a point off the canvas edge,
// like the side decorations on ranteis.eu
function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number, side: 1 | -1) {
  ctx.clearRect(0, 0, w, h)
  const time = t / 1000
  // emitter sits just outside the frame edge, vertically centered
  const ex = side === -1 ? -40 : w + 40
  const ey = h * 0.5

  for (let y = GAP / 2; y < h; y += GAP) {
    for (let x = GAP / 2; x < w; x += GAP) {
      const d = Math.hypot(x - ex, y - ey)
      // two ring trains at different speeds => organic interference
      const r1 = Math.sin(d * 0.055 - time * 1.35) * 0.5 + 0.5
      const r2 = Math.sin(d * 0.021 - time * 0.6 + 1.7) * 0.5 + 0.5
      const wave = r1 * 0.7 + r2 * 0.3
      const fade = Math.min(1, 520 / Math.max(d, 60)) // fade far from emitter
      const alpha = (0.05 + wave * 0.3) * fade
      if (alpha < 0.02) continue
      const rad = R + wave * 0.7
      ctx.fillStyle = `rgba(196, 208, 222, ${alpha.toFixed(3)})`
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

  const side: 1 | -1 = el.classList.contains('dot-field--right') ? 1 : -1
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

  const resize = () => {
    const rect = el.getBoundingClientRect()
    const dpr = Math.min(devicePixelRatio || 1, 2)
    el.width = Math.max(1, Math.round(rect.width * dpr))
    el.height = Math.max(1, Math.round(rect.height * dpr))
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    if (reduced) draw(ctx, rect.width, rect.height, 0, side)
  }

  observer = new ResizeObserver(resize)
  observer.observe(el)
  resize()

  if (!reduced) {
    const loop = (t: number) => {
      const rect = el.getBoundingClientRect()
      draw(ctx, rect.width, rect.height, t, side)
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
  <canvas ref="canvas" class="dot-field" aria-hidden="true" />
</template>
