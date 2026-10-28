import type { Ref } from 'vue'

// Плавающая плашка активного сегмента внутри .pills - тот же приём, что
// fab-nav__pill: меряем offset активной кнопки и двигаем плашку transform'ом.
// Контейнеру нужен класс has-pill, иначе работает CSS-фолбэк с фоном на кнопке.
export function usePillIndicator(itemEls: Ref<unknown[]>, activeIndex: Ref<number>) {
  const indicator = ref({ x: 0, w: 0, ready: false })

  async function sync() {
    await nextTick()
    const raw = itemEls.value?.[activeIndex.value]
    const el = raw instanceof HTMLElement ? raw : (raw as { $el?: unknown })?.$el
    if (!(el instanceof HTMLElement)) {
      indicator.value = { x: 0, w: 0, ready: false }
      return
    }
    indicator.value = { x: el.offsetLeft, w: el.offsetWidth, ready: true }
  }

  onMounted(() => {
    sync()
    // перемер после подгрузки шрифтов - метрики кнопок сдвигаются
    document.fonts?.ready.then(() => void sync())
    window.addEventListener('resize', sync)
  })
  onBeforeUnmount(() => window.removeEventListener('resize', sync))
  watch([itemEls, activeIndex], sync)

  return { indicator, sync }
}
