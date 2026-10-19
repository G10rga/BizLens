import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { useI18n } from '../i18n'

const TYPE_KEYS = ['bakery', 'restaurant', 'retail', 'pharmacy', 'salon', 'other']
const CITY_KEYS = ['Tbilisi', 'Batumi', 'Kutaisi', 'Other']
const LEGAL_FORMS = ['ie', 'llc']
const TAX_REGIMES_IE = ['micro', 'small', 'general']

export default function Settings() {
  const { user, business, refresh, logout } = useAuth()
  const { lang, setLanguage, t } = useI18n()
  const [form, setForm] = useState({
    language: user?.language || lang,
    full_name: user?.full_name || '',
    name: business?.name || '',
    business_type: business?.business_type || 'other',
    city: business?.city || 'Tbilisi',
    legal_form: business?.legal_form || 'ie',
    tax_regime: business?.tax_regime || 'small',
    is_vat_payer: Boolean(business?.is_vat_payer),
    has_employees: Boolean(business?.has_employees),
    pension_participants: business?.pension_participants !== false,
    llc_distributes_profit: Boolean(business?.llc_distributes_profit),
  })
  const [obligations, setObligations] = useState([])
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setForm((f) => (f.language === lang ? f : { ...f, language: lang }))
  }, [lang])

  useEffect(() => {
    if (!business) return
    setForm((f) => ({
      ...f,
      name: business.name || f.name,
      business_type: business.business_type || f.business_type,
      city: business.city || f.city,
      legal_form: business.legal_form || f.legal_form,
      tax_regime: business.tax_regime || f.tax_regime,
      is_vat_payer: Boolean(business.is_vat_payer),
      has_employees: Boolean(business.has_employees),
      pension_participants: business.pension_participants !== false,
      llc_distributes_profit: Boolean(business.llc_distributes_profit),
    }))
  }, [business])

  useEffect(() => {
    api('/tax/obligations')
      .then((res) => setObligations(res.obligations || []))
      .catch(() => setObligations([]))
  }, [business?.tax_regime, business?.legal_form, business?.is_vat_payer, business?.has_employees])

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setMsg('')
    try {
      const tax_regime = form.legal_form === 'llc' ? 'llc_estonian' : form.tax_regime
      const res = await api('/settings', {
        method: 'PUT',
        body: JSON.stringify({
          language: form.language,
          full_name: form.full_name,
          business: {
            name: form.name,
            business_type: form.business_type,
            city: form.city,
            legal_form: form.legal_form,
            tax_regime,
            is_vat_payer: form.is_vat_payer,
            has_employees: form.has_employees,
            pension_participants: form.pension_participants,
            llc_distributes_profit: form.legal_form === 'llc' ? form.llc_distributes_profit : false,
          },
        }),
      })
      setObligations(res.obligations || [])
      await refresh()
      setMsg(t('settings.saved'))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const regimeOptions = form.legal_form === 'llc' ? ['llc_estonian'] : TAX_REGIMES_IE
  const obligationTitle = (o) => (lang === 'ka' ? o.title_ka || o.title_en : o.title_en || o.title_ka)
  const obligationDetail = (o) => (lang === 'ka' ? o.detail_ka || o.detail_en : o.detail_en || o.detail_ka)

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

        <h3 style={{ marginBottom: '0.25rem' }}>{t('settings.taxSection')}</h3>
        <p className="muted" style={{ marginTop: 0 }}>{t('settings.taxSectionHint')}</p>

        <div className="field">
          <label>{t('onboarding.legalForm')}</label>
          <select
            value={form.legal_form}
            onChange={(e) => {
              const legal_form = e.target.value
              setForm({
                ...form,
                legal_form,
                tax_regime: legal_form === 'llc' ? 'llc_estonian' : form.tax_regime === 'llc_estonian' ? 'small' : form.tax_regime,
              })
            }}
          >
            {LEGAL_FORMS.map((v) => (
              <option key={v} value={v}>{t(`onboarding.legalForms.${v}`)}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t('onboarding.taxRegime')}</label>
          <select
            value={form.tax_regime}
            onChange={(e) => setForm({ ...form, tax_regime: e.target.value })}
          >
            {regimeOptions.map((v) => (
              <option key={v} value={v}>{t(`onboarding.taxRegimes.${v}`)}</option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{t('onboarding.vatPayer')}</label>
          <select
            value={form.is_vat_payer ? 'true' : 'false'}
            onChange={(e) => setForm({ ...form, is_vat_payer: e.target.value === 'true' })}
          >
            <option value="false">{t('onboarding.vatNo')}</option>
            <option value="true">{t('onboarding.vatYes')}</option>
          </select>
        </div>
        <div className="field">
          <label>{t('onboarding.hasEmployees')}</label>
          <select
            value={form.has_employees ? 'true' : 'false'}
            onChange={(e) => setForm({ ...form, has_employees: e.target.value === 'true' })}
          >
            <option value="false">{t('onboarding.no')}</option>
            <option value="true">{t('onboarding.yes')}</option>
          </select>
        </div>
        {form.has_employees && (
          <div className="field">
            <label>{t('onboarding.pensionParticipants')}</label>
            <select
              value={form.pension_participants ? 'true' : 'false'}
              onChange={(e) => setForm({ ...form, pension_participants: e.target.value === 'true' })}
            >
              <option value="true">{t('onboarding.yes')}</option>
              <option value="false">{t('onboarding.no')}</option>
            </select>
          </div>
        )}
        {form.legal_form === 'llc' && (
          <div className="field">
            <label>{t('onboarding.llcDistributes')}</label>
            <select
              value={form.llc_distributes_profit ? 'true' : 'false'}
              onChange={(e) => setForm({ ...form, llc_distributes_profit: e.target.value === 'true' })}
            >
              <option value="false">{t('onboarding.no')}</option>
              <option value="true">{t('onboarding.yes')}</option>
            </select>
          </div>
        )}

        {obligations.length > 0 && (
          <div style={{ marginBottom: '1rem' }}>
            <strong>{t('dashboard.taxObligations')}</strong>
            <ul style={{ paddingLeft: '1.1rem' }}>
              {obligations.map((o) => (
                <li key={o.code} style={{ marginBottom: '0.35rem' }}>
                  <strong>{obligationTitle(o)}</strong>
                  <div className="muted" style={{ fontSize: '0.9rem' }}>{obligationDetail(o)}</div>
                </li>
              ))}
            </ul>
            <p className="muted" style={{ fontSize: '0.85rem' }}>{t('onboarding.taxDisclaimer')}</p>
          </div>
        )}

        <button className="btn" disabled={busy}>{busy ? t('common.saving') : t('common.save')}</button>
      </form>
    </>
  )
}
