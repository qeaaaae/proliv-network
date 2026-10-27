export default defineNuxtPlugin((nuxtApp) => {
  let observer: IntersectionObserver | undefined

  if (import.meta.client) {
    const root = document.documentElement
    root.dataset.reveal = ''
    if (root.classList.contains('motion')) {
      observer = new IntersectionObserver(entries => entries.forEach((entry) => {
        if (!entry.isIntersecting) return
        entry.target.setAttribute('data-shown', '')
        observer?.unobserve(entry.target)
      }), { rootMargin: '0px 0px -8% 0px' })
    }
  }

  nuxtApp.vueApp.directive<HTMLElement>('reveal', {
    getSSRProps: binding => ({ 'data-reveal': binding.arg ?? '' }),
    created: (element, binding) => element.setAttribute('data-reveal', binding.arg ?? ''),
    mounted: element => observer?.observe(element),
    unmounted: element => observer?.unobserve(element)
  })
})
