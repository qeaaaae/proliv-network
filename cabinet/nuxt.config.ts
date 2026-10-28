export default defineNuxtConfig({
  compatibilityDate: '2025-10-25',
  devtools: { enabled: false },
  ssr: false,
  runtimeConfig: {
    // токен shop-бота для верификации Telegram Login Widget
    botToken: process.env.NUXT_BOT_TOKEN || '',
    // подпись сессионной куки; если пусто - берётся хэш от botToken (dev)
    sessionSecret: process.env.NUXT_SESSION_SECRET || '',
    // URL общего бэкенда (minishop WebApp API); в compose - http://remnawave-minishop-backend:8081
    shopApiUrl: process.env.NUXT_SHOP_API_URL || '',
    // OIDC client_secret из BotFather -> Bot Settings -> Web Login (code-flow)
    telegramOauthClientSecret: process.env.NUXT_TELEGRAM_OAUTH_CLIENT_SECRET || '',
    public: {
      // username бота, привязанного к домену через /setdomain у BotFather
      botUsername: process.env.NUXT_PUBLIC_BOT_USERNAME || '',
      landingUrl: process.env.NUXT_PUBLIC_LANDING_URL || 'https://proliv-network.xyz',
      // '1' включает POST /api/auth/dev и кнопку dev-входа (только локальная разработка)
      devAuth: process.env.NUXT_PUBLIC_DEV_AUTH || '',
    },
  },
  app: {
    pageTransition: { name: 'page', mode: 'default' },
    head: {
      htmlAttrs: { lang: 'ru' },
      title: 'Личный кабинет - Proliv Network',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
        { name: 'theme-color', content: '#0a0c0e' },
        { name: 'format-detection', content: 'telephone=no' },
        { name: 'robots', content: 'noindex, nofollow' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      // Telegram Mini App API (window.Telegram.WebApp) - нужен для initData-авторизации
      script: [{ src: 'https://telegram.org/js/telegram-web-app.js' }],
    },
  },
  css: ['@fontsource-variable/manrope', '@fontsource-variable/unbounded', '~/assets/css/main.css'],
  routeRules: {
    '/**': {
      headers: {
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        // Mini App грузится в iframe Telegram - XFO нельзя, CSP ограничивает предков
        'Content-Security-Policy':
          "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org https://t.me https://*.t.me",
      },
    },
  },
})
