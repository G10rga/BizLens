import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import { LanguageSwitcher, useI18n } from './i18n'
import { ThemeToggle } from './theme'

const links = [
  { to: '/', key: 'nav.home' },
  { to: '/pos', key: 'nav.pos' },
  { to: '/lens', key: 'nav.lens' },
  { to: '/products', key: 'nav.products' },
  { to: '/today', key: 'nav.today' },
  { to: '/dashboard', key: 'nav.dashboard' },
  { to: '/alerts', key: 'nav.alerts' },
  { to: '/csv', key: 'nav.csv' },
  { to: '/expenses', key: 'nav.expenses' },
  { to: '/settings', key: 'nav.settings' },
]

export default function Layout() {
  const { user, business, logout } = useAuth()
  const { t, money } = useI18n()
  const location = useLocation()
  const [navOpen, setNavOpen] = useState(false)

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
        <div className="shell-top-tools">
          <LanguageSwitcher />
          <ThemeToggle variant="sidebar" />
        </div>
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
        <div className="sidebar-tools">
          <LanguageSwitcher />
          <ThemeToggle variant="sidebar" />
        </div>
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
          >
            {t(l.key)}
          </NavLink>
        ))}
        <div className="sidebar-foot">
          <div>{business?.name || '—'}</div>
          <div className="muted sidebar-muted">
            {t('nav.cashOnHand', { amount: money(business?.cash_on_hand) })}
          </div>
          <div className="sidebar-email">{user?.email}</div>
          <Link className="btn ghost sidebar-action" to="/">
            {t('nav.home')}
          </Link>
          <button className="btn ghost sidebar-action" type="button" onClick={logout}>
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
