import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeToggle } from '../theme'

export default function Login() {
  const { login, user, loading } = useAuth()
  const { t } = useI18n()
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
        <div className="auth-card-head">
          <div>
            <h1>{t('login.title')}</h1>
            <p className="muted">{t('login.subtitle')}</p>
          </div>
          <div className="auth-tools">
            <LanguageSwitcher variant="light" />
            <ThemeToggle />
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>{t('login.email')}</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </div>
        <div className="field">
          <label>{t('login.password')}</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </div>
        <button className="btn" style={{ width: '100%' }} disabled={busy}>
          {busy ? t('common.saving') : t('login.submit')}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          {t('login.noAccount')} <Link to="/register">{t('login.register')}</Link>
        </p>
        <p className="muted">
          <Link to="/">{t('landing.backHome')}</Link>
        </p>
      </form>
    </div>
  )
}
