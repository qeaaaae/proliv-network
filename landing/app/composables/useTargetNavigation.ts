import { NavigationFailureType, isNavigationFailure } from 'vue-router'
import { telegramBotUrl } from '~/data/product'

export function useTargetNavigation() {
  const router = useRouter()
  const cabinetUrl = useRuntimeConfig().public.cabinetUrl as string

  async function navigate(target: string) {
    const url = new URL(target, window.location.href)
    if (url.origin !== window.location.origin) {
      if (url.origin === new URL(telegramBotUrl).origin) {
        window.open(url.href, '_blank', 'noopener')
        return
      }
      if (url.origin === new URL(cabinetUrl).origin) {
        const referral = new URL(window.location.href).searchParams.get('ref')
        if (referral && !url.searchParams.has('ref')) url.searchParams.set('ref', referral)
      }
      window.location.assign(url.href)
      return
    }

    const failure = await router.push(`${url.pathname}${url.search}${url.hash}`)
    if (!url.hash && isNavigationFailure(failure, NavigationFailureType.duplicated)) window.scrollTo({ top: 0 })
  }

  return { navigate }
}
