export interface Toast {
  id: number
  text: string
  type: 'info' | 'error'
}

export function useToast() {
  const toasts = useState<Toast[]>('toasts', () => [])

  function push(text: string, type: Toast['type'] = 'info') {
    const id = Date.now() + Math.random()
    toasts.value.push({ id, text, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 3400)
  }

  return { toasts, push }
}
