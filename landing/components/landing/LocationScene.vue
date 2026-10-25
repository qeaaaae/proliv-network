<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const props = defineProps<{ seed: string }>()

interface Building {
  x: number
  w: number
  h: number
  antenna: number
}

interface Beacon {
  x: number
  y: number
  phase: number
}

interface LitWindow {
  x: number
  y: number
  a: number
  dim: boolean
}

interface Drop {
  x: number
  y: number
  len: number
  speed: number
  alpha: number
}

interface Scene {
  back: Building[]
  front: Building[]
  windows: LitWindow[]
  beacons: Beacon[]
  glowX: number
}

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null
let scene: Scene | null = null
let drops: Drop[] = []

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

function makeScene(w: number, h: number): Scene {
  const rand = mulberry32(hashSeed(props.seed))
  const back: Building[] = []
  const front: Building[] = []
  const windows: LitWindow[] = []
  const beacons: Beacon[] = []

  let x = -12 - rand() * 24
  while (x < w + 12) {
    const bw = 20 + rand() * 28
    back.push({ x, w: bw, h: h * (0.16 + rand() * 0.3), antenna: 0 })
    x += bw + 5 + rand() * 12
  }

  x = -8 - rand() * 16
  while (x < w + 10) {
    const bw = 16 + rand() * 34
    const bh = h * (0.3 + rand() * 0.42)
    const antenna = rand() < 0.22 ? 5 + rand() * 9 : 0
    front.push({ x, w: bw, h: bh, antenna })
    if (antenna > 6 && rand() < 0.6) {
      beacons.push({ x: x + bw / 2, y: h - bh - antenna - 1.5, phase: rand() * Math.PI * 2 })
    }
    const cols = Math.floor((bw - 8) / 9)
    const rows = Math.floor((bh - 10) / 11)
    for (let c = 0; c < cols; c++) {
      for (let r = 0; r < rows; r++) {
        const lit = rand()
        if (lit < 0.08) {
          windows.push({ x: x + 5 + c * 9, y: h - bh + 6 + r * 11, a: 0.28 + rand() * 0.5, dim: false })
        } else if (lit < 0.2) {
          windows.push({ x: x + 5 + c * 9, y: h - bh + 6 + r * 11, a: 0.04 + rand() * 0.06, dim: true })
        }
      }
    }
    x += bw + 3 + rand() * 9
  }

  return { back, front, windows, beacons, glowX: 0.3 + rand() * 0.4 }
}

function makeDrops(): Drop[] {
  const rand = mulberry32(hashSeed(`${props.seed}:rain`))
  const list: Drop[] = []
  for (let i = 0; i < 48; i++) {
    list.push({
      x: rand(),
      y: rand(),
      len: 0.045 + rand() * 0.05,
      speed: 0.1 + rand() * 0.14,
      alpha: 0.05 + rand() * 0.13,
    })
  }
  return list
}

function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)

  const sky = ctx.createLinearGradient(0, 0, 0, h)
  sky.addColorStop(0, '#111418')
  sky.addColorStop(1, '#15181d')
  ctx.fillStyle = sky
  ctx.fillRect(0, 0, w, h)

  if (!scene) return
  const time = t / 1000

  const glow = ctx.createRadialGradient(w * scene.glowX, h * 1.05, 0, w * scene.glowX, h * 1.05, h * 0.95)
  glow.addColorStop(0, 'rgba(125, 211, 252, 0.11)')
  glow.addColorStop(1, 'rgba(125, 211, 252, 0)')
  ctx.fillStyle = glow
  ctx.fillRect(0, 0, w, h)

  ctx.fillStyle = '#181e27'
  for (const b of scene.back) ctx.fillRect(b.x, h - b.h, b.w, b.h)

  ctx.fillStyle = '#202834'
  for (const b of scene.front) {
    ctx.fillRect(b.x, h - b.h, b.w, b.h)
    if (b.antenna > 0) ctx.fillRect(b.x + b.w / 2 - 0.5, h - b.h - b.antenna, 1, b.antenna)
  }

  for (const win of scene.windows) {
    ctx.fillStyle = win.dim
      ? `rgba(206, 222, 238, ${win.a.toFixed(3)})`
      : `rgba(125, 211, 252, ${win.a.toFixed(3)})`
    ctx.fillRect(win.x, win.y, 3, 4)
  }

  for (const bc of scene.beacons) {
    const a = 0.3 + 0.5 * (Math.sin(time * 1.6 + bc.phase) * 0.5 + 0.5)
    ctx.fillStyle = `rgba(125, 211, 252, ${a.toFixed(3)})`
    ctx.beginPath()
    ctx.arc(bc.x, bc.y, 1.3, 0, Math.PI * 2)
    ctx.fill()
  }

  ctx.lineWidth = 1
  ctx.lineCap = 'round'
  for (const d of drops) {
    const py = ((d.y + time * d.speed) % 1) * h
    const px = d.x * w - py * 0.1
    const len = d.len * h
    ctx.strokeStyle = `rgba(168, 208, 238, ${d.alpha.toFixed(3)})`
    ctx.beginPath()
    ctx.moveTo(px, py)
    ctx.lineTo(px + len * 0.1, py + len)
    ctx.stroke()
  }
}

onMounted(() => {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
  drops = makeDrops()

  const resize = () => {
    const rect = el.getBoundingClientRect()
    const dpr = Math.min(devicePixelRatio || 1, 2)
    el.width = Math.max(1, Math.round(rect.width * dpr))
    el.height = Math.max(1, Math.round(rect.height * dpr))
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    scene = makeScene(rect.width, rect.height)
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
  <canvas ref="canvas" class="location-scene" aria-hidden="true" />
</template>

<style scoped>
.location-scene {
  display: block;
  width: 100%;
  height: 198px;
  border-radius: 16px;
  background: linear-gradient(180deg, #111418, #15181d);
}
</style>
