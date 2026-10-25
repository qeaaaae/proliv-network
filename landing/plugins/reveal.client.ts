export default defineNuxtPlugin(() => {
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

  const observeAll = () => {
    document.querySelectorAll('[data-reveal]:not([data-shown])').forEach((el) => observer.observe(el))
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observeAll, { once: true })
  } else {
    observeAll()
  }

  // safety: if anything stays hidden after 4s, reveal everything
  setTimeout(() => {
    document
      .querySelectorAll('[data-reveal]:not([data-shown])')
      .forEach((el) => el.setAttribute('data-shown', ''))
    observer.disconnect()
  }, 4000)
})
