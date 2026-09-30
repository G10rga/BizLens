import { useEffect, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'
import { api, money } from '../api'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [horizon, setHorizon] = useState(90)
  const [view, setView] = useState('sales')
  const [scenario, setScenario] = useState('likely')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api(`/forecast/dashboard?horizon=${horizon}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [horizon])

  const chart = useMemo(() => {
    if (!data) return null
    const hist = data.history.slice(-45)
    const labels = [
      ...hist.map((h) => h.date.slice(5)),
      ...data.timeline.map((t) => t.date.slice(5)),
    ]

    if (view === 'sales') {
      const incomeKey =
        scenario === 'best' ? 'income_best' : scenario === 'worst' ? 'income_worst' : 'income_likely'
      return {
        labels,
        datasets: [
          {
            label: 'ისტორიული გაყიდვები (დღე)',
            data: [...hist.map((h) => h.revenue), ...data.timeline.map(() => null)],
            borderColor: '#64748b',
            backgroundColor: 'transparent',
            tension: 0.25,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: 'მომავალი გაყიდვები (დღე)',
            data: [...hist.map(() => null), ...data.timeline.map((t) => t[incomeKey])],
            borderColor: scenario === 'worst' ? '#ef4444' : scenario === 'best' ? '#10b981' : '#1b4332',
            backgroundColor: 'rgba(16,185,129,0.12)',
            fill: true,
            tension: 0.25,
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
      }
    }

    const cashKey =
      scenario === 'best' ? 'cash_best' : scenario === 'worst' ? 'cash_worst' : 'cash_likely'
    const todayCash = data.summary.cash_today
    return {
      labels: ['დღეს', ...data.timeline.map((t) => t.date.slice(5))],
      datasets: [
        {
          label: 'ნაღდი ფულის ნაშთი',
          data: [todayCash, ...data.timeline.map((t) => t[cashKey])],
          borderColor: scenario === 'worst' ? '#ef4444' : scenario === 'best' ? '#10b981' : '#1b4332',
          backgroundColor: 'rgba(27,67,50,0.1)',
          fill: true,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    }
  }, [data, scenario, view])

  return (
    <>
      <div className="topbar">
        <div>
          <h1>ფულადი ნაკადების პროგნოზი</h1>
          <p className="muted">
            {data
              ? `${data.business.name} · ${data.model} · ისტორია: ${data.history_days} დღე · ბაზა: ${money(data.baseline_daily || 0)} · კალიბრაცია ×${data.calibration_scale ?? 1}`
              : 'იტვირთება...'}
          </p>
          {data?.as_of && (
            <p className="muted">
              მონაცემები ბოლომდე: {data.as_of} · პროგნოზი იწყება: {data.forecast_starts}
            </p>
          )}
        </div>
        <div className="row">
          {[30, 60, 90].map((h) => (
            <button
              key={h}
              className={`btn ${horizon === h ? '' : 'ghost'}`}
              onClick={() => setHorizon(h)}
            >
              გრაფიკი {h}დ
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <p className="muted">პროგნოზი ითვლება...</p>}

      {data && (
        <>
          {data.backtest?.enabled && (
            <div className="card" style={{ marginBottom: '1rem', background: '#fffbeb', borderColor: '#fde68a' }}>
              <strong>შიდა backtest ≠ მომავალი პროგნოზი</strong>
              <p className="muted" style={{ margin: '0.35rem 0 0' }}>
                Backtest ამოწმებს უკვე ატვირთულ ისტორიაში ბოლო {data.backtest.holdout_days} დღეს
                ({data.backtest.holdout_start} → {data.backtest.holdout_end}):
                ფაქტი {money(data.backtest.actual_sum)}, მაშინდელი პროგნოზი {money(data.backtest.predicted_sum)},
                ცდომილება {data.backtest.error_pct}%.
                ქვემოთ ბარათები არის <strong>მომავალი</strong> გაყიდვები — იწყება {data.forecast_starts}-დან
                (ისტორიის ბოლო დღის შემდეგ), არა backtest-ის რიცხვი.
              </p>
            </div>
          )}

          <h3 style={{ color: 'var(--pine)', margin: '0 0 0.5rem' }}>
            მომავალი გაყიდვების პროგნოზი (ჯამი)
          </h3>
          <div className="grid grid-4" style={{ marginBottom: '1.25rem' }}>
            <div className="card">
              <div className="label">საშ. დღიური</div>
              <div className="metric small">{money(data.summary.avg_daily_sales)}</div>
            </div>
            <div className="card">
              <div className="label">გაყიდვები 30 დღე</div>
              <div className="metric small">{money(data.summary.sales_30)}</div>
            </div>
            <div className="card">
              <div className="label">გაყიდვები 60 დღე</div>
              <div className="metric small">{money(data.summary.sales_60)}</div>
            </div>
            <div className="card">
              <div className="label">გაყიდვები 90 დღე</div>
              <div className="metric small">{money(data.summary.sales_90)}</div>
            </div>
          </div>

          <h3 style={{ color: 'var(--pine)', margin: '0 0 0.5rem' }}>
            ნაღდი ნაშთი (გაყიდვები − ხარჯები)
          </h3>
          <p className="muted" style={{ marginTop: 0 }}>
            იწყება თქვენი მიმდინარე ნაღდიდან ({money(data.summary.cash_today)}).
          </p>
          <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
            <div className="card">
              <div className="label">ნაღდი ახლა</div>
              <div className="metric">{money(data.summary.cash_today)}</div>
            </div>
            <div className="card">
              <div className="label">ნაშთი +30</div>
              <div className="metric small">{money(data.summary.cash_30)}</div>
            </div>
            <div className="card">
              <div className="label">ნაშთი +60</div>
              <div className="metric small">{money(data.summary.cash_60)}</div>
            </div>
            <div className="card">
              <div className="label">საფრთხემდე</div>
              <div className="metric small">
                {data.summary.days_until_danger == null
                  ? '—'
                  : `${data.summary.days_until_danger} დღე`}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="row" style={{ marginBottom: '0.75rem' }}>
              <h2 style={{ margin: 0 }}>გრაფიკი</h2>
              <div className="row" style={{ marginLeft: 'auto' }}>
                <button className={`btn ${view === 'sales' ? '' : 'ghost'}`} onClick={() => setView('sales')}>
                  გაყიდვები
                </button>
                <button className={`btn ${view === 'cash' ? '' : 'ghost'}`} onClick={() => setView('cash')}>
                  ნაღდი
                </button>
                {['worst', 'likely', 'best'].map((s) => (
                  <button
                    key={s}
                    className={`btn ${scenario === s ? '' : 'ghost'}`}
                    onClick={() => setScenario(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="chart-wrap">
              {chart && (
                <Line
                  data={chart}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                    scales: {
                      y: { ticks: { callback: (v) => `${v} ₾` } },
                    },
                  }}
                />
              )}
            </div>
          </div>

          <div className="grid grid-2">
            <div className="card">
              <h3>დღესასწაულები / სეზონი</h3>
              {data.holiday_markers.slice(0, 8).map((m) => (
                <div key={`${m.key}-${m.date}`} className="cart-line">
                  <div>
                    <strong>{m.name_ka || m.name}</strong>
                    <div className="muted">{m.date}</div>
                  </div>
                  <span className={`badge ${m.direction === 'down' ? 'yellow' : 'green'}`}>
                    {m.direction}
                  </span>
                </div>
              ))}
              {!data.holiday_markers.length && <p className="muted">მარკერები არ არის</p>}
            </div>
            <div className="card">
              <h3>მომავალი ხარჯები</h3>
              {data.expense_markers.slice(0, 8).map((m) => (
                <div key={m.date + m.amount} className="cart-line">
                  <div>
                    <strong>{m.date}</strong>
                    <div className="muted">{m.items.map((i) => i.name).join(', ')}</div>
                  </div>
                  <strong>-{money(m.amount)}</strong>
                </div>
              ))}
              {!data.expense_markers.length && <p className="muted">დაგეგმილი ხარჯი არ არის</p>}
            </div>
          </div>
        </>
      )}
    </>
  )
}
