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

interface Mote {
  x: number
  y: number
  r: number
  speed: number
  phase: number
}

let packets: Packet[] = []
let motes: Mote[] = []

// wire path: straight line, a smooth bump rising in the middle, back down,
// then it fans out into a burst on the right - like truecost's tariff cable
function pathPoint(u: number, w: number, h: number): { x: number; y: number } {
  const y0 = h * 0.58
  const x = u * w
  // gaussian bump centered at u=0.62
  const bump = Math.exp(-(((u - 0.62) / 0.09) ** 2)) * h * 0.4
  return { x, y: y0 - bump }
}

function draw(ctx: CanvasRenderingContext2D, w: number, h: number, t: number) {
  ctx.clearRect(0, 0, w, h)
  const time = t / 1000

  // ambient motes - dust drifting up around the cable
  for (const m of motes) {
    const my = ((m.y - time * m.speed) % 1 + 1) % 1
    const mx = m.x + Math.sin(time * 0.8 + m.phase) * 0.012
    const a = 0.1 + 0.14 * Math.sin(time * 1.7 + m.phase * 3)
    if (a <= 0.02) continue
    ctx.fillStyle = `rgba(125, 211, 252, ${a.toFixed(3)})`
    ctx.beginPath()
    ctx.arc(mx * w, my * h, m.r, 0, Math.PI * 2)
    ctx.fill()
  }

  // single wire, dotted
  const steps = Math.floor(w / 9)
  for (let i = 0; i <= steps; i++) {
    const u = i / steps
    const p = pathPoint(u, w, h)
    const edge = u < 0.86 ? 0.18 : 0.18 * (1 - (u - 0.86) / 0.14)
    if (edge <= 0.02) continue
    ctx.fillStyle = `rgba(200, 210, 222, ${edge.toFixed(3)})`
    ctx.fillRect(p.x - 1.4, p.y - 1.4, 2.8, 2.8)
  }

  const gate = pathPoint(0.62, w, h)

  // soft halo under the encryption gate, breathing
  const haloA = 0.05 + 0.03 * Math.sin(time * 1.6)
  const grad = ctx.createRadialGradient(gate.x, gate.y, 2, gate.x, gate.y, 52)
  grad.addColorStop(0, `rgba(125, 211, 252, ${haloA.toFixed(3)})`)
  grad.addColorStop(1, 'rgba(125, 211, 252, 0)')
  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.arc(gate.x, gate.y, 52, 0, Math.PI * 2)
  ctx.fill()

  // ripple rings each time a packet crosses the gate
  for (const pk of packets) {
    const u = (time * pk.speed + pk.off) % 1
    if (u > 0.62 && u < 0.7) {
      const e = (u - 0.62) / 0.08
      ctx.strokeStyle = `rgba(125, 211, 252, ${((1 - e) * 0.45).toFixed(3)})`
      ctx.lineWidth = 1.2
      ctx.beginPath()
      ctx.arc(gate.x, gate.y, 17 + e * 30, 0, Math.PI * 2)
      ctx.stroke()
    }
  }

  // encryption gate on the bump apex: bigger chip, breathing glow, tick marks
  const glow = 0.32 + 0.24 * Math.sin(time * 1.6)
  ctx.strokeStyle = `rgba(125, 211, 252, ${glow.toFixed(3)})`
  ctx.lineWidth = 1.6
  ctx.fillStyle = 'rgba(15, 15, 15, 0.92)'
  ctx.beginPath()
  ctx.roundRect(gate.x - 16, gate.y - 16, 32, 32, 10)
  ctx.fill()
  ctx.stroke()
  // little tick marks around the chip
  for (let k = 0; k < 8; k++) {
    const ang = (k / 8) * Math.PI * 2 + time * 0.35
    const r1 = 22
    const r2 = 26
    ctx.strokeStyle = `rgba(125, 211, 252, ${(glow * 0.5).toFixed(3)})`
    ctx.lineWidth = 1.2
    ctx.beginPath()
    ctx.moveTo(gate.x + Math.cos(ang) * r1, gate.y + Math.sin(ang) * r1)
    ctx.lineTo(gate.x + Math.cos(ang) * r2, gate.y + Math.sin(ang) * r2)
    ctx.stroke()
  }
  // lock glyph
  ctx.strokeStyle = `rgba(125, 211, 252, ${(glow + 0.4).toFixed(3)})`
  ctx.lineWidth = 1.8
  ctx.beginPath()
  ctx.arc(gate.x, gate.y - 1.5, 4.6, Math.PI, 0)
  ctx.stroke()
  ctx.beginPath()
  ctx.roundRect(gate.x - 7, gate.y - 1.5, 14, 11, 3)
  ctx.stroke()
  ctx.fillStyle = `rgba(125, 211, 252, ${(glow + 0.4).toFixed(3)})`
  ctx.beginPath()
  ctx.arc(gate.x, gate.y + 3.5, 1.6, 0, Math.PI * 2)
  ctx.fill()

  // endpoint node: square beacon, dual pulse rings, slow rotating dashes
  const end = pathPoint(0.98, w, h)
  ctx.fillStyle = 'rgba(125, 211, 252, 0.95)'
  ctx.fillRect(end.x - 4, end.y - 4, 8, 8)
  for (const phase of [0, 0.5]) {
    const ring = (time * 0.7 + phase) % 1
    const ringR = 8 + ring * 20
    const ringA = 0.5 * (1 - ring)
    if (ringA <= 0.02) continue
    ctx.strokeStyle = `rgba(125, 211, 252, ${ringA.toFixed(3)})`
    ctx.lineWidth = 1.5
    ctx.strokeRect(end.x - ringR / 2, end.y - ringR / 2, ringR, ringR)
  }
  ctx.save()
  ctx.translate(end.x, end.y)
  ctx.rotate(time * 0.5)
  ctx.strokeStyle = 'rgba(125, 211, 252, 0.35)'
  ctx.lineWidth = 1.2
  ctx.setLineDash([4, 7])
  ctx.strokeRect(-16, -16, 32, 32)
  ctx.restore()

  // packets riding the wire on lanes; past the node they burst into a spark fan
  const burstDirs = [
    [1, 0],
    [1, -0.55],
    [1, 0.55],
    [0.65, -1],
    [0.65, 1],
    [0.3, -0.9],
    [0.3, 0.9],
  ]
  for (const pk of packets) {
    const u = (time * pk.speed + pk.off) % 1
    const p = pathPoint(u, w, h)
    // packets are white until the gate, encrypted blue after it
    const enc = u > 0.62
    const col = enc ? '125, 211, 252' : '228, 235, 246'
    // trail: 5 fading dots behind
    for (let k = 4; k >= 0; k--) {
      const tu = u - k * 0.006
      if (tu < 0) continue
      const tp = pathPoint(tu, w, h)
      const a = (0.95 - k * 0.18) * (u > 0.96 ? 0 : 1) * (enc ? 1 : 0.8)
      const s = pk.size - k * 0.4
      if (a <= 0 || s <= 0) continue
      ctx.fillStyle = `rgba(${col}, ${a.toFixed(3)})`
      ctx.fillRect(tp.x - s / 2, tp.y + pk.lane - s / 2, s, s)
    }
    // sparks around the gate right as the packet gets encrypted
    if (u > 0.62 && u < 0.7) {
      const e = (u - 0.62) / 0.08
      for (const [sx, sy] of [[-1, -0.8], [0.9, -0.9], [0.4, 1], [-0.6, 0.9]]) {
        const sa = (1 - e) * 0.85
        ctx.fillStyle = `rgba(125, 211, 252, ${sa.toFixed(3)})`
        const ss = Math.max(1.2, 3 - e * 1.4)
        ctx.fillRect(gate.x + sx * e * 30 - ss / 2, gate.y + sy * e * 24 - ss / 2, ss, ss)
      }
    }
    // burst sparks after reaching the node
    if (u > 0.96) {
      const e = (u - 0.96) / 0.04
      for (const [dx, dy] of burstDirs) {
        const sa = (1 - e) * 0.9
        ctx.fillStyle = `rgba(125, 211, 252, ${sa.toFixed(3)})`
        const ss = Math.max(1.4, pk.size * (1 - e * 0.6))
        ctx.fillRect(end.x + dx * e * 46 - ss / 2, end.y + dy * e * 38 - ss / 2, ss, ss)
      }
    }
  }
}

function seedPackets() {
  packets = []
  for (let i = 0; i < 14; i++) {
    packets.push({
      off: i / 14 + (i % 3) * 0.017,
      speed: 0.055 + (i % 4) * 0.012,
      size: 3.4 + (i % 3) * 0.7,
      lane: ((i % 3) - 1) * 6,
    })
  }
}

function seedMotes(w: number, h: number) {
  motes = []
  for (let i = 0; i < 18; i++) {
    motes.push({
      x: Math.random(),
      y: Math.random(),
      r: 0.9 + Math.random() * 1.1,
      speed: 0.012 + Math.random() * 0.02,
      phase: Math.random() * Math.PI * 2,
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
    seedMotes(rect.width, rect.height)
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
  height: 150px;
}
</style>
