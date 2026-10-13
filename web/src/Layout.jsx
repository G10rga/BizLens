import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import { LanguageSwitcher, useI18n } from './i18n'
import { ThemeToggle, useTheme } from './theme'

function Ico({ children }) {
  return (
    <svg className="nav-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      {children}
    </svg>
  )
}

const links = [
  { to: '/pos', key: 'nav.pos', ico: <Ico><rect x="4" y="4" width="16" height="16" rx="3" /><path d="M8 9h8M8 12h5" /></Ico> },
  { to: '/products', key: 'nav.products', ico: <Ico><path d="M4 8l8-4 8 4v10l-8 4-8-4z" /><path d="M12 12v10M4 8l8 4 8-4" /></Ico> },
  { to: '/today', key: 'nav.today', ico: <Ico><rect x="4" y="5" width="16" height="15" rx="2" /><path d="M8 3v4M16 3v4M4 10h16" /></Ico> },
  { to: '/lens', key: 'nav.lens', ico: <Ico><circle cx="12" cy="12" r="4" /><rect x="3" y="7" width="18" height="12" rx="2" /></Ico> },
  { to: '/dashboard', key: 'nav.dashboard', ico: <Ico><path d="M4 16l5-5 4 3 7-8" /><path d="M14 6h6v6" /></Ico> },
  { to: '/alerts', key: 'nav.alerts', ico: <Ico><path d="M12 4a6 6 0 016 6c0 7 2 7 2 7H4s2 0 2-7a6 6 0 016-6z" /><path d="M10 20h4" /></Ico> },
  { to: '/csv', key: 'nav.csv', ico: <Ico><path d="M12 4v12M8 12l4 4 4-4" /><path d="M5 20h14" /></Ico> },
  { to: '/expenses', key: 'nav.expenses', ico: <Ico><rect x="4" y="5" width="16" height="14" rx="2" /><path d="M8 10h8M8 14h5" /></Ico> },
  { to: '/settings', key: 'nav.settings', ico: <Ico><circle cx="12" cy="12" r="3" /><path d="M12 3v2M12 19v2M4.9 6.5l1.5 1.5M17.6 16l1.5 1.5M3 12h2M19 12h2M4.9 17.5l1.5-1.5M17.6 8l1.5-1.5" /></Ico> },
]

export default function Layout() {
  const { user, business, logout } = useAuth()
  const { t, money } = useI18n()
  const { theme } = useTheme()
  const location = useLocation()
  const [navOpen, setNavOpen] = useState(false)
  const switchTone = theme === 'dark' ? 'dark' : 'light'

  useEffect(() => {
    setNavOpen(false)
  }, [location.pathname])

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 1100) setNavOpen(false)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    document.body.classList.toggle('nav-locked', navOpen)
    return () => document.body.classList.remove('nav-locked')
  }, [navOpen])

  return (
    <div className={`app-shell${navOpen ? ' nav-open' : ''}`}>
      <header className="shell-top">
        <button
          type="button"
          className="icon-btn"
          aria-label={t('common.menu')}
          aria-expanded={navOpen}
          onClick={() => setNavOpen(true)}
        >
          ☰
        </button>
        <Link to="/" className="brand-home shell-top-brand">
          <div className="brand-mark">B</div>
          <strong>{t('brand.name')}</strong>
        </Link>
      </header>

      {navOpen && (
        <button
          type="button"
          className="nav-backdrop"
          aria-label={t('common.closeMenu')}
          onClick={() => setNavOpen(false)}
        />
      )}

      <aside className="sidebar">
        <div className="brand">
          <Link to="/" className="brand-home">
            <div className="brand-mark">B</div>
            <div>
              <strong>{t('brand.name')}</strong>
              <span>{t('brand.tagline')}</span>
            </div>
          </Link>
          <button
            type="button"
            className="icon-btn sidebar-close"
            aria-label={t('common.closeMenu')}
            onClick={() => setNavOpen(false)}
          >
            ×
          </button>
        </div>
        <p className="sidebar-label">{t('nav.workspace')}</p>
        <div className="sidebar-tools">
          <LanguageSwitcher variant={switchTone} />
          <ThemeToggle variant={switchTone} />
        </div>
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            {l.ico}
            <span>{t(l.key)}</span>
          </NavLink>
        ))}
        <div className="sidebar-help">
          <strong>{t('nav.needHelp')}</strong>
          <Link to="/">{t('nav.support')}</Link>
        </div>
        <div className="sidebar-foot">
          <div className="sidebar-user">
            <div className="sidebar-avatar">{(user?.full_name || user?.email || 'U').slice(0, 1)}</div>
            <div>
              <div>{user?.full_name || business?.name || '—'}</div>
              <div className="muted sidebar-muted">{t('nav.online')}</div>
            </div>
          </div>
          <div className="muted sidebar-muted">
            {t('nav.cashOnHand', { amount: money(business?.cash_on_hand) })}
          </div>
          <button className="btn ghost sidebar-action lgout" type="button" onClick={logout}>
            {t('common.logout')}
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
