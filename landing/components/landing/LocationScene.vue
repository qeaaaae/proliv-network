<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const props = defineProps<{ seed: string }>()

interface Dot {
  x: number
  y: number
  r: number
  base: number
  phase: number
  speed: number
  twinkle: boolean
  born: number
  bornY: number
}

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null
let dots: Dot[] = []

const MASK_W = 400
const MASK_H = 170

function hashSeed(seed: string): number {
  let h = 2166136261
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function mulberry32(a: number): () => number {
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// landmarks in normalized coords (x: 0..1 left->right, y: 0..1 bottom->top)
function paintLandmark(m: CanvasRenderingContext2D, seed: string) {
  const X = (v: number) => v * MASK_W
  const Y = (v: number) => MASK_H - v * MASK_H

  m.fillStyle = '#fff'
  m.strokeStyle = '#fff'
  m.lineCap = 'round'

  const rect = (x: number, y: number, w: number, h: number) =>
    m.fillRect(X(x), Y(y + h), X(x + w) - X(x), Y(y) - Y(y + h))
  const tri = (x1: number, y1: number, x2: number, y2: number, x3: number, y3: number) => {
    m.beginPath()
    m.moveTo(X(x1), Y(y1))
    m.lineTo(X(x2), Y(y2))
    m.lineTo(X(x3), Y(y3))
    m.closePath()
    m.fill()
  }
  const circ = (x: number, y: number, r: number, fill = true) => {
    m.beginPath()
    m.arc(X(x), Y(y), r * MASK_H, 0, Math.PI * 2)
    fill ? m.fill() : m.stroke()
  }

  if (seed === 'gb') {
    // London Eye - big wheel on the left
    m.lineWidth = MASK_H * 0.035
    circ(0.24, 0.45, 0.33, false)
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2
      m.lineWidth = MASK_H * 0.012
      m.beginPath()
      m.moveTo(X(0.24), Y(0.45))
      m.lineTo(X(0.24) + Math.cos(a) * 0.33 * MASK_H, Y(0.45) - Math.sin(a) * 0.33 * MASK_H)
      m.stroke()
    }
    m.lineWidth = MASK_H * 0.03
    m.beginPath()
    m.moveTo(X(0.19), Y(0))
    m.lineTo(X(0.24), Y(0.45))
    m.lineTo(X(0.29), Y(0))
    m.stroke()

    // Elizabeth Tower
    rect(0.56, 0, 0.075, 0.62)
    tri(0.54, 0.62, 0.5975, 0.82, 0.655, 0.62)
    rect(0.594, 0.82, 0.007, 0.05)
    circ(0.5975, 0.5, 0.045)

    // Gherkin
    m.beginPath()
    m.ellipse(X(0.78), Y(0.34), MASK_W * 0.055, MASK_H * 0.34, 0, 0, Math.PI * 2)
    m.fill()

    // low skyline
    rect(0.44, 0, 0.09, 0.3)
    rect(0.66, 0, 0.08, 0.26)
    rect(0.87, 0, 0.1, 0.32)
    rect(0.05, 0, 0.12, 0.22)
    rect(0, 0, 1, 0.045)
  } else if (seed === 'ee') {
    // Tallinn old town: town wall + church spires
    rect(0, 0, 1, 0.14)
    for (let i = 0; i < 22; i++) {
      rect(i * 0.048 + 0.012, 0.14, 0.024, 0.035)
    }

    // St. Olaf's tall spire
    rect(0.26, 0.14, 0.05, 0.3)
    tri(0.245, 0.44, 0.285, 0.78, 0.325, 0.44)
    rect(0.282, 0.78, 0.006, 0.06)
    circ(0.285, 0.86, 0.012)

    // Dome church towers
    rect(0.55, 0.14, 0.07, 0.22)
    m.beginPath()
    m.arc(X(0.585), Y(0.36), 0.035 * MASK_W * 0.55, Math.PI, 0)
    m.fill()
    tri(0.545, 0.365, 0.585, 0.56, 0.625, 0.365)

    rect(0.72, 0.14, 0.055, 0.28)
    tri(0.705, 0.42, 0.7475, 0.62, 0.79, 0.42)
    rect(0.7445, 0.62, 0.006, 0.04)

    // houses
    tri(0.1, 0.14, 0.16, 0.26, 0.22, 0.14)
    tri(0.4, 0.14, 0.46, 0.3, 0.52, 0.14)
    tri(0.84, 0.14, 0.9, 0.25, 0.96, 0.14)
  } else {
    // generic skyline
    const rand = mulberry32(hashSeed(seed))
    let x = 0.02
    while (x < 0.98) {
      const w = 0.05 + rand() * 0.09
      const h = 0.15 + rand() * 0.4
      rect(x, 0, w, h)
      if (rand() < 0.3) rect(x + w / 2 - 0.004, h, 0.008, 0.06)
      x += w + 0.02 + rand() * 0.05
    }
    rect(0, 0, 1, 0.045)
  }
}

function buildDots(w: number, h: number) {
  const mask = document.createElement('canvas')
  mask.width = MASK_W
  mask.height = MASK_H
  const m = mask.getContext('2d')
  if (!m) return
  paintLandmark(m, props.seed)
  const data = m.getImageData(0, 0, MASK_W, MASK_H).data

  const rand = mulberry32(hashSeed(`${props.seed}:dots`))
  const step = 7
  const sx = w / MASK_W
  const sy = h / MASK_H
  const list: Dot[] = []

  for (let gy = 0; gy < MASK_H; gy += step) {
    for (let gx = 0; gx < MASK_W; gx += step) {
      if (data[(gy * MASK_W + gx) * 4 + 3] > 100) {
        const twinkle = rand() < 0.28
        list.push({
          x: (gx + step / 2) * sx,
          y: (gy + step / 2) * sy,
          r: 1.5 + rand() * 0.7,
          base: 0.45 + rand() * 0.45,
          phase: rand() * Math.PI * 2,
          speed: 0.6 + rand() * 1.4,
          twinkle,
          born: (gx / MASK_W) * 1.4 + rand() * 0.25,
          bornY: 8 + rand() * 10,
        })
      }
    }
  }
  dots = list
}

const FADE = 0.7

function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const time = t / 1000
  for (const d of dots) {
    const p = Math.min(Math.max((time - d.born) / FADE, 0), 1)
    if (p <= 0) continue
    const ease = 1 - (1 - p) * (1 - p) * (1 - p)
    const drift = (1 - ease) * d.bornY
    const a = d.twinkle ? d.base * (0.35 + 0.65 * (Math.sin(time * d.speed + d.phase) * 0.5 + 0.5)) : d.base
    ctx.fillStyle = `rgba(226, 232, 240, ${(a * ease).toFixed(3)})`
    ctx.beginPath()
    ctx.arc(d.x, d.y + drift, d.r * (0.5 + 0.5 * ease), 0, Math.PI * 2)
    ctx.fill()
  }
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
    buildDots(rect.width, rect.height)
    if (reduced) draw(ctx, rect.width, rect.height, 10000)
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
  <canvas ref="canvas" class="location-scene" aria-hidden="true" />
</template>

<style scoped>
.location-scene {
  display: block;
  width: 100%;
  height: 198px;
  border-radius: 16px;
  background: linear-gradient(180deg, #0b0d10, #101318);
}
</style>
