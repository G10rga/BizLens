import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'

const TYPE_KEYS = ['bakery', 'restaurant', 'retail', 'pharmacy', 'salon', 'other']
const CITY_KEYS = ['Tbilisi', 'Batumi', 'Kutaisi', 'Other']

export default function Onboarding() {
  const { user, refresh } = useAuth()
  const { t } = useI18n()
  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [profile, setProfile] = useState({
    name: '',
    business_type: 'bakery',
    city: 'Tbilisi',
  })
  const [expenses, setExpenses] = useState([
    { name: 'rent', amount: '', due_day: 1 },
    { name: 'salaries', amount: '', due_day: 1 },
    { name: 'utilities', amount: '', due_day: 10 },
    { name: 'other', amount: '', due_day: 15 },
  ])
  const [suppliers, setSuppliers] = useState([
    { name: 'Supplier 1', amount: '', every_n_days: 14, next_due_date: new Date().toISOString().slice(0, 10) },
  ])
  const [cash, setCash] = useState('')

  if (user?.onboarding_complete) return <Navigate to="/pos" replace />

  const next = async () => {
    setBusy(true)
    setError('')
    try {
      if (step === 1) {
        await api('/onboarding/profile', { method: 'POST', body: JSON.stringify(profile) })
        setStep(2)
      } else if (step === 2) {
        await api('/onboarding/expenses', {
          method: 'POST',
          body: JSON.stringify({
            expenses: expenses
              .filter((e) => Number(e.amount) > 0)
              .map((e) => ({ ...e, amount: Number(e.amount), due_day: Number(e.due_day) })),
          }),
        })
        setStep(3)
      } else if (step === 3) {
        await api('/onboarding/suppliers', {
          method: 'POST',
          body: JSON.stringify({
            suppliers: suppliers
              .filter((s) => Number(s.amount) > 0)
              .map((s) => ({
                ...s,
                amount: Number(s.amount),
                every_n_days: Number(s.every_n_days),
              })),
          }),
        })
        setStep(4)
      } else {
        await api('/onboarding/cash', {
          method: 'POST',
          body: JSON.stringify({ cash_on_hand: Number(cash || 0) }),
        })
        await refresh()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const skipSuppliers = async () => {
    setBusy(true)
    try {
      await api('/onboarding/suppliers', { method: 'POST', body: JSON.stringify({ skip: true }) })
      setStep(4)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const expenseLabel = (name) => t(`onboarding.expenses.${name}`) || name

  return (
    <div className="auth-page">
      <div className="auth-card" style={{ width: 'min(560px, 100%)' }}>
        <div className="auth-card-head">
          <div>
            <h1>{t('onboarding.title', { step })}</h1>
            <p className="muted">{t('onboarding.subtitle')}</p>
          </div>
          <LanguageSwitcher variant="light" />
        </div>
        {error && <div className="error">{error}</div>}

        {step === 1 && (
          <>
            <div className="field">
              <label>{t('onboarding.businessName')}</label>
              <input value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} required />
            </div>
            <div className="field">
              <label>{t('onboarding.type')}</label>
              <select value={profile.business_type} onChange={(e) => setProfile({ ...profile, business_type: e.target.value })}>
                {TYPE_KEYS.map((v) => (
                  <option key={v} value={v}>{t(`onboarding.types.${v}`)}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>{t('onboarding.city')}</label>
              <select value={profile.city} onChange={(e) => setProfile({ ...profile, city: e.target.value })}>
                {CITY_KEYS.map((c) => (
                  <option key={c} value={c}>{t(`onboarding.cities.${c}`)}</option>
                ))}
              </select>
            </div>
          </>
        )}

        {step === 2 &&
          expenses.map((exp, i) => (
            <div className="row" key={exp.name}>
              <div className="field" style={{ flex: 2 }}>
                <label>{expenseLabel(exp.name)}</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={exp.amount}
                  onChange={(e) => {
                    const nextEx = [...expenses]
                    nextEx[i] = { ...exp, amount: e.target.value }
                    setExpenses(nextEx)
                  }}
                />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>{t('common.day')}</label>
                <input
                  type="number"
                  min="1"
                  max="28"
                  value={exp.due_day}
                  onChange={(e) => {
                    const nextEx = [...expenses]
                    nextEx[i] = { ...exp, due_day: e.target.value }
                    setExpenses(nextEx)
                  }}
                />
              </div>
            </div>
          ))}

        {step === 3 && (
          <>
            {suppliers.map((s, i) => (
              <div key={i} className="card" style={{ marginBottom: '0.75rem' }}>
                <div className="field">
                  <label>{t('onboarding.supplier')}</label>
                  <input value={s.name} onChange={(e) => {
                    const n = [...suppliers]; n[i] = { ...s, name: e.target.value }; setSuppliers(n)
                  }} />
                </div>
                <div className="row">
                  <div className="field" style={{ flex: 1 }}>
                    <label>{t('onboarding.amountGel')}</label>
                    <input type="number" value={s.amount} onChange={(e) => {
                      const n = [...suppliers]; n[i] = { ...s, amount: e.target.value }; setSuppliers(n)
                    }} />
                  </div>
                  <div className="field" style={{ flex: 1 }}>
                    <label>{t('onboarding.everyNDays')}</label>
                    <input type="number" value={s.every_n_days} onChange={(e) => {
                      const n = [...suppliers]; n[i] = { ...s, every_n_days: e.target.value }; setSuppliers(n)
                    }} />
                  </div>
                </div>
              </div>
            ))}
            <button type="button" className="btn ghost" onClick={skipSuppliers}>{t('onboarding.skip')}</button>
          </>
        )}

        {step === 4 && (
          <div className="field">
            <label>{t('onboarding.cashNow')}</label>
            <input type="number" min="0" step="0.01" value={cash} onChange={(e) => setCash(e.target.value)} />
          </div>
        )}

        <button className="btn" style={{ width: '100%', marginTop: '0.5rem' }} disabled={busy || (step === 1 && !profile.name)} onClick={next}>
          {busy ? t('common.saving') : step === 4 ? t('onboarding.finish') : t('common.next')}
        </button>
      </div>
    </div>
  )
}
