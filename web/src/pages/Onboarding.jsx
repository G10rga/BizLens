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
  validateTaxProfile,
} from '../validation'

const TYPE_KEYS = ['bakery', 'restaurant', 'retail', 'pharmacy', 'salon', 'other']
const CITY_KEYS = ['Tbilisi', 'Batumi', 'Kutaisi', 'Other']
const LEGAL_FORMS = ['ie', 'llc']
const TAX_REGIMES_IE = ['micro', 'small', 'general', 'unsure']
const TURNOVER_BANDS = ['under_30k', '30k_100k', '100k_500k', 'over_500k']

export default function Onboarding() {
  const { user, refresh } = useAuth()
  const { t, lang } = useI18n()
  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const [profile, setProfile] = useState({
    name: '',
    business_type: '',
    city: '',
  })
  const [tax, setTax] = useState({
    legal_form: '',
    tax_regime: '',
    is_vat_payer: '',
    has_employees: '',
    pension_participants: true,
    llc_distributes_profit: false,
    turnover_band: '',
  })
  const [obligations, setObligations] = useState([])
  const [recommendedLabel, setRecommendedLabel] = useState('')
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

  const obligationTitle = (o) => (lang === 'ka' ? o.title_ka || o.title_en : o.title_en || o.title_ka)
  const obligationDetail = (o) => (lang === 'ka' ? o.detail_ka || o.detail_en : o.detail_en || o.detail_ka)

  const buildTaxPayload = () => {
    const isVat =
      tax.is_vat_payer === 'unsure'
        ? 'unsure'
        : tax.is_vat_payer === true || tax.is_vat_payer === 'true' || tax.is_vat_payer === 'yes'
    const hasEmp = tax.has_employees === true || tax.has_employees === 'true' || tax.has_employees === 'yes'
    const payload = {
      legal_form: tax.legal_form,
      tax_regime: tax.legal_form === 'llc' ? 'llc_estonian' : tax.tax_regime,
      is_vat_payer: isVat,
      has_employees: hasEmp,
      pension_participants: Boolean(tax.pension_participants),
      llc_distributes_profit: tax.legal_form === 'llc' ? Boolean(tax.llc_distributes_profit) : false,
      turnover_band: tax.turnover_band || undefined,
      recommend: tax.tax_regime === 'unsure' || tax.is_vat_payer === 'unsure',
    }
    return payload
  }

  const fetchRecommendation = async () => {
    setBusy(true)
    setError('')
    try {
      const payload = buildTaxPayload()
      const res = await api('/onboarding/tax-recommend', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      const s = res.suggestion || {}
      setTax((prev) => ({
        ...prev,
        legal_form: s.legal_form || prev.legal_form,
        tax_regime: s.tax_regime,
        is_vat_payer: s.is_vat_payer ? 'true' : 'false',
        has_employees: s.has_employees ? 'true' : prev.has_employees,
      }))
      setObligations(res.obligations || [])
      setRecommendedLabel(
        t('onboarding.recommended', {
          regime: t(`onboarding.taxRegimes.${s.tax_regime}`) || s.tax_regime,
        }),
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

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
        const nextErrors = validateTaxProfile(tax, t)
        if (Object.keys(nextErrors).length) {
          setErrors(nextErrors)
          setError(firstError(nextErrors))
          return
        }
        const res = await api('/onboarding/tax-profile', {
          method: 'POST',
          body: JSON.stringify(buildTaxPayload()),
        })
        setObligations(res.obligations || [])
        setStep(3)
      } else if (step === 3) {
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
        setStep(4)
      } else if (step === 4) {
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
        setStep(5)
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
      setStep(5)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const expenseLabel = (name) => t(`onboarding.expenses.${name}`) || name
  const regimeOptions = tax.legal_form === 'llc' ? ['llc_estonian'] : TAX_REGIMES_IE

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

        {step === 2 && (
          <>
            <h2 style={{ marginTop: 0 }}>{t('onboarding.taxTitle')}</h2>
            <p className="muted" style={{ marginTop: 0 }}>{t('onboarding.taxSubtitle')}</p>

            <div className="field">
              <label>{t('onboarding.legalForm')}</label>
              <select
                className={errors.legal_form ? 'invalid' : ''}
                value={tax.legal_form}
                onChange={(e) => {
                  const legal_form = e.target.value
                  setTax({
                    ...tax,
                    legal_form,
                    tax_regime: legal_form === 'llc' ? 'llc_estonian' : tax.tax_regime === 'llc_estonian' ? '' : tax.tax_regime,
                  })
                  setObligations([])
                  setRecommendedLabel('')
                }}
              >
                <option value="">{t('onboarding.selectLegalForm')}</option>
                {LEGAL_FORMS.map((v) => (
                  <option key={v} value={v}>{t(`onboarding.legalForms.${v}`)}</option>
                ))}
              </select>
              {errors.legal_form && <p className="field-error">{errors.legal_form}</p>}
            </div>

            <div className="field">
              <label>{t('onboarding.taxRegime')}</label>
              <select
                className={errors.tax_regime ? 'invalid' : ''}
                value={tax.tax_regime}
                disabled={!tax.legal_form}
                onChange={(e) => {
                  setTax({ ...tax, tax_regime: e.target.value })
                  setObligations([])
                }}
              >
                <option value="">{t('onboarding.selectTaxRegime')}</option>
                {regimeOptions.map((v) => (
                  <option key={v} value={v}>{t(`onboarding.taxRegimes.${v}`)}</option>
                ))}
              </select>
              {errors.tax_regime && <p className="field-error">{errors.tax_regime}</p>}
            </div>

            {(tax.tax_regime === 'unsure' || tax.is_vat_payer === 'unsure') && (
              <div className="field">
                <label>{t('onboarding.turnoverBand')}</label>
                <select
                  className={errors.turnover_band ? 'invalid' : ''}
                  value={tax.turnover_band}
                  onChange={(e) => setTax({ ...tax, turnover_band: e.target.value })}
                >
                  <option value="">{t('onboarding.selectTurnover')}</option>
                  {TURNOVER_BANDS.map((b) => (
                    <option key={b} value={b}>{t(`onboarding.turnoverBands.${b}`)}</option>
                  ))}
                </select>
                {errors.turnover_band && <p className="field-error">{errors.turnover_band}</p>}
                <button
                  type="button"
                  className="btn ghost"
                  style={{ marginTop: '0.5rem' }}
                  disabled={busy || !tax.turnover_band}
                  onClick={fetchRecommendation}
                >
                  {t('onboarding.getRecommendation')}
                </button>
                {recommendedLabel && <p className="muted">{recommendedLabel}</p>}
              </div>
            )}

            <div className="field">
              <label>{t('onboarding.vatPayer')}</label>
              <select
                className={errors.is_vat_payer ? 'invalid' : ''}
                value={tax.is_vat_payer === true ? 'true' : tax.is_vat_payer === false ? 'false' : tax.is_vat_payer}
                onChange={(e) => setTax({ ...tax, is_vat_payer: e.target.value })}
              >
                <option value="">{t('onboarding.selectTaxRegime')}</option>
                <option value="true">{t('onboarding.vatYes')}</option>
                <option value="false">{t('onboarding.vatNo')}</option>
                <option value="unsure">{t('onboarding.vatUnsure')}</option>
              </select>
              {errors.is_vat_payer && <p className="field-error">{errors.is_vat_payer}</p>}
            </div>

            <div className="field">
              <label>{t('onboarding.hasEmployees')}</label>
              <select
                className={errors.has_employees ? 'invalid' : ''}
                value={tax.has_employees === true ? 'true' : tax.has_employees === false ? 'false' : tax.has_employees}
                onChange={(e) => setTax({ ...tax, has_employees: e.target.value })}
              >
                <option value="">—</option>
                <option value="true">{t('onboarding.yes')}</option>
                <option value="false">{t('onboarding.no')}</option>
              </select>
              {errors.has_employees && <p className="field-error">{errors.has_employees}</p>}
            </div>

            {(tax.has_employees === true || tax.has_employees === 'true') && (
              <div className="field">
                <label>{t('onboarding.pensionParticipants')}</label>
                <select
                  value={tax.pension_participants ? 'true' : 'false'}
                  onChange={(e) => setTax({ ...tax, pension_participants: e.target.value === 'true' })}
                >
                  <option value="true">{t('onboarding.yes')}</option>
                  <option value="false">{t('onboarding.no')}</option>
                </select>
              </div>
            )}

            {tax.legal_form === 'llc' && (
              <div className="field">
                <label>{t('onboarding.llcDistributes')}</label>
                <select
                  value={tax.llc_distributes_profit ? 'true' : 'false'}
                  onChange={(e) => setTax({ ...tax, llc_distributes_profit: e.target.value === 'true' })}
                >
                  <option value="false">{t('onboarding.no')}</option>
                  <option value="true">{t('onboarding.yes')}</option>
                </select>
              </div>
            )}

            {obligations.length > 0 && (
              <div className="card" style={{ marginTop: '0.75rem' }}>
                <h3 style={{ marginTop: 0 }}>{t('onboarding.obligationsTitle')}</h3>
                <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
                  {obligations.map((o) => (
                    <li key={o.code} style={{ marginBottom: '0.5rem' }}>
                      <strong>{obligationTitle(o)}</strong>
                      <div className="muted">{obligationDetail(o)}</div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <p className="muted" style={{ fontSize: '0.85rem' }}>{t('onboarding.taxDisclaimer')}</p>
          </>
        )}

        {step === 3 &&
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

        {step === 4 && (
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

        {step === 5 && (
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
          {busy ? t('common.saving') : step === 5 ? t('onboarding.finish') : t('common.next')}
        </button>
        <p className="muted" style={{ marginTop: '1rem' }}>
          <Link to="/">{t('landing.backHome')}</Link>
        </p>
      </div>
    </div>
  )
}
