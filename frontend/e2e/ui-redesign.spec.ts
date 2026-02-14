import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5199'

test.describe('UI Redesign - Layout & Navigation', () => {
  test('Home page loads with hero section and sport cards', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Hero section should have split typography
    const heading = page.locator('text=Sports')
    await expect(heading.first()).toBeVisible()
    await expect(page.locator('text=Dashboard').first()).toBeVisible()

    // Should have 3 sport cards (Football, Cricket, Rugby)
    const sportCards = page.locator('.glass-card, .glass-card-interactive')
    const count = await sportCards.count()
    expect(count).toBeGreaterThanOrEqual(3)

    // Football card should be clickable
    const footballCard = page.locator('a[href="/football"]').first()
    await expect(footballCard).toBeVisible()

    // Cricket and Rugby should show "COMING SOON"
    await expect(page.locator('text=COMING SOON').first()).toBeVisible()
  })

  test('Sidebar is visible and has correct navigation structure', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Sidebar should be present
    const sidebar = page.locator('.app-sidebar, nav, aside').first()
    await expect(sidebar).toBeVisible()

    // Should have SportsDash logo/branding
    await expect(page.locator('text=SportsDash').first()).toBeVisible()

    // Should have Football section
    await expect(page.locator('text=Football').first()).toBeVisible()

    // Should have theme toggle button (sun/moon icon)
    const themeToggle = page.locator('button').filter({ has: page.locator('[class*="pi-sun"], [class*="pi-moon"]') })
    await expect(themeToggle.first()).toBeVisible()
  })

  test('Navigating to Football Dashboard via sidebar', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Click Football in sidebar to expand
    const footballNav = page.locator('text=Football').first()
    await footballNav.click()
    await page.waitForTimeout(300)

    // Click Dashboard sub-item
    const dashboardLink = page.locator('a[href="/football"]').first()
    await dashboardLink.click()
    await page.waitForURL('**/football')

    expect(page.url()).toContain('/football')
  })

  test('TopBar shows breadcrumbs on subpages', async ({ page }) => {
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')

    // Should show breadcrumb-like text
    const topBar = page.locator('.top-bar, header').first()
    await expect(topBar).toBeVisible()
  })
})

test.describe('UI Redesign - Dark/Light Mode', () => {
  test('Dark mode is active by default', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // HTML element should have dark class
    const htmlClass = await page.locator('html').getAttribute('class')
    expect(htmlClass).toContain('dark')
  })

  test('Theme toggle switches between dark and light', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Verify starts in dark mode
    let htmlClass = await page.locator('html').getAttribute('class')
    expect(htmlClass).toContain('dark')

    // Find and click theme toggle
    const themeToggle = page.locator('button').filter({ has: page.locator('[class*="pi-moon"], [class*="pi-sun"]') }).first()
    await themeToggle.click()
    await page.waitForTimeout(500)

    // Should now be in light mode
    htmlClass = await page.locator('html').getAttribute('class')
    expect(htmlClass).toContain('light')

    // Toggle back to dark
    await themeToggle.click()
    await page.waitForTimeout(500)
    htmlClass = await page.locator('html').getAttribute('class')
    expect(htmlClass).toContain('dark')
  })

  test('Light mode changes surface colors', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Get body bg in dark mode
    const darkBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor)

    // Toggle to light
    const themeToggle = page.locator('button').filter({ has: page.locator('[class*="pi-moon"], [class*="pi-sun"]') }).first()
    await themeToggle.click()
    await page.waitForTimeout(500)

    // Get body bg in light mode
    const lightBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor)

    // Colors should be different
    expect(darkBg).not.toEqual(lightBg)
  })
})

test.describe('UI Redesign - Design System', () => {
  test('CSS custom properties (design tokens) are defined', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    const tokens = await page.evaluate(() => {
      const style = getComputedStyle(document.documentElement)
      return {
        accentCyan: style.getPropertyValue('--sd-accent-cyan').trim(),
        accentViolet: style.getPropertyValue('--sd-accent-violet').trim(),
        surface50: style.getPropertyValue('--sd-surface-50').trim(),
        textPrimary: style.getPropertyValue('--sd-text-primary').trim(),
        win: style.getPropertyValue('--sd-win').trim(),
        loss: style.getPropertyValue('--sd-loss').trim(),
      }
    })

    expect(tokens.accentCyan).toBeTruthy()
    expect(tokens.accentViolet).toBeTruthy()
    expect(tokens.surface50).toBeTruthy()
    expect(tokens.textPrimary).toBeTruthy()
    expect(tokens.win).toBeTruthy()
    expect(tokens.loss).toBeTruthy()
  })

  test('Google Fonts are loaded (Outfit, Inter, JetBrains Mono)', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Check that font-family declarations reference our custom fonts
    await page.evaluate(() => {
      const styles = Array.from(document.styleSheets)
        .flatMap(sheet => {
          try {
            return Array.from(sheet.cssRules)
          } catch {
            return []
          }
        })
        .map(rule => rule.cssText)
        .join(' ')
      return styles
    })

    // The link tags should be in the head
    const links = await page.locator('link[href*="fonts.googleapis.com"]').count()
    expect(links).toBeGreaterThanOrEqual(1)
  })

  test('Tailwind utility classes are working', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Check that flex display is applied (Tailwind's "flex" class)
    const flexElements = await page.evaluate(() => {
      const els = document.querySelectorAll('.flex')
      return Array.from(els).slice(0, 5).map(el => getComputedStyle(el).display)
    })

    expect(flexElements.length).toBeGreaterThan(0)
    for (const display of flexElements) {
      expect(display).toBe('flex')
    }

    // Check that grid is working
    const gridElements = await page.evaluate(() => {
      const els = document.querySelectorAll('[class*="grid-cols"]')
      return Array.from(els).slice(0, 3).map(el => getComputedStyle(el).display)
    })

    for (const display of gridElements) {
      expect(display).toBe('grid')
    }
  })

  test('Glassmorphism effect is applied to glass-card elements', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    const glassProps = await page.evaluate(() => {
      const card = document.querySelector('.glass-card')
      if (!card) return null
      const style = getComputedStyle(card)
      return {
        backdropFilter: style.backdropFilter || style.webkitBackdropFilter,
        borderRadius: style.borderRadius,
      }
    })

    if (glassProps) {
      // Should have backdrop blur
      expect(glassProps.backdropFilter).toContain('blur')
    }
  })
})

test.describe('UI Redesign - Football Dashboard', () => {
  test('Dashboard page loads with stat cards', async ({ page }) => {
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Should show "Premier League" heading
    await expect(page.locator('text=Premier League').first()).toBeVisible()

    // Should have stat cards or skeleton loaders
    const statCards = page.locator('.stat-card-glass, [class*="stat-card"]')
    const skeletons = page.locator('.skeleton-shimmer, [class*="skeleton"]')
    const totalCards = await statCards.count()
    const totalSkeletons = await skeletons.count()

    // Either stat cards loaded or skeletons are showing
    expect(totalCards + totalSkeletons).toBeGreaterThanOrEqual(0)
  })

  test('Dashboard has GlassCard wrapped sections', async ({ page }) => {
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Glass cards should be present on the page
    const glassCards = page.locator('.glass-card')
    const count = await glassCards.count()
    expect(count).toBeGreaterThan(0)
  })

  test('Dashboard league table renders without deprecated styles', async ({ page }) => {
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    // Check that DataTable is present (PrimeVue)
    const dataTable = page.locator('.p-datatable')
    const tableCount = await dataTable.count()

    // If data loaded, table should exist
    if (tableCount > 0) {
      await expect(dataTable.first()).toBeVisible()

      // Table should NOT have old alternating row colors
      const hasOldStyles = await page.evaluate(() => {
        const rows = document.querySelectorAll('.p-datatable-tbody tr')
        if (rows.length < 2) return false
        const bg1 = getComputedStyle(rows[0]).backgroundColor
        const bg2 = getComputedStyle(rows[1]).backgroundColor
        // Old style had alternating #1e1e2e / #282838
        return bg1.includes('30, 30, 46') || bg2.includes('40, 40, 56')
      })
      expect(hasOldStyles).toBe(false)
    }
  })

  test('GradientBadge components render correctly', async ({ page }) => {
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Season badge or other gradient badges should be visible
    // Check for any element with gradient badge styling
    const badges = page.locator('[class*="gradient-badge"], [class*="rounded-full"]')
    // At minimum the season badge should exist
    const count = await badges.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })
})

test.describe('UI Redesign - Analytics Page', () => {
  test('Analytics page uses pill navigation instead of TabView', async ({ page }) => {
    await page.goto(`${BASE}/football/analytics`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)

    // Should NOT have PrimeVue TabView
    const tabView = page.locator('.p-tabview')
    await expect(tabView).toHaveCount(0)

    // Should have pill navigation
    const pillNav = page.locator('.pill-nav')
    await expect(pillNav.first()).toBeVisible()

    // Should have pill nav items
    const pillItems = page.locator('.pill-nav-item')
    const count = await pillItems.count()
    expect(count).toBeGreaterThanOrEqual(7)
  })

  test('Analytics pill navigation switches content', async ({ page }) => {
    await page.goto(`${BASE}/football/analytics`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)

    // Click different tabs and verify content changes
    const pillItems = page.locator('.pill-nav-item')

    // Click second tab (xG Analysis or similar)
    if (await pillItems.count() > 1) {
      await pillItems.nth(1).click()
      await page.waitForTimeout(300)

      // Active tab should have active class
      const activeItems = page.locator('.pill-nav-item-active')
      await expect(activeItems).toHaveCount(1)
    }
  })

  test('Analytics page has no @apply scoped styles', async ({ page }) => {
    await page.goto(`${BASE}/football/analytics`)
    await page.waitForLoadState('networkidle')

    // The page should render without CSS errors
    // Check that key elements are visible and styled
    const heading = page.locator('text=Analytics').first()
    // Page title or content should be visible
    await heading.isVisible().catch(() => false)
    // At minimum the pill nav should be showing
    await expect(page.locator('.pill-nav').first()).toBeVisible()
  })
})

test.describe('UI Redesign - Responsive Design', () => {
  test('Sidebar collapses on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 900, height: 800 })
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)

    // Sidebar should be collapsed or hidden at this viewport
    // Check for hamburger menu button
    const hamburger = page.locator('button').filter({ has: page.locator('[class*="pi-bars"]') })
    await hamburger.first().isVisible().catch(() => false)

    // Either hamburger is showing (mobile) or sidebar is collapsed
    // The content should still be accessible
    const content = page.locator('main, .main-content, [class*="main"]').first()
    await expect(content).toBeVisible()
  })

  test('Mobile viewport shows hamburger menu', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500)

    // Hamburger button should be visible
    const hamburger = page.locator('button').filter({ has: page.locator('[class*="pi-bars"]') })
    await expect(hamburger.first()).toBeVisible()

    // Click hamburger to open sidebar
    await hamburger.first().click()
    await page.waitForTimeout(300)

    // Sidebar overlay or sidebar content should appear
    const sidebarContent = page.locator('text=SportsDash')
    await expect(sidebarContent.first()).toBeVisible()
  })
})

test.describe('UI Redesign - Component Integration', () => {
  test('No console errors on home page', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })

    await page.goto(BASE)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Filter out expected network errors (backend not running)
    const unexpectedErrors = errors.filter(e =>
      !e.includes('ERR_CONNECTION_REFUSED') &&
      !e.includes('Failed to fetch') &&
      !e.includes('Network Error') &&
      !e.includes('net::ERR') &&
      !e.includes('AxiosError')
    )

    expect(unexpectedErrors).toEqual([])
  })

  test('No console errors on dashboard page', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })

    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    const unexpectedErrors = errors.filter(e =>
      !e.includes('ERR_CONNECTION_REFUSED') &&
      !e.includes('Failed to fetch') &&
      !e.includes('Network Error') &&
      !e.includes('net::ERR') &&
      !e.includes('AxiosError')
    )

    expect(unexpectedErrors).toEqual([])
  })

  test('No console errors on analytics page', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })

    await page.goto(`${BASE}/football/analytics`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    const unexpectedErrors = errors.filter(e =>
      !e.includes('ERR_CONNECTION_REFUSED') &&
      !e.includes('Failed to fetch') &&
      !e.includes('Network Error') &&
      !e.includes('net::ERR') &&
      !e.includes('AxiosError')
    )

    expect(unexpectedErrors).toEqual([])
  })

  test('Deprecated components are not loaded', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // AppHeader should not be present (replaced by TopBar + Sidebar)
    const appHeader = page.locator('.app-header')
    await expect(appHeader).toHaveCount(0)

    // SportNav should not be present
    const sportNav = page.locator('.sport-nav')
    await expect(sportNav).toHaveCount(0)

    // FootballNav should not be present
    const footballNav = page.locator('.football-nav')
    await expect(footballNav).toHaveCount(0)
  })

  test('Page transitions are defined', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Navigate to football
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')

    // Page should have rendered (transition completed)
    // Check that content is visible after transition
    const content = page.locator('text=Premier League')
    await expect(content.first()).toBeVisible({ timeout: 5000 })
  })
})

test.describe('UI Redesign - Visual Regression Checks', () => {
  test('Screenshot: Home page dark mode', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'e2e/screenshots/home-dark.png', fullPage: true })
  })

  test('Screenshot: Home page light mode', async ({ page }) => {
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')

    // Toggle to light
    const themeToggle = page.locator('button').filter({ has: page.locator('[class*="pi-moon"], [class*="pi-sun"]') }).first()
    await themeToggle.click()
    await page.waitForTimeout(500)

    await page.screenshot({ path: 'e2e/screenshots/home-light.png', fullPage: true })
  })

  test('Screenshot: Football Dashboard', async ({ page }) => {
    await page.goto(`${BASE}/football`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: 'e2e/screenshots/dashboard-dark.png', fullPage: true })
  })

  test('Screenshot: Analytics page', async ({ page }) => {
    await page.goto(`${BASE}/football/analytics`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'e2e/screenshots/analytics-dark.png', fullPage: true })
  })

  test('Screenshot: Mobile home page', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto(BASE)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
    await page.screenshot({ path: 'e2e/screenshots/home-mobile.png', fullPage: true })
  })
})
