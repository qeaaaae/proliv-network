import { BUILD_ASSETS_DIR, viteAssetBuild, viteServerAssetBuild } from './config/vite-assets'

export default defineNuxtConfig({
  compatibilityDate: '2025-10-25',
  devtools: { enabled: false },
  ssr: true,
  runtimeConfig: {
    public: {
      // локальный dev кабинета; в проде переопределяется NUXT_PUBLIC_CABINET_URL при сборке
      cabinetUrl: process.env.NUXT_PUBLIC_CABINET_URL || 'http://localhost:3300',
    },
  },
  css: ['@fontsource-variable/unbounded', '@fontsource-variable/manrope', '~/assets/css/main.css'],
  features: { inlineStyles: false },
  hooks: {
    'build:manifest'(manifest) {
      for (const resource of Object.values(manifest)) {
        resource.prefetch = false
      }
    }
  },
  app: {
    buildAssetsDir: BUILD_ASSETS_DIR,
    head: {
      title: 'Proliv Network',
      htmlAttrs: { lang: 'ru' },
      link: [
        { rel: 'canonical', href: 'https://proliv-network.xyz/' },
        { rel: 'icon', type: 'image/svg+xml', sizes: 'any', href: '/favicon.svg' }
      ],
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'theme-color', content: '#0a0c0e', tagPriority: 'critical' },
        { name: 'format-detection', content: 'telephone=no', tagPriority: 'critical' },
        { name: 'robots', content: 'index, follow, max-image-preview:large', tagPriority: 'critical' }
      ],
      script: [
        { key: 'motion', innerHTML: "if(matchMedia('(prefers-reduced-motion: no-preference)').matches&&'IntersectionObserver'in window){const root=document.documentElement;root.classList.add('motion');setTimeout(()=>{if(!('reveal'in root.dataset))root.classList.remove('motion')},4000)}", tagPriority: 'critical' }
      ]
    }
  },
  vite: {
    $client: {
      build: viteAssetBuild
    },
    $server: {
      build: viteServerAssetBuild
    }
  },
  nitro: {
    prerender: {
      ignore: ['/200.html', '/404.html'],
      routes: ['/', '/terms', '/privacy', '/offer', '/personal-data', '/invite', '/status']
    }
  },
  typescript: {
    strict: true,
    typeCheck: false
  }
})
