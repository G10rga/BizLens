import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Register() {
  const { register, user, loading } = useAuth()
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!loading && user) return <Navigate to="/onboarding" replace />

  const onSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await register(form)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>რეგისტრაცია</h1>
        <p className="muted">შექმენით BizLens ანგარიში</p>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>სახელი</label>
          <input
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
        </div>
        <div className="field">
          <label>ელფოსტა</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div className="field">
          <label>პაროლი</label>
          <input
            type="password"
            required
            minLength={6}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <button className="btn" style={{ width: '100%' }} disabled={busy}>
          {busy ? '...' : 'შექმნა'}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          უკვე გაქვთ ანგარიში? <Link to="/login">შესვლა</Link>
        </p>
      </form>
    </div>
  )
}
