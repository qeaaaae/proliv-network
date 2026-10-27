<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, useTemplateRef } from 'vue'

const props = withDefaults(defineProps<{ side?: 'left' | 'right' }>(), { side: 'left' })

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
const ready = ref(false)
let raf = 0
let last = 0
let running = false
let visible = false
let resizeObserver: ResizeObserver | null = null
let intersectionObserver: IntersectionObserver | null = null
let ctx: CanvasRenderingContext2D | null = null
let w = 0
let h = 0
let reduced = false

const GAP = 14
const FEATHER = 280

// large concentric rims radiating from the off-viewport edge, slow drift
function draw(t: number) {
  if (!ctx || !w || !h) return
  const right = props.side === 'right'
  ctx.clearRect(0, 0, w, h)

  const cols = Math.floor(w / GAP)
  const rows = Math.floor(h / GAP)
  if (cols < 4) return

  const feather = Math.min(FEATHER, h * 0.4)
  const midY = h / 2

  for (let i = 0; i < cols; i++) {
    const falloff = Math.pow(1 - i / cols, 1.6)
    const x = right ? w - GAP / 2 - i * GAP : GAP / 2 + i * GAP
    for (let j = 0; j < rows; j++) {
      const y = GAP / 2 + j * GAP
      const s = Math.min(1, y / feather, (h - y) / feather)
      const vfade = s * s * (3 - 2 * s)
      // wavelength ~2π/0.022 ≈ 285px - few large rims, crisp outline
      const ring = Math.max(0, Math.sin(Math.hypot(i * GAP, y - midY) * 0.022 - t * 1.1)) ** 16
      const alpha = falloff * vfade * (0.05 + 0.95 * ring)
      if (alpha < 0.03) continue
      ctx.fillStyle = `rgba(125, 211, 252, ${alpha.toFixed(3)})`
      ctx.beginPath()
      ctx.arc(x, y, 1 + ring * 1.3, 0, Math.PI * 2)
      ctx.fill()
    }
  }
}

function resize() {
  const el = canvas.value
  if (!el || !ctx) return
  const rect = el.getBoundingClientRect()
  const dpr = Math.min(devicePixelRatio || 1, 2)
  el.width = Math.max(1, Math.round(rect.width * dpr))
  el.height = Math.max(1, Math.round(rect.height * dpr))
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  w = rect.width
  h = rect.height
  draw(Date.now() / 1000)
}

// ~30fps cap, wall-clock time keeps ring phase continuous between mounts
function loop(now: number) {
  raf = requestAnimationFrame(loop)
  if (now - last < 33) return
  last = now
  draw(Date.now() / 1000)
}

function start() {
  if (running || reduced) return
  running = true
  raf = requestAnimationFrame(loop)
}

function stop() {
  running = false
  cancelAnimationFrame(raf)
  raf = 0
}

onMounted(() => {
  const el = canvas.value
  if (!el) return
  ctx = el.getContext('2d')
  if (!ctx) return
  reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

  resizeObserver = new ResizeObserver(() => {
    resize()
    if (reduced) draw(2)
    if (!ready.value) ready.value = true
  })
  resizeObserver.observe(el)
  resize()

  if (!reduced) {
    intersectionObserver = new IntersectionObserver((entries) => {
      const next = entries[entries.length - 1]?.isIntersecting ?? false
      if (next === visible) return
      visible = next
      visible ? start() : stop()
    })
    intersectionObserver.observe(el)
  } else {
    draw(2)
  }
  ready.value = true
})

onBeforeUnmount(() => {
  stop()
  resizeObserver?.disconnect()
  intersectionObserver?.disconnect()
})
</script>

<template>
  <canvas ref="canvas" class="dot-field" :class="[`dot-field--${props.side}`, { 'is-ready': ready }]" aria-hidden="true" />
</template>

<style scoped>
.dot-field {
  position: fixed;
  top: 0;
  height: 100vh;
  z-index: 0;
  width: 460px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 1.2s ease;
}

.dot-field.is-ready {
  opacity: 1;
}

.dot-field--left {
  left: 0;
}

.dot-field--right {
  right: 0;
}

@media (max-width: 900px) {
  .dot-field {
    display: none;
  }
}
</style>
