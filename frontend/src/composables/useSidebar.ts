import { ref, computed, watch } from 'vue'
import { useMediaQuery } from '@vueuse/core'

const isCollapsed = ref(false)
const isMobileOpen = ref(false)

export function useSidebar() {
  const isDesktop = useMediaQuery('(min-width: 1024px)')
  const isTablet = useMediaQuery('(min-width: 768px)')

  const sidebarWidth = computed(() => {
    if (!isDesktop.value) return '0px'
    return isCollapsed.value ? '64px' : '260px'
  })

  const showOverlay = computed(() => {
    return !isDesktop.value && isMobileOpen.value
  })

  const toggleCollapse = () => {
    isCollapsed.value = !isCollapsed.value
  }

  const toggleMobile = () => {
    isMobileOpen.value = !isMobileOpen.value
  }

  const closeMobile = () => {
    isMobileOpen.value = false
  }

  // Auto-close mobile sidebar on route change
  watch(isDesktop, (val) => {
    if (val) isMobileOpen.value = false
  })

  return {
    isCollapsed,
    isMobileOpen,
    isDesktop,
    isTablet,
    sidebarWidth,
    showOverlay,
    toggleCollapse,
    toggleMobile,
    closeMobile,
  }
}
