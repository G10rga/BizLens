import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'

export default function Settings() {
  const { user, business, refresh, logout } = useAuth()
  const [form, setForm] = useState({
    language: user?.language || 'ka',
    full_name: user?.full_name || '',
    name: business?.name || '',
    business_type: business?.business_type || 'other',
    city: business?.city || 'Tbilisi',
  })
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMsg('')
    try {
      await api('/settings', {
        method: 'PUT',
        body: JSON.stringify({
          language: form.language,
          full_name: form.full_name,
          business: {
            name: form.name,
            business_type: form.business_type,
            city: form.city,
          },
        }),
      })
      await refresh()
      setMsg('შენახულია')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="topbar">
        <div>
          <h1>პარამეტრები</h1>
          <p className="muted">{user?.email}</p>
        </div>
        <button className="btn danger" onClick={logout}>გამოსვლა</button>
      </div>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}
      <form className="card" onSubmit={save} style={{ maxWidth: 520 }}>
        <div className="field">
          <label>სახელი</label>
          <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </div>
        <div className="field">
          <label>ენა</label>
          <select value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
            <option value="ka">ქართული</option>
            <option value="en">English</option>
          </select>
        </div>
        <div className="field">
          <label>ბიზნესი</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="field">
          <label>ტიპი</label>
          <select value={form.business_type} onChange={(e) => setForm({ ...form, business_type: e.target.value })}>
            <option value="bakery">bakery</option>
            <option value="restaurant">restaurant</option>
            <option value="retail">retail</option>
            <option value="pharmacy">pharmacy</option>
            <option value="salon">salon</option>
            <option value="other">other</option>
          </select>
        </div>
        <div className="field">
          <label>ქალაქი</label>
          <select value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}>
            <option>Tbilisi</option>
            <option>Batumi</option>
            <option>Kutaisi</option>
            <option>Other</option>
          </select>
        </div>
        <button className="btn" disabled={busy}>{busy ? '...' : 'შენახვა'}</button>
      </form>
    </>
  )
}
