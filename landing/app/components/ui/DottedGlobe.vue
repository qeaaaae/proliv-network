<script setup lang="ts">
import { homeCity } from '~/data/product'
import { landMask } from '~/data/landMask'

interface GlobeMarker {
  id: string
  lat: number
  lon: number
  label: string
}

const props = defineProps<{ markers: GlobeMarker[], active: string }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const radians = Math.PI / 180
const plate = '#7dd3fc'
const ink = '#06222f'

type Vector = [number, number, number]

function toVector(lat: number, lon: number): Vector {
  return [Math.cos(lat * radians) * Math.sin(lon * radians), Math.sin(lat * radians), Math.cos(lat * radians) * Math.cos(lon * radians)]
}

function decodeLand() {
  const bytes = Uint8Array.from(atob(landMask.bits), character => character.charCodeAt(0))
  const vectors: Vector[] = []
  const span = landMask.east - landMask.west
  let index = 0
  for (let lat = landMask.north; lat >= landMask.south; lat -= landMask.step) {
    const count = Math.max(1, Math.round(span * Math.cos(lat * radians) / landMask.step))
    for (let step = 0; step < count; step += 1, index += 1) {
      if (bytes[index >> 3]! & (1 << (index & 7))) vectors.push(toVector(lat, landMask.west + (step + .5) * span / count))
    }
  }
  return vectors
}

function buildGraticule() {
  const vectors: Vector[] = []
  for (let lat = 30; lat <= 75; lat += 5) {
    for (let lon = -40; lon <= 84; lon += .5) vectors.push(toVector(lat, lon))
  }
  for (let lon = -40; lon <= 84; lon += 10) {
    for (let lat = 26; lat <= 76; lat += .5) vectors.push(toVector(lat, lon))
  }
  return vectors
}

let land: Vector[] = []
let graticule: Vector[] = []
let context: CanvasRenderingContext2D | null = null
let width = 0
let height = 0
let arcStartedAt = 0
const pointer = { target: 0, eased: 0 }

function slerp(from: Vector, to: Vector, step: number): Vector {
  const cosine = Math.min(1, from[0] * to[0] + from[1] * to[1] + from[2] * to[2])
  const angle = Math.acos(cosine)
  if (angle < 1e-4) return from
  const a = Math.sin((1 - step) * angle) / Math.sin(angle)
  const b = Math.sin(step * angle) / Math.sin(angle)
  return [from[0] * a + to[0] * b, from[1] * a + to[1] * b, from[2] * a + to[2] * b]
}

function draw(time: number) {
  if (!context || !width) return
  pointer.eased += (pointer.target - pointer.eased) * .06
  const view = { lat: 53, lon: 18 + Math.sin(time * .16) * 6 + pointer.eased * 7 }
  const radius = Math.max(width, height) * 1.35
  const centerX = width / 2
  const centerY = height * .5
  const yawSin = Math.sin(view.lon * radians)
  const yawCos = Math.cos(view.lon * radians)
  const pitchSin = Math.sin(view.lat * radians)
  const pitchCos = Math.cos(view.lat * radians)

  const project = ([x, y, z]: Vector, lift = 1) => {
    const rotatedX = x * yawCos - z * yawSin
    const rotatedZ = x * yawSin + z * yawCos
    const finalY = y * pitchCos - rotatedZ * pitchSin
    const depth = y * pitchSin + rotatedZ * pitchCos
    return { x: centerX + rotatedX * radius * lift, y: centerY - finalY * radius * lift, depth }
  }

  context.clearRect(0, 0, width, height)
  context.fillStyle = plate
  context.globalAlpha = .1
  for (const vector of graticule) {
    const point = project(vector)
    if (point.depth > 0 && point.x > -2 && point.x < width + 2 && point.y > -2 && point.y < height + 2) context.fillRect(point.x - .5, point.y - .5, 1, 1)
  }
  context.globalAlpha = 1

  const activeMarker = props.markers.find(marker => marker.id === props.active)
  const activeVector = activeMarker ? toVector(activeMarker.lat, activeMarker.lon) : null
  const dot = Math.max(1.6, width / 400)
  context.fillStyle = plate
  for (const vector of land) {
    const point = project(vector)
    if (point.depth <= 0 || point.x < -dot || point.x > width + dot || point.y < -dot || point.y > height + dot) continue
    let alpha = .34
    if (activeVector) {
      const closeness = vector[0] * activeVector[0] + vector[1] * activeVector[1] + vector[2] * activeVector[2]
      if (closeness > .9985) alpha = Math.min(.95, alpha + (closeness - .9985) * 480)
    }
    context.globalAlpha = alpha
    context.fillRect(point.x - dot / 2, point.y - dot / 2, dot, dot)
  }
  context.globalAlpha = 1

  const home = toVector(homeCity.lat, homeCity.lon)
  if (activeVector) {
    const progress = Math.min(1, (time - arcStartedAt) / .9)
    const eased = 1 - Math.pow(1 - progress, 3)
    const segments = 56
    const arcPoints = []
    for (let index = 0; index <= segments; index += 1) {
      const step = index / segments
      if (step > eased) break
      arcPoints.push(project(slerp(home, activeVector, step), 1 + Math.sin(Math.PI * step) * .07))
    }
    context.fillStyle = plate
    arcPoints.forEach((point, index) => {
      if (index % 2) return
      context!.globalAlpha = .55
      context!.fillRect(point.x - 1, point.y - 1, 2, 2)
    })
    if (progress >= 1) {
      const head = (time * .55) % 1
      for (let trail = 0; trail < 10; trail += 1) {
        const step = head - trail * .018
        if (step < 0) break
        const point = project(slerp(home, activeVector, step), 1 + Math.sin(Math.PI * step) * .07)
        context.globalAlpha = 1 - trail / 10
        context.beginPath()
        context.arc(point.x, point.y, 2.6 - trail * .2, 0, Math.PI * 2)
        context.fill()
      }
    }
    context.globalAlpha = 1
  }

  const homePoint = project(home)
  context.strokeStyle = plate
  context.lineWidth = 1.2
  context.beginPath()
  context.arc(homePoint.x, homePoint.y, 4, 0, Math.PI * 2)
  context.stroke()

  const focus = activeVector ? project(activeVector) : null
  for (const marker of props.markers) {
    const point = project(toVector(marker.lat, marker.lon))
    if (point.depth <= 0) continue
    if (marker.id !== props.active) {
      context.fillStyle = 'rgb(125 211 252 / 70%)'
      context.beginPath()
      context.arc(point.x, point.y, 3, 0, Math.PI * 2)
      context.fill()
      if (width >= 520 && (!focus || Math.hypot(point.x - focus.x, point.y - focus.y) > 70)) {
        context.font = '600 12px "Manrope Variable", system-ui, sans-serif'
        context.fillStyle = 'rgb(125 211 252 / 50%)'
        context.fillText(marker.label, point.x + 9, point.y + 4)
      }
      continue
    }
    for (let ring = 0; ring < 2; ring += 1) {
      const pulse = (time * .7 + ring * .5) % 1
      context.strokeStyle = `rgb(125 211 252 / ${(1 - pulse) * 60}%)`
      context.lineWidth = 1
      context.beginPath()
      context.arc(point.x, point.y, 5 + pulse * 22, 0, Math.PI * 2)
      context.stroke()
    }
    context.fillStyle = plate
    context.beginPath()
    context.arc(point.x, point.y, 4.5, 0, Math.PI * 2)
    context.fill()

    context.font = '700 13px "Manrope Variable", system-ui, sans-serif'
    const labelWidth = context.measureText(marker.label).width + 18
    const labelX = Math.min(width - labelWidth - 8, point.x + 16)
    const labelY = point.y - 40
    context.strokeStyle = 'rgb(125 211 252 / 50%)'
    context.beginPath()
    context.moveTo(point.x + 3, point.y - 3)
    context.lineTo(labelX + 8, labelY + 26)
    context.stroke()
    context.fillStyle = plate
    context.beginPath()
    context.roundRect(labelX, labelY, labelWidth, 26, 7)
    context.fill()
    context.fillStyle = ink
    context.fillText(marker.label, labelX + 9, labelY + 17.5)
  }
}

useCanvasLoop(canvas, {
  resize: (element) => {
    if (!land.length) {
      land = decodeLand()
      graticule = buildGraticule()
    }
    const surface = prepareContext(element)
    context = surface.context
    width = surface.width
    height = surface.height
  },
  draw,
  stillTime: 2
})

watch(() => props.active, () => {
  arcStartedAt = performance.now() / 1000
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    arcStartedAt = -10
    draw(2)
  }
})

function onPointer(event: PointerEvent) {
  const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
  pointer.target = ((event.clientX - bounds.left) / bounds.width) * 2 - 1
}
</script>

<template>
  <div class="globe" aria-hidden="true" @pointermove="onPointer" @pointerleave="pointer.target = 0">
    <canvas ref="canvas" />
  </div>
</template>

<style scoped>
.globe {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 360px;
}

.globe canvas {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  -webkit-mask-image: radial-gradient(ellipse 72% 70% at 50% 50%, #000 55%, transparent 100%);
  mask-image: radial-gradient(ellipse 72% 70% at 50% 50%, #000 55%, transparent 100%);
}
</style>
