<script setup lang="ts">
import { onBeforeUnmount, onMounted, useTemplateRef } from 'vue'

const canvas = useTemplateRef<HTMLCanvasElement>('canvas')
let raf = 0
let observer: ResizeObserver | null = null

interface Packet {
  off: number
  speed: number
  size: number
  lane: number
}
let packets: Packet[] = []

// wire path: straight line, a smooth bump rising in the middle, back down,
// then it fans out into a burst on the right - like truecost's tariff cable
function pathPoint(u: number, w: number, h: number): { x: number; y: number } {
  const y0 = h * 0.62
  const x = u * w
  // gaussian bump centered at u=0.62
  const bump = Math.exp(-(((u - 0.62) / 0.09) ** 2)) * h * 0.42
  return { x, y: y0 - bump }
}

function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const time = t / 1000

  // dotted wire - sample the path, faint dots
  const steps = Math.floor(w / 9)
  for (let i = 0; i <= steps; i++) {
    const u = i / steps
    const p = pathPoint(u, w, h)
    const edge = u < 0.86 ? 0.16 : 0.16 * (1 - (u - 0.86) / 0.14)
    if (edge <= 0.02) continue
    ctx.fillStyle = `rgba(200, 210, 222, ${edge.toFixed(3)})`
    ctx.fillRect(p.x - 1.4, p.y - 1.4, 2.8, 2.8)
  }

  // endpoint node where the wire terminates - small square beacon, pulsing ring
  const end = pathPoint(0.98, w, h)
  ctx.fillStyle = 'rgba(125, 211, 252, 0.9)'
  ctx.fillRect(end.x - 3, end.y - 3, 6, 6)
  const ring = (time * 0.7) % 1
  const ringR = 6 + ring * 16
  const ringA = 0.5 * (1 - ring)
  ctx.strokeStyle = `rgba(125, 211, 252, ${ringA.toFixed(3)})`
  ctx.lineWidth = 1.5
  ctx.strokeRect(end.x - ringR / 2, end.y - ringR / 2, ringR, ringR)

  // packets riding the wire; past the node they burst into a spark fan
  const burstDirs = [
    [1, 0],
    [1, -0.55],
    [1, 0.55],
    [0.65, -1],
    [0.65, 1],
  ]
  for (const pk of packets) {
    const u = (time * pk.speed + pk.off) % 1
    const p = pathPoint(u, w, h)
    // trail: 5 fading dots behind
    for (let k = 4; k >= 0; k--) {
      const tu = u - k * 0.006
      if (tu < 0) continue
      const tp = pathPoint(tu, w, h)
      const a = (0.95 - k * 0.18) * (u > 0.96 ? 0 : 1)
      const s = pk.size - k * 0.4
      if (a <= 0 || s <= 0) continue
      ctx.fillStyle = `rgba(125, 211, 252, ${a.toFixed(3)})`
      ctx.fillRect(tp.x - s / 2, tp.y + pk.lane - s / 2, s, s)
    }
    // burst sparks after reaching the node
    if (u > 0.96) {
      const e = (u - 0.96) / 0.04
      for (const [dx, dy] of burstDirs) {
        const sa = (1 - e) * 0.9
        ctx.fillStyle = `rgba(125, 211, 252, ${sa.toFixed(3)})`
        const ss = Math.max(1.4, pk.size * (1 - e * 0.6))
        ctx.fillRect(end.x + dx * e * 42 - ss / 2, end.y + dy * e * 34 - ss / 2, ss, ss)
      }
    }
  }
}

function seedPackets() {
  packets = []
  for (let i = 0; i < 11; i++) {
    packets.push({
      off: i / 11 + (i % 3) * 0.017,
      speed: 0.055 + (i % 4) * 0.012,
      size: 3.4 + (i % 3) * 0.7,
      lane: 0,
    })
  }
}

onMounted(() => {
  const el = canvas.value
  if (!el) return
  const ctx = el.getContext('2d')
  if (!ctx) return

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
  seedPackets()

  const resize = () => {
    const rect = el.getBoundingClientRect()
    const dpr = Math.min(devicePixelRatio || 1, 2)
    el.width = Math.max(1, Math.round(rect.width * dpr))
    el.height = Math.max(1, Math.round(rect.height * dpr))
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    if (reduced) draw(ctx, rect.width, rect.height, 5000)
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
  <canvas ref="canvas" class="packet-flow" aria-hidden="true" />
</template>

<style scoped>
.packet-flow {
  display: block;
  width: 100%;
  height: 110px;
}
</style>
