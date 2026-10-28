import { createI18n } from 'vue-i18n'
import ru from '../../i18n/locales/ru'

export default defineNuxtPlugin(({ vueApp }) => {
  const i18n = createI18n({
    legacy: false,
    locale: 'ru',
    fallbackLocale: 'ru',
    messages: { ru }
  })

  vueApp.use(i18n)
})
