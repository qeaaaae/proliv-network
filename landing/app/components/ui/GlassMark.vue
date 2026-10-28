<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { locations } from '~/data/product'
import { flagUrls } from '~/data/assets'

const { t } = useI18n()
const stage = ref<HTMLElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
const ready = ref(false)
const failed = ref(false)

const markPaths = [
  'M224 56c58.8 78.4 112 142.8 112 210a112 112 0 1 1-224 0c0-67.2 53.2-131.6 112-210z'
]

const tags = [
  { side: 'left', x: 2, y: 12, delay: 0 },
  { side: 'right', x: 6, y: 6, delay: -1.6 },
  { side: 'right', x: 0, y: 38, delay: -3.1 },
  { side: 'left', x: 0, y: 50, delay: -2.2 },
  { side: 'right', x: 8, y: 72, delay: -0.8 },
  { side: 'left', x: 10, y: 80, delay: -3.8 }
] as const

const flagTags = computed(() => locations.map((location, index) => ({
  id: location.id,
  name: t(location.nameKey),
  flag: flagUrls[location.countryCode],
  ...tags[index]!
})))

let dispose = () => {}

onMounted(async () => {
  const element = canvas.value
  const host = stage.value
  if (!element || !host) return
  try {
    const THREE = await import('three')
    const { SVGLoader } = await import('three/addons/loaders/SVGLoader.js')
    const { RoomEnvironment } = await import('three/addons/environments/RoomEnvironment.js')

    const renderer = new THREE.WebGLRenderer({ canvas: element, antialias: true, alpha: true, powerPreference: 'high-performance' })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = .9
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0a0c0e)
    const pmrem = new THREE.PMREMGenerator(renderer)
    const environment = pmrem.fromScene(new RoomEnvironment(), .04).texture
    scene.environment = environment
    scene.environmentIntensity = 1

    const camera = new THREE.PerspectiveCamera(30, 1, 10, 6000)
    camera.position.set(0, 40, 1500)
    camera.lookAt(0, 0, 0)

    const svg = `<svg xmlns="http://www.w3.org/2000/svg">${markPaths.map(path => `<path d="${path}"/>`).join('')}</svg>`
    const shapes = new SVGLoader().parse(svg).paths.flatMap(path => SVGLoader.createShapes(path))
    const geometry = new THREE.ExtrudeGeometry(shapes, {
      depth: 64,
      bevelEnabled: true,
      bevelThickness: 22,
      bevelSize: 14,
      bevelOffset: -2,
      bevelSegments: 12,
      curveSegments: 40
    })
    geometry.center()
    geometry.rotateX(Math.PI)
    geometry.computeVertexNormals()

    const glass = new THREE.MeshPhysicalMaterial({
      color: 0x7dd3fc,
      metalness: 0,
      roughness: .08,
      transmission: 1,
      thickness: 70,
      ior: 1.45,
      dispersion: 3,
      iridescence: .35,
      iridescenceIOR: 1.3,
      iridescenceThicknessRange: [220, 420],
      clearcoat: 1,
      clearcoatRoughness: .04,
      specularIntensity: 1,
      envMapIntensity: 1.25,
      attenuationColor: new THREE.Color(0x3fb5ec),
      attenuationDistance: 900
    })
    const mark = new THREE.Mesh(geometry, glass)
    mark.scale.setScalar(.92)
    const markGroup = new THREE.Group()
    markGroup.position.y = 120
    markGroup.add(mark)
    scene.add(markGroup)

    const key = new THREE.DirectionalLight(0xffffff, 1.4)
    key.position.set(-520, 700, 900)
    scene.add(key)
    const rim = new THREE.DirectionalLight(0x7dd3fc, 1)
    rim.position.set(700, -200, -400)
    scene.add(rim)

    const pointCloud = (points: number[], color: number, size: number) => {
      const buffer = new THREE.BufferGeometry()
      buffer.setAttribute('position', new THREE.Float32BufferAttribute(points, 3))
      return new THREE.Points(buffer, new THREE.PointsMaterial({ color, size, sizeAttenuation: true }))
    }
    const line = (target: number[], from: readonly number[], to: readonly number[], count: number) => {
      for (let index = 0; index <= count; index += 1) {
        const step = index / count
        target.push(from[0]! + (to[0]! - from[0]!) * step, from[1]! + (to[1]! - from[1]!) * step, from[2]! + (to[2]! - from[2]!) * step)
      }
    }

    const baseY = -420
    const topY = -150
    const baseHalf = 110
    const topHalf = 22
    const corners = (y: number, half: number) => [[-half, y, -half], [half, y, -half], [half, y, half], [-half, y, half]]
    const towerPoints: number[] = []
    const base = corners(baseY, baseHalf)
    const top = corners(topY, topHalf)
    base.forEach((corner, index) => line(towerPoints, corner, top[index]!, 34))
    const levels = 6
    for (let level = 0; level < levels; level += 1) {
      const y0 = baseY + (topY - baseY) * (level / levels)
      const y1 = baseY + (topY - baseY) * ((level + 1) / levels)
      const h0 = baseHalf + (topHalf - baseHalf) * (level / levels)
      const h1 = baseHalf + (topHalf - baseHalf) * ((level + 1) / levels)
      const lower = corners(y0, h0)
      const upper = corners(y1, h1)
      for (let side = 0; side < 4; side += 1) {
        line(towerPoints, lower[side]!, upper[(side + 1) % 4]!, 12)
        line(towerPoints, lower[side]!, lower[(side + 1) % 4]!, 10)
      }
    }
    line(towerPoints, [0, topY, 0], [0, topY + 70, 0], 12)
    const tower = pointCloud(towerPoints, 0x8d8d95, 5)
    scene.add(tower)

    const rings: { cloud: InstanceType<typeof THREE.Points>, speed: number }[] = []
    for (const [radius, count, color, speed] of [[200, 90, 0x55555c, .08], [290, 120, 0x3e3e44, -.05], [380, 150, 0x2c2c31, .03]] as const) {
      const ringPoints: number[] = []
      for (let index = 0; index < count; index += 1) {
        const angle = index / count * Math.PI * 2
        ringPoints.push(Math.cos(angle) * radius, baseY, Math.sin(angle) * radius)
      }
      const cloud = pointCloud(ringPoints, color, 5)
      scene.add(cloud)
      rings.push({ cloud, speed })
    }

    const glowCanvas = document.createElement('canvas')
    glowCanvas.width = glowCanvas.height = 256
    const glowContext = glowCanvas.getContext('2d')!
    const glowGradient = glowContext.createRadialGradient(128, 128, 0, 128, 128, 128)
    glowGradient.addColorStop(0, '#45454c')
    glowGradient.addColorStop(.45, '#1c1c20')
    glowGradient.addColorStop(1, '#0a0c0e')
    glowContext.fillStyle = glowGradient
    glowContext.fillRect(0, 0, 256, 256)
    const glowTexture = new THREE.CanvasTexture(glowCanvas)
    glowTexture.colorSpace = THREE.SRGBColorSpace
    const glow = new THREE.Mesh(new THREE.PlaneGeometry(1500, 1500), new THREE.MeshBasicMaterial({ map: glowTexture, toneMapped: false }))
    glow.position.set(0, 110, -520)
    scene.add(glow)

    const haloPoints: number[] = []
    for (let ring = 0; ring < 7; ring += 1) {
      const radius = 120 + ring * 52
      const count = Math.round(radius * .42)
      for (let index = 0; index < count; index += 1) {
        const angle = index / count * Math.PI * 2 + ring * .2
        haloPoints.push(Math.cos(angle) * radius, Math.sin(angle) * radius, 0)
      }
    }
    const halo = pointCloud(haloPoints, 0x6a6a74, 5)
    halo.position.set(0, 120, -320)
    scene.add(halo)

    const waves: InstanceType<typeof THREE.Points>[] = []
    for (let index = 0; index < 3; index += 1) {
      const wavePoints: number[] = []
      for (let step = 0; step < 120; step += 1) {
        const angle = step / 120 * Math.PI * 2
        wavePoints.push(Math.cos(angle), Math.sin(angle) * .34, Math.sin(angle) * .6)
      }
      const wave = pointCloud(wavePoints, 0xffffff, 4)
      wave.position.set(0, topY + 70, 0)
      scene.add(wave)
      waves.push(wave)
    }

    const resize = () => {
      const { width, height } = host.getBoundingClientRect()
      if (!width || !height) return
      renderer.setSize(width, height, false)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    }
    resize()
    const resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(host)

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const pointer = { x: 0, y: 0 }
    const eased = { x: 0, y: 0 }
    const onPointer = (event: PointerEvent) => {
      pointer.x = event.clientX / window.innerWidth * 2 - 1
      pointer.y = event.clientY / window.innerHeight * 2 - 1
    }
    window.addEventListener('pointermove', onPointer, { passive: true })

    const background = new THREE.Color(0x0a0c0e)
    const white = new THREE.Color(0xffffff)
    let visible = true
    let frame = 0
    const clock = new THREE.Clock()
    const render = () => {
      const time = clock.getElapsedTime()
      eased.x += (pointer.x - eased.x) * .05
      eased.y += (pointer.y - eased.y) * .05
      markGroup.rotation.y = Math.sin(time * .45) * .42 + eased.x * .55
      markGroup.rotation.x = Math.sin(time * .32) * .06 + eased.y * .22
      markGroup.position.y = 120 + Math.sin(time * .9) * 14
      rings.forEach(({ cloud, speed }) => { cloud.rotation.y = time * speed })
      tower.rotation.y = time * .12
      halo.rotation.z = time * .05
      waves.forEach((wave, index) => {
        const progress = (time * .32 + index / waves.length) % 1
        const radius = 60 + progress * 420
        wave.scale.set(radius, radius, radius)
        ;(wave.material as InstanceType<typeof THREE.PointsMaterial>).color.copy(white).lerp(background, progress)
      })
      renderer.render(scene, camera)
      if (!ready.value) ready.value = true
      frame = visible && !reduced ? requestAnimationFrame(render) : 0
    }

    const visibility = new IntersectionObserver(([entry]) => {
      visible = Boolean(entry?.isIntersecting) && document.visibilityState === 'visible'
      if (visible && !frame) frame = requestAnimationFrame(render)
    })
    visibility.observe(host)
    const onVisibility = () => {
      visible = document.visibilityState === 'visible'
      if (visible && !frame) frame = requestAnimationFrame(render)
    }
    document.addEventListener('visibilitychange', onVisibility)
    frame = requestAnimationFrame(render)

    dispose = () => {
      cancelAnimationFrame(frame)
      visibility.disconnect()
      resizeObserver.disconnect()
      window.removeEventListener('pointermove', onPointer)
      document.removeEventListener('visibilitychange', onVisibility)
      scene.traverse((object) => {
        const mesh = object as InstanceType<typeof THREE.Mesh>
        mesh.geometry?.dispose()
        const material = mesh.material as InstanceType<typeof THREE.Material> | undefined
        material?.dispose()
      })
      environment.dispose()
      glowTexture.dispose()
      pmrem.dispose()
      renderer.dispose()
    }
  } catch {
    failed.value = true
  }
})

onBeforeUnmount(() => dispose())
</script>

<template>
  <div ref="stage" class="glass-stage" :class="{ 'is-ready': ready }" aria-hidden="true">
    <canvas ref="canvas" class="glass-canvas" />
    <svg v-if="failed" class="glass-fallback" viewBox="96 40 256 336">
      <path v-for="(path, index) in markPaths" :key="index" :d="path" />
    </svg>
    <ul class="flag-tags">
      <li
        v-for="tag in flagTags"
        :key="tag.id"
        class="flag-tag"
        :style="{ [tag.side]: `${tag.x}%`, top: `${tag.y}%`, animationDelay: `${tag.delay}s` }"
      >
        <img :src="tag.flag" alt="" width="20" height="14">
        <span>{{ tag.name }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.glass-stage {
  position: relative;
  aspect-ratio: 1;
  width: 100%;
  user-select: none;
}

.glass-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  -webkit-mask-image: radial-gradient(closest-side, #000 74%, transparent 100%);
  mask-image: radial-gradient(closest-side, #000 74%, transparent 100%);
  transition: opacity 1.2s var(--ease-out);
}

.glass-stage.is-ready .glass-canvas {
  opacity: 1;
}

.glass-fallback {
  position: absolute;
  inset: 12% 30% 30%;
  fill: var(--plate);
}

.flag-tags {
  position: absolute;
  inset: 0;
  margin: 0;
  padding: 0;
  list-style: none;
  pointer-events: none;
}

.flag-tag {
  position: absolute;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 11px 7px 8px;
  color: var(--fg);
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  background: rgb(15 18 21 / 86%);
  border: 1px solid var(--line-strong);
  border-radius: 10px;
  box-shadow: 0 10px 30px rgb(0 0 0 / 40%);
  animation: float-soft 6.5s var(--ease) infinite;
}

.flag-tag img {
  width: 20px;
  height: 14px;
  object-fit: cover;
  border-radius: 3px;
  box-shadow: 0 0 0 1px rgb(255 255 255 / 16%);
}

@media (max-width: 720px) {
  .flag-tag {
    padding: 5px 8px 5px 6px;
    font-size: 10px;
    gap: 6px;
  }

  .flag-tag img {
    width: 16px;
    height: 11px;
  }
}
</style>
