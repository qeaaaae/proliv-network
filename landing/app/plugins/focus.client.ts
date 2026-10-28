export default defineNuxtPlugin((nuxtApp) => {
  const root = document.documentElement

  const handleKeydown = (event: KeyboardEvent) => {
    if (['Tab', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) {
      root.dataset.inputModality = 'keyboard'
    }
  }

  const handlePointerdown = () => { root.dataset.inputModality = 'pointer' }

  const cleanup = () => {
    document.removeEventListener('keydown', handleKeydown, true)
    document.removeEventListener('pointerdown', handlePointerdown, true)
    delete root.dataset.inputModality
  }

  handlePointerdown()
  document.addEventListener('keydown', handleKeydown, true)
  document.addEventListener('pointerdown', handlePointerdown, true)
  nuxtApp.vueApp.onUnmount(cleanup)
  if (import.meta.hot) import.meta.hot.dispose(cleanup)
})
