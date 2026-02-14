import { computed, watch } from 'vue'
import { useDark, useToggle } from '@vueuse/core'

export function useTheme() {
  const isDark = useDark({
    selector: 'html',
    attribute: 'class',
    valueDark: 'dark',
    valueLight: 'light',
  })

  const toggleDark = useToggle(isDark)

  const themeName = computed(() => isDark.value ? 'dark' : 'light')
  const themeIcon = computed(() => isDark.value ? 'pi pi-sun' : 'pi pi-moon')

  // Brief transition effect when toggling
  watch(isDark, () => {
    document.documentElement.classList.add('theme-transition')
    setTimeout(() => {
      document.documentElement.classList.remove('theme-transition')
    }, 350)
  })

  return {
    isDark,
    toggleDark,
    themeName,
    themeIcon,
  }
}
