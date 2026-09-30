import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Login() {
  const { login, user, loading } = useAuth()
  const [email, setEmail] = useState('demo@bizlens.ge')
  const [password, setPassword] = useState('demo1234')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!loading && user) {
    return <Navigate to={user.onboarding_complete ? '/pos' : '/onboarding'} replace />
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>BizLens</h1>
        <p className="muted">შედით თქვენს ანგარიშში</p>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>ელფოსტა</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </div>
        <div className="field">
          <label>პაროლი</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </div>
        <button className="btn" style={{ width: '100%' }} disabled={busy}>
          {busy ? '...' : 'შესვლა'}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          ახალი ანგარიში? <Link to="/register">რეგისტრაცია</Link>
        </p>
      </form>
    </div>
  )
}
