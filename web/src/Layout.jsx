import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from './auth'
import { money } from './api'

const links = [
  { to: '/pos', label: 'POS / გაყიდვები' },
  { to: '/products', label: 'პროდუქტები' },
  { to: '/today', label: 'დღევანდელი გაყიდვები' },
  { to: '/dashboard', label: 'დაფა' },
  { to: '/alerts', label: 'გაფრთხილებები' },
  { to: '/csv', label: 'CSV იმპორტი' },
  { to: '/expenses', label: 'ხარჯები' },
  { to: '/settings', label: 'პარამეტრები' },
]

export default function Layout() {
  const { user, business, logout } = useAuth()

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">B</div>
          <div>
            <strong>BizLens</strong>
            <span>ბიზლენსი</span>
          </div>
        </div>
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            {l.label}
          </NavLink>
        ))}
        <div className="sidebar-foot">
          <div>{business?.name || '—'}</div>
          <div className="muted" style={{ color: 'rgba(255,255,255,0.7)' }}>
            ნაღდი: {money(business?.cash_on_hand)}
          </div>
          <div style={{ marginTop: '0.5rem' }}>{user?.email}</div>
          <button className="btn ghost" style={{ marginTop: '0.75rem', width: '100%', color: '#fff', borderColor: 'rgba(255,255,255,0.25)' }} onClick={logout}>
            გამოსვლა
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
