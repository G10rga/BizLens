import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { useI18n } from '../i18n'

const TYPE_KEYS = ['bakery', 'restaurant', 'retail', 'pharmacy', 'salon', 'other']
const CITY_KEYS = ['Tbilisi', 'Batumi', 'Kutaisi', 'Other']

export default function Settings() {
  const { user, business, refresh, logout } = useAuth()
  const { lang, setLanguage, t } = useI18n()
  const [form, setForm] = useState({
    language: user?.language || lang,
    full_name: user?.full_name || '',
    name: business?.name || '',
    business_type: business?.business_type || 'other',
    city: business?.city || 'Tbilisi',
  })
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setForm((f) => (f.language === lang ? f : { ...f, language: lang }))
  }, [lang])

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
      setMsg(t('settings.saved'))
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
          <h1>{t('settings.title')}</h1>
          <p className="muted">{user?.email}</p>
        </div>
        <button className="btn danger" onClick={logout}>{t('common.logout')}</button>
      </div>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}
      <form className="card" onSubmit={save} style={{ maxWidth: 520 }}>
        <div className="field">
          <label>{t('settings.fullName')}</label>
          <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
        </div>
        <div className="field">
          <label>{t('settings.language')}</label>
          <select
            value={form.language}
            onChange={(e) => {
              const language = e.target.value
              setForm({ ...form, language })
              setLanguage(language)
            }}
          >
            <option value="ka">{t('lang.ka')}</option>
            <option value="en">{t('lang.en')}</option>
          </select>
        </div>
        <div className="field">
          <label>{t('settings.business')}</label>
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </div>
        <div className="field">
          <label>{t('settings.type')}</label>
          <select value={form.business_type} onChange={(e) => setForm({ ...form, business_type: e.target.value })}>
            {TYPE_KEYS.map((v) => (
              <option key={v} value={v}>{t(`onboarding.types.${v}`)}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t('settings.city')}</label>
          <select value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}>
            {CITY_KEYS.map((c) => (
              <option key={c} value={c}>{t(`onboarding.cities.${c}`)}</option>
            ))}
          </select>
        </div>
        <button className="btn" disabled={busy}>{busy ? t('common.saving') : t('common.save')}</button>
      </form>
    </>
  )
}
