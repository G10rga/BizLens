import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useI18n } from '../i18n'

export default function TodaySales() {
  const { t, money, lang } = useI18n()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/sales/today')
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  const methodLabel = (method) => (method === 'card' ? t('common.card') : t('common.cash'))

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('today.title')}</h1>
          <p className="muted">{data?.date || '—'}</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {data && (
        <>
          <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
            <div className="card">
              <div className="label">{t('today.dayTotal')}</div>
              <div className="metric">{money(data.total)}</div>
            </div>
            <div className="card">
              <div className="label">{t('today.posTx')}</div>
              <div className="metric small">{money(data.pos_total)}</div>
              <div className="muted">{t('today.receipts', { count: data.count })}</div>
            </div>
            <div className="card">
              <div className="label">{t('today.csvImport')}</div>
              <div className="metric small">{money(data.imported_daily_total)}</div>
              <div className="muted">{data.daily_source || '—'}</div>
            </div>
            <div className="card">
              <div className="label">{t('today.cashCard')}</div>
              <div className="metric small">{money(data.cash_total)} / {money(data.card_total)}</div>
            </div>
          </div>

          {!data.sales.length && data.imported_daily_total > 0 && (
            <div className="success" style={{ marginBottom: '1rem' }}>
              {t('today.importedNote', { amount: money(data.imported_daily_total) })}{' '}
              <Link to="/pos">POS</Link> · <Link to="/dashboard">{t('nav.dashboard')}</Link>
            </div>
          )}

          {!data.sales.length && !data.imported_daily_total && (
            <div className="error" style={{ marginBottom: '1rem' }}>
              {t('today.emptyNote', { date: data.date })}
            </div>
          )}

          <div className="card">
            <h2 style={{ marginTop: 0 }}>{t('today.posReceipts')}</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{t('today.time')}</th>
                  <th>{t('today.payment')}</th>
                  <th>{t('today.items')}</th>
                  <th>{t('today.amount')}</th>
                </tr>
              </thead>
              <tbody>
                {data.sales.map((s) => (
                  <tr key={s.id}>
                    <td>{s.id}</td>
                    <td>{new Date(s.sold_at).toLocaleTimeString(lang === 'ka' ? 'ka-GE' : 'en-US')}</td>
                    <td>{methodLabel(s.payment_method)}</td>
                    <td>{s.items.map((i) => `${i.product_name}×${i.quantity}`).join(', ')}</td>
                    <td>{money(s.total)}</td>
                  </tr>
                ))}
                {!data.sales.length && (
                  <tr>
                    <td colSpan="5" className="muted">
                      {t('today.noPos')}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  )
}
