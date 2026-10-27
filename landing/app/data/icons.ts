import arrowDown from '@iconify-icons/iconoir/arrow-down'
import arrowRight from '@iconify-icons/iconoir/arrow-right'
import arrowUpRight from '@iconify-icons/iconoir/arrow-up-right'
import sendDiagonal from '@iconify-icons/iconoir/send-diagonal'

export const icons = {
  'arrow-down': arrowDown,
  'arrow-right': arrowRight,
  'arrow-up-right': arrowUpRight,
  plane: sendDiagonal
}

export type IconName = keyof typeof icons
