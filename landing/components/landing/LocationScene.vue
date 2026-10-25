<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const props = defineProps<{ seed: string }>()

interface Drop {
  x: number
  off: number
  len: number
  speed: number
  a: number
}

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null
let drops: Drop[] = []

// landmark alpha sampled per grid cell
let staticAlpha: Float32Array = new Float32Array(0)
let gridCols = 0
let gridRows = 0
let cellX = 0
let cellY = 0

const MASK_W = 400
const MASK_H = 170
// London Eye wheel center (mask coords)
const WCX = 0.24 * MASK_W
const WCY = MASK_H - 0.45 * MASK_H
const WHEEL_R = 0.33 * MASK_H
const WHEEL_SPEED = 0.14

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
// static parts only; moving parts are evaluated analytically per frame
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
    // London Eye - static rim + support legs; spokes rotate per-frame
    m.lineWidth = MASK_H * 0.03
    circ(0.24, 0.45, 0.33, false)
    circ(0.24, 0.45, 0.02)
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

    // St. Olaf's tall spire (flag on top waves per-frame)
    rect(0.26, 0.14, 0.05, 0.3)
    tri(0.245, 0.44, 0.285, 0.78, 0.325, 0.44)
    rect(0.282, 0.78, 0.006, 0.1)
    circ(0.285, 0.885, 0.01)

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

// London Eye: 12 bright cabins riding the rim + faint spokes, in mask units
function wheelAlpha(px: number, py: number, t: number): number {
  const dx = px - WCX
  const dy = py - WCY
  const r = Math.hypot(dx, dy)
  const rot = t * WHEEL_SPEED
  const ang = Math.atan2(dy, dx)

  // rotating capsules on the rim - big enough to read as moving cabins
  if (Math.abs(r - WHEEL_R) < 12) {
    let best = 1e9
    for (let k = 0; k < 12; k++) {
      const a = rot + (k * Math.PI) / 6
      const cx = WCX + Math.cos(a) * WHEEL_R
      const cy = WCY + Math.sin(a) * WHEEL_R
      best = Math.min(best, Math.hypot(px - cx, py - cy))
    }
    if (best < 11) return Math.min(1.2, (11 - best) / 7)
  }

  // faint rotating spokes
  if (r > 4 && r < WHEEL_R - 2) {
    let best = 1
    for (let k = 0; k < 8; k++) {
      let d = ang - (rot + (k * Math.PI) / 4)
      d = ((d + Math.PI) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2) - Math.PI
      const w = 3.2 / r
      best = Math.min(best, Math.abs(d) / w)
    }
    return Math.max(0, 1 - best) * 0.55
  }
  return 0
}

// waving pennant on St. Olaf's spire, in mask units
function flagAlpha(px: number, py: number, t: number): number {
  const fx = 0.285 * MASK_W
  const fy = MASK_H - 0.945 * MASK_H
  const LEN = 20
  if (px < fx + 1 || px > fx + LEN) return 0
  const u = (px - fx - 1) / LEN
  const wave = Math.sin(t * 2.6 + u * 5.5) * 3.4 * u
  const half = (1 - u) * 4.6 + 0.8
  return Math.abs(py - fy - wave) < half ? 0.9 : 0
}

function buildGrid(w: number, h: number) {
  gridCols = Math.max(1, Math.floor(w / 7))
  gridRows = Math.max(1, Math.floor(h / 7))
  cellX = (w - gridCols * 7) / 2 + 3.5
  cellY = (h - gridRows * 7) / 2 + 3.5

  const mask = document.createElement('canvas')
  mask.width = gridCols
  mask.height = gridRows
  const m = mask.getContext('2d')
  if (!m) return
  m.scale(gridCols / MASK_W, gridRows / MASK_H)
  paintLandmark(m, props.seed)
  const img = m.getImageData(0, 0, gridCols, gridRows).data
  staticAlpha = new Float32Array(gridCols * gridRows)
  for (let i = 0; i < staticAlpha.length; i++) {
    staticAlpha[i] = img[i * 4 + 3] / 255
  }

  const rand = mulberry32(hashSeed(`${props.seed}:rain`))
  drops = []
  for (let i = 0; i < 30; i++) {
    drops.push({
      x: rand() * w,
      off: rand() * h,
      len: 8 + rand() * 16,
      speed: 22 + rand() * 30,
      a: 0.04 + rand() * 0.07,
    })
  }
}

function maskAt(col: number, row: number, t: number): number {
  let a = staticAlpha[row * gridCols + col]
  // cell position in mask units
  const mx = ((col + 0.5) / gridCols) * MASK_W
  const my = ((row + 0.5) / gridRows) * MASK_H
  if (props.seed === 'gb') {
    const s = wheelAlpha(mx, my, t)
    if (s > a) a = s
  } else if (props.seed === 'ee') {
    const f = flagAlpha(mx, my, t)
    if (f > a) a = f
  }
  return Math.min(a, 1.2) // capsules exceed 1 -> tinted accent in draw
}

function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const sweep = ((t * 0.14) % 1.6) - 0.3

  for (let row = 0; row < gridRows; row++) {
    const n = (row + 0.5) / gridRows
    for (let col = 0; col < gridCols; col++) {
      const i = (col + 0.5) / gridCols
      const o = maskAt(col, row, t)
      const u = Math.exp(-(((i - sweep) / 0.06) ** 2))
      const alpha = Math.max(0.05 + u * 0.06 * (1 - n * 0.4), o * (0.74 + u * 0.26))
      // capsules (very bright dots) render in brand accent so motion reads clearly
      ctx.fillStyle =
        o > 1.0
          ? `rgba(125, 211, 252, ${Math.min(1, alpha * 1.15).toFixed(3)})`
          : `rgba(240, 246, 252, ${alpha.toFixed(3)})`
      ctx.beginPath()
      ctx.arc(cellX + col * 7, cellY + row * 7, o > 0.55 ? 1.45 : 1 + o * 0.5, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  // brand rain streaks
  for (const d of drops) {
    const y = ((d.off + t * d.speed) % (h + d.len * 2)) - d.len
    const slant = d.len * 0.18
    const g = ctx.createLinearGradient(d.x, y - d.len, d.x + slant, y)
    g.addColorStop(0, 'rgba(125, 211, 252, 0)')
    g.addColorStop(1, `rgba(125, 211, 252, ${d.a})`)
    ctx.strokeStyle = g
    ctx.lineWidth = 1.1
    ctx.beginPath()
    ctx.moveTo(d.x, y - d.len)
    ctx.lineTo(d.x + slant, y)
    ctx.stroke()
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
    buildGrid(rect.width, rect.height)
    if (reduced) draw(ctx, rect.width, rect.height, 20)
  }

  observer = new ResizeObserver(resize)
  observer.observe(el)
  resize()

  if (!reduced) {
    const loop = (ts: number) => {
      const rect = el.getBoundingClientRect()
      draw(ctx, rect.width, rect.height, ts / 1000)
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
  height: 100%;
}
</style>
