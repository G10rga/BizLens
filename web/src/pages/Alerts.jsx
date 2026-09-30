import { useEffect, useState } from 'react'
import { api, money } from '../api'

export default function Alerts() {
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

  return (
    <>
      <div className="topbar">
        <div>
          <h1>გაფრთხილებები</h1>
          <p className="muted">მოქმედებაზე ორიენტირებული შეტყობინებები პროგნოზიდან</p>
        </div>
        <button className="btn secondary" onClick={regenerate} disabled={busy}>
          {busy ? '...' : 'განახლება'}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="grid">
        {alerts.map((a) => (
          <div key={a.id} className={`card alert-item ${a.severity}`}>
            <div className="row">
              <span className={`badge ${a.severity === 'danger' ? 'red' : a.severity === 'opportunity' ? 'green' : 'yellow'}`}>
                {a.severity}
              </span>
              {a.alert_date && <span className="muted">{a.alert_date}</span>}
              {a.amount != null && <strong style={{ marginLeft: 'auto' }}>{money(a.amount)}</strong>}
            </div>
            <h3 style={{ marginTop: '0.6rem' }}>{a.title_ka || a.title}</h3>
            <p>{a.message_ka || a.message}</p>
            {!a.acknowledged && (
              <button className="btn ghost" onClick={() => ack(a.id)}>მიღებულია</button>
            )}
          </div>
        ))}
        {!alerts.length && <div className="card muted">გაფრთხილებები არ არის</div>}
      </div>
    </>
  )
}
