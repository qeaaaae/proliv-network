import type { Ref } from 'vue'

interface CanvasLoopOptions {
  resize: (canvas: HTMLCanvasElement) => void
  draw: (time: number) => void
  stillTime?: number
  wallClock?: boolean
}

export function prepareContext(canvas: HTMLCanvasElement) {
  const scale = Math.min(window.devicePixelRatio || 1, 2)
  const width = canvas.clientWidth
  const height = canvas.clientHeight
  canvas.width = Math.max(1, Math.round(width * scale))
  canvas.height = Math.max(1, Math.round(height * scale))
  const context = canvas.getContext('2d')
  context?.setTransform(scale, 0, 0, scale, 0, 0)
  return { context, width, height }
}

export function useCanvasLoop(canvas: Ref<HTMLCanvasElement | null>, options: CanvasLoopOptions) {
  let frame = 0
  let last = 0
  let reduceMotion = false
  let resizeObserver: ResizeObserver | undefined
  let visibilityObserver: IntersectionObserver | undefined

  const clock = () => (options.wallClock ? Date.now() : performance.now()) / 1000

  const tick = (now: number) => {
    frame = requestAnimationFrame(tick)
    if (now - last < 33) return
    last = now
    options.draw(clock())
  }

  const start = () => {
    if (!frame && !reduceMotion) frame = requestAnimationFrame(tick)
  }

  const stop = () => {
    cancelAnimationFrame(frame)
    frame = 0
  }

  onMounted(() => {
    const element = canvas.value
    if (!element) return
    reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    resizeObserver = new ResizeObserver(() => {
      options.resize(element)
      options.draw(reduceMotion ? options.stillTime ?? 0 : clock())
    })
    resizeObserver.observe(element)
    visibilityObserver = new IntersectionObserver((entries) => {
      if (entries.at(-1)?.isIntersecting) start()
      else stop()
    })
    visibilityObserver.observe(element)
  })

  onBeforeUnmount(() => {
    stop()
    resizeObserver?.disconnect()
    visibilityObserver?.disconnect()
  })
}
