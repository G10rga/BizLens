import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'

export default function Register() {
  const { register, user, loading } = useAuth()
  const { lang, t } = useI18n()
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!loading && user) return <Navigate to="/onboarding" replace />

  const onSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await register({ ...form, language: lang })
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
            <h1>{t('register.title')}</h1>
            <p className="muted">{t('register.subtitle')}</p>
          </div>
          <LanguageSwitcher variant="light" />
        </div>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label>{t('register.name')}</label>
          <input
            value={form.full_name}
            onChange={(e) => setForm({ ...form, full_name: e.target.value })}
          />
        </div>
        <div className="field">
          <label>{t('register.email')}</label>
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div className="field">
          <label>{t('register.password')}</label>
          <input
            type="password"
            required
            minLength={6}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <button className="btn" style={{ width: '100%' }} disabled={busy}>
          {busy ? t('common.saving') : t('register.submit')}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          {t('register.haveAccount')} <Link to="/login">{t('register.login')}</Link>
        </p>
      </form>
    </div>
  )
}
