import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, money } from '../api'

export default function TodaySales() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/sales/today')
      .then(setData)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <>
      <div className="topbar">
        <div>
          <h1>დღევანდელი გაყიდვები</h1>
          <p className="muted">{data?.date || '—'}</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {data && (
        <>
          <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
            <div className="card">
              <div className="label">დღის ჯამი</div>
              <div className="metric">{money(data.total)}</div>
            </div>
            <div className="card">
              <div className="label">POS ტრანზაქციები</div>
              <div className="metric small">{money(data.pos_total)}</div>
              <div className="muted">{data.count} ჩეკი</div>
            </div>
            <div className="card">
              <div className="label">Excel/CSV იმპორტი</div>
              <div className="metric small">{money(data.imported_daily_total)}</div>
              <div className="muted">{data.daily_source || '—'}</div>
            </div>
            <div className="card">
              <div className="label">ნაღდი / ბარათი (POS)</div>
              <div className="metric small">{money(data.cash_total)} / {money(data.card_total)}</div>
            </div>
          </div>

          {!data.sales.length && data.imported_daily_total > 0 && (
            <div className="success" style={{ marginBottom: '1rem' }}>
              დღის ჯამი მოდის Excel/CSV იმპორტიდან ({money(data.imported_daily_total)}).
              ცალკეული POS ჩეკები ჯერ არ არის — ჩაწერეთ გაყიდვა <Link to="/pos">POS</Link>-დან,
              ან ნახეთ პროგნოზი <Link to="/dashboard">დაფაზე</Link>.
            </div>
          )}

          {!data.sales.length && !data.imported_daily_total && (
            <div className="error" style={{ marginBottom: '1rem' }}>
              დღეს მონაცემი არ არის. Excel იმპორტი ჩანს <Link to="/dashboard">დაფაზე</Link> (ისტორია),
              ხოლო ამ გვერდზე POS ჩეკები ან დღევანდელი იმპორტირებული ჯამი ჩანს.
              შეამოწმეთ რომ ფაილში არის დღევანდელი თარიღი ({data.date}).
            </div>
          )}

          <div className="card">
            <h2 style={{ marginTop: 0 }}>POS ჩეკები</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>დრო</th>
                  <th>გადახდა</th>
                  <th>პროდუქტები</th>
                  <th>თანხა</th>
                </tr>
              </thead>
              <tbody>
                {data.sales.map((s) => (
                  <tr key={s.id}>
                    <td>{s.id}</td>
                    <td>{new Date(s.sold_at).toLocaleTimeString()}</td>
                    <td>{s.payment_method}</td>
                    <td>{s.items.map((i) => `${i.product_name}×${i.quantity}`).join(', ')}</td>
                    <td>{money(s.total)}</td>
                  </tr>
                ))}
                {!data.sales.length && (
                  <tr>
                    <td colSpan="5" className="muted">
                      POS ჩეკები არ არის (Excel იმპორტი აქ ცალკე ჩანაწერებად არ იშლება)
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
