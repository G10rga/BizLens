import { Link, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from './auth'
import { LanguageSwitcher, useI18n } from './i18n'

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

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Link to="/" className="brand-home">
            <div className="brand-mark">B</div>
            <div>
              <strong>{t('brand.name')}</strong>
              <span>{t('brand.tagline')}</span>
            </div>
          </Link>
          <LanguageSwitcher />
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
          <div className="muted" style={{ color: 'rgba(255,255,255,0.7)' }}>
            {t('nav.cashOnHand', { amount: money(business?.cash_on_hand) })}
          </div>
          <div style={{ marginTop: '0.5rem' }}>{user?.email}</div>
          <Link className="btn ghost" style={{ marginTop: '0.75rem', width: '100%', color: '#fff', borderColor: 'rgba(255,255,255,0.25)', textDecoration: 'none' }} to="/">
            {t('nav.home')}
          </Link>
          <button className="btn ghost" style={{ marginTop: '0.5rem', width: '100%', color: '#fff', borderColor: 'rgba(255,255,255,0.25)' }} onClick={logout}>
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
