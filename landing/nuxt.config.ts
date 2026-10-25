export default defineNuxtConfig({
  compatibilityDate: '2025-10-25',
  devtools: { enabled: false },
  ssr: true,
  app: {
    head: {
      htmlAttrs: { lang: 'ru' },
      title: 'Proliv Network',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'theme-color', content: '#050607' },
        { name: 'format-detection', content: 'telephone=no' },
        {
          name: 'description',
          content:
            'Две локации с портом 10 Гбит/с, 1000 ГБ трафика в месяц и 5 устройств. Подключение от 179 ₽.',
        },
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: 'Proliv Network' },
        { property: 'og:title', content: 'Proliv Network' },
        {
          property: 'og:description',
          content:
            'Две локации с портом 10 Гбит/с, 1000 ГБ трафика в месяц и 5 устройств. Подключение от 179 ₽.',
        },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      script: [
        {
          innerHTML:
            "if(matchMedia('(prefers-reduced-motion: no-preference)').matches&&'IntersectionObserver'in window){const r=document.documentElement;r.classList.add('motion');setTimeout(()=>{if(!('reveal'in r.dataset))r.classList.remove('motion')},4000)}",
        },
      ],
    },
  },
  css: [
    '@fontsource-variable/onest',
    '@fontsource-variable/unbounded',
    '~/assets/css/main.css',
  ],
})
