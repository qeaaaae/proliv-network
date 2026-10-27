export default defineNuxtPlugin((nuxtApp) => {
  const root = document.documentElement
  if (!matchMedia('(prefers-reduced-motion: no-preference)').matches) return
  if (!('IntersectionObserver' in window)) return

  root.classList.add('motion')

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.setAttribute('data-shown', '')
          observer.unobserve(entry.target)
        }
      }
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px' },
  )

  const scan = (scope: ParentNode | Element) => {
    if (scope instanceof Element && scope.matches('[data-reveal]:not([data-shown])')) {
      observer.observe(scope)
    }
    scope.querySelectorAll?.('[data-reveal]:not([data-shown])').forEach((el) => observer.observe(el))
  }

  // catch elements added by client-side navigation or lazy mounts
  new MutationObserver((mutations) => {
    for (const m of mutations) {
      m.addedNodes.forEach((n) => scan(n as ParentNode))
    }
  }).observe(document.documentElement, { childList: true, subtree: true })

  nuxtApp.hooks.hook('page:finish', () => scan(document))

  scan(document)
})
