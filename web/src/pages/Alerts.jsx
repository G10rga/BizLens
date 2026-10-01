import { useEffect, useState } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

export default function Alerts() {
  const { lang, t, money } = useI18n()
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = async () => setAlerts(await api('/alerts'))

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const regenerate = async () => {
    setBusy(true)
    try {
      setAlerts(await api('/alerts/generate', { method: 'POST' }))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const ack = async (id) => {
    await api(`/alerts/${id}/acknowledge`, { method: 'POST' })
    await load()
  }

  const severityLabel = (severity) => t(`alerts.severity.${severity}`) || severity

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('alerts.title')}</h1>
          <p className="muted">{t('alerts.subtitle')}</p>
        </div>
        <button className="btn secondary" onClick={regenerate} disabled={busy}>
          {busy ? t('common.saving') : t('alerts.refresh')}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="grid">
        {alerts.map((a) => (
          <div key={a.id} className={`card alert-item ${a.severity}`}>
            <div className="row">
              <span className={`badge ${a.severity === 'danger' ? 'red' : a.severity === 'opportunity' ? 'green' : 'yellow'}`}>
                {severityLabel(a.severity)}
              </span>
              {a.alert_date && <span className="muted">{a.alert_date}</span>}
              {a.amount != null && <strong style={{ marginLeft: 'auto' }}>{money(a.amount)}</strong>}
            </div>
            <h3 style={{ marginTop: '0.6rem' }}>{lang === 'ka' ? (a.title_ka || a.title) : (a.title || a.title_ka)}</h3>
            <p>{lang === 'ka' ? (a.message_ka || a.message) : (a.message || a.message_ka)}</p>
            {!a.acknowledged && (
              <button className="btn ghost" onClick={() => ack(a.id)}>{t('alerts.ack')}</button>
            )}
          </div>
        ))}
        {!alerts.length && <div className="card muted">{t('alerts.empty')}</div>}
      </div>
    </>
  )
}
