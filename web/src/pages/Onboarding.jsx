import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeToggle } from '../theme'
import {
  firstError,
  validateBusinessProfile,
  validateCash,
  validateExpenses,
  validateSuppliers,
} from '../validation'

const TYPE_KEYS = ['bakery', 'restaurant', 'retail', 'pharmacy', 'salon', 'other']
const CITY_KEYS = ['Tbilisi', 'Batumi', 'Kutaisi', 'Other']

export default function Onboarding() {
  const { user, refresh } = useAuth()
  const { t } = useI18n()
  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [profile, setProfile] = useState({
    name: '',
    business_type: '',
    city: '',
  })
  const [expenses, setExpenses] = useState([
    { name: 'rent', amount: '', due_day: 1 },
    { name: 'salaries', amount: '', due_day: 1 },
    { name: 'utilities', amount: '', due_day: 10 },
    { name: 'other', amount: '', due_day: 15 },
  ])
  const [suppliers, setSuppliers] = useState([
    { name: '', amount: '', every_n_days: '', next_due_date: new Date().toISOString().slice(0, 10) },
  ])
  const [cash, setCash] = useState('')

  if (user?.onboarding_complete) return <Navigate to="/pos" replace />

  const next = async () => {
    setBusy(true)
    setError('')
    setErrors({})
    try {
      if (step === 1) {
        const nextErrors = validateBusinessProfile(profile, t)
        if (Object.keys(nextErrors).length) {
          setErrors(nextErrors)
          setError(firstError(nextErrors))
          return
        }
        await api('/onboarding/profile', {
          method: 'POST',
          body: JSON.stringify({
            ...profile,
            name: profile.name.trim(),
          }),
        })
        setStep(2)
      } else if (step === 2) {
        const nextErrors = validateExpenses(expenses, t)
        if (Object.keys(nextErrors).length) {
          setErrors(nextErrors)
          setError(firstError(nextErrors))
          return
        }
        await api('/onboarding/expenses', {
          method: 'POST',
          body: JSON.stringify({
            expenses: expenses.map((e) => ({
              ...e,
              amount: Number(e.amount),
              due_day: Number(e.due_day),
            })),
          }),
        })
        setStep(3)
      } else if (step === 3) {
        const { skip, errors: nextErrors } = validateSuppliers(suppliers, t)
        if (Object.keys(nextErrors).length) {
          setErrors(nextErrors)
          setError(firstError(nextErrors))
          return
        }
        if (skip) {
          await api('/onboarding/suppliers', { method: 'POST', body: JSON.stringify({ skip: true }) })
        } else {
          await api('/onboarding/suppliers', {
            method: 'POST',
            body: JSON.stringify({
              suppliers: suppliers
                .filter((s) => (s.name || '').trim() || String(s.amount || '').trim() || String(s.every_n_days || '').trim())
                .map((s) => ({
                  ...s,
                  name: s.name.trim(),
                  amount: Number(s.amount),
                  every_n_days: Number(s.every_n_days),
                })),
            }),
          })
        }
        setStep(4)
      } else {
        const cashErr = validateCash(cash, t)
        if (cashErr) {
          setErrors({ cash: cashErr })
          setError(cashErr)
          return
        }
        await api('/onboarding/cash', {
          method: 'POST',
          body: JSON.stringify({ cash_on_hand: Number(cash) }),
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
    setError('')
    setErrors({})
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
      <div className="auth-card wide">
        <div className="auth-card-head">
          <div>
            <h1>{t('onboarding.title', { step })}</h1>
            <p className="muted">{t('onboarding.subtitle')}</p>
          </div>
          <div className="auth-tools">
            <LanguageSwitcher variant="light" />
            <ThemeToggle />
          </div>
        </div>
        {error && <div className="error">{error}</div>}

        {step === 1 && (
          <>
            <div className="field">
              <label>{t('onboarding.businessName')}</label>
              <input
                className={errors.name ? 'invalid' : ''}
                value={profile.name}
                maxLength={80}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
              />
              {errors.name && <p className="field-error">{errors.name}</p>}
            </div>
            <div className="field">
              <label>{t('onboarding.type')}</label>
              <select
                className={errors.business_type ? 'invalid' : ''}
                value={profile.business_type}
                onChange={(e) => setProfile({ ...profile, business_type: e.target.value })}
              >
                <option value="">{t('onboarding.selectType')}</option>
                {TYPE_KEYS.map((v) => (
                  <option key={v} value={v}>{t(`onboarding.types.${v}`)}</option>
                ))}
              </select>
              {errors.business_type && <p className="field-error">{errors.business_type}</p>}
            </div>
            <div className="field">
              <label>{t('onboarding.city')}</label>
              <select
                className={errors.city ? 'invalid' : ''}
                value={profile.city}
                onChange={(e) => setProfile({ ...profile, city: e.target.value })}
              >
                <option value="">{t('onboarding.selectCity')}</option>
                {CITY_KEYS.map((c) => (
                  <option key={c} value={c}>{t(`onboarding.cities.${c}`)}</option>
                ))}
              </select>
              {errors.city && <p className="field-error">{errors.city}</p>}
            </div>
          </>
        )}

        {step === 2 &&
          expenses.map((exp, i) => (
            <div className="row" key={exp.name}>
              <div className="field" style={{ flex: 2 }}>
                <label>{expenseLabel(exp.name)}</label>
                <input
                  type="text"
                  inputMode="decimal"
                  className={errors[`amount_${i}`] ? 'invalid' : ''}
                  value={exp.amount}
                  onChange={(e) => {
                    const nextEx = [...expenses]
                    nextEx[i] = { ...exp, amount: e.target.value }
                    setExpenses(nextEx)
                  }}
                />
                {errors[`amount_${i}`] && <p className="field-error">{errors[`amount_${i}`]}</p>}
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>{t('common.day')}</label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  step="1"
                  className={errors[`due_${i}`] ? 'invalid' : ''}
                  value={exp.due_day}
                  onChange={(e) => {
                    const nextEx = [...expenses]
                    nextEx[i] = { ...exp, due_day: e.target.value }
                    setExpenses(nextEx)
                  }}
                />
                {errors[`due_${i}`] && <p className="field-error">{errors[`due_${i}`]}</p>}
              </div>
            </div>
          ))}

        {step === 3 && (
          <>
            {suppliers.map((s, i) => (
              <div key={i} className="card" style={{ marginBottom: '0.75rem' }}>
                <div className="field">
                  <label>{t('onboarding.supplier')}</label>
                  <input
                    className={errors[`name_${i}`] ? 'invalid' : ''}
                    maxLength={80}
                    value={s.name}
                    onChange={(e) => {
                      const n = [...suppliers]
                      n[i] = { ...s, name: e.target.value }
                      setSuppliers(n)
                    }}
                  />
                  {errors[`name_${i}`] && <p className="field-error">{errors[`name_${i}`]}</p>}
                </div>
                <div className="row">
                  <div className="field" style={{ flex: 1 }}>
                    <label>{t('onboarding.amountGel')}</label>
                    <input
                      type="text"
                      inputMode="decimal"
                      className={errors[`amount_${i}`] ? 'invalid' : ''}
                      value={s.amount}
                      onChange={(e) => {
                        const n = [...suppliers]
                        n[i] = { ...s, amount: e.target.value }
                        setSuppliers(n)
                      }}
                    />
                    {errors[`amount_${i}`] && <p className="field-error">{errors[`amount_${i}`]}</p>}
                  </div>
                  <div className="field" style={{ flex: 1 }}>
                    <label>{t('onboarding.everyNDays')}</label>
                    <input
                      type="number"
                      min="1"
                      max="365"
                      step="1"
                      className={errors[`n_${i}`] ? 'invalid' : ''}
                      value={s.every_n_days}
                      onChange={(e) => {
                        const n = [...suppliers]
                        n[i] = { ...s, every_n_days: e.target.value }
                        setSuppliers(n)
                      }}
                    />
                    {errors[`n_${i}`] && <p className="field-error">{errors[`n_${i}`]}</p>}
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
            <input
              type="text"
              inputMode="decimal"
              className={errors.cash ? 'invalid' : ''}
              value={cash}
              onChange={(e) => setCash(e.target.value)}
            />
            {errors.cash && <p className="field-error">{errors.cash}</p>}
          </div>
        )}

        <button className="btn" style={{ width: '100%', marginTop: '0.5rem' }} disabled={busy} onClick={next}>
          {busy ? t('common.saving') : step === 4 ? t('onboarding.finish') : t('common.next')}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          <Link to="/">{t('landing.backHome')}</Link>
        </p>
      </div>
    </div>
  )
}
