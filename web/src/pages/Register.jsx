import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeToggle } from '../theme'
import { firstError, validateRegister } from '../validation'

export default function Register() {
  const { register, user, loading } = useAuth()
  const { lang, t } = useI18n()
  const [form, setForm] = useState({ email: '', password: '', full_name: '' })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (!loading && user) return <Navigate to="/onboarding" replace />

  const onChange = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value })
    if (errors[field]) setErrors({ ...errors, [field]: '' })
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    const nextErrors = validateRegister(form, t)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) {
      setError(firstError(nextErrors))
      return
    }
    setBusy(true)
    setError('')
    try {
      await register({ ...form, full_name: form.full_name.trim(), language: lang })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit} noValidate>
        <div className="auth-card-head">
          <div>
            <h1>{t('register.title')}</h1>
            <p className="muted">{t('register.subtitle')}</p>
          </div>
          <div className="auth-tools">
            <LanguageSwitcher variant="light" />
            <ThemeToggle />
          </div>
        </div>
        {error && <div className="error">{error}</div>}
        <div className="field">
          <label htmlFor="reg-name">{t('register.name')}</label>
          <input
            id="reg-name"
            autoComplete="name"
            className={errors.full_name ? 'invalid' : ''}
            value={form.full_name}
            onChange={onChange('full_name')}
            maxLength={50}
          />
          {errors.full_name && <p className="field-error">{errors.full_name}</p>}
        </div>
        <div className="field">
          <label htmlFor="reg-email">{t('register.email')}</label>
          <input
            id="reg-email"
            type="email"
            autoComplete="email"
            className={errors.email ? 'invalid' : ''}
            value={form.email}
            onChange={onChange('email')}
            maxLength={254}
          />
          {errors.email && <p className="field-error">{errors.email}</p>}
        </div>
        <div className="field">
          <label htmlFor="reg-password">{t('register.password')}</label>
          <input
            id="reg-password"
            type="password"
            autoComplete="new-password"
            className={errors.password ? 'invalid' : ''}
            value={form.password}
            onChange={onChange('password')}
            maxLength={128}
          />
          <p className="field-hint">{t('register.hintPassword')}</p>
          {errors.password && <p className="field-error">{errors.password}</p>}
        </div>
        <button className="btn" style={{ width: '100%' }} disabled={busy}>
          {busy ? t('common.saving') : t('register.submit')}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          {t('register.haveAccount')} <Link to="/login">{t('register.login')}</Link>
        </p>
        <p className="muted">
          <Link to="/">{t('landing.backHome')}</Link>
        </p>
      </form>
    </div>
  )
}
