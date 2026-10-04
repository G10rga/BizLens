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
import { api } from '../api'
import { useI18n } from '../i18n'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

export default function Dashboard() {
  const { t, money, lang } = useI18n()
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
      ...data.timeline.map((x) => x.date.slice(5)),
    ]

    if (view === 'sales') {
      const incomeKey =
        scenario === 'best' ? 'income_best' : scenario === 'worst' ? 'income_worst' : 'income_likely'
      return {
        labels,
        datasets: [
          {
            label: t('dashboard.histSales'),
            data: [...hist.map((h) => h.revenue), ...data.timeline.map(() => null)],
            borderColor: '#64748b',
            backgroundColor: 'transparent',
            tension: 0.2,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: t('dashboard.futureSalesLine'),
            data: [...hist.map(() => null), ...data.timeline.map((x) => x[incomeKey])],
            borderColor: scenario === 'worst' ? '#ef4444' : scenario === 'best' ? '#10b981' : '#1b4332',
            backgroundColor: 'rgba(16,185,129,0.10)',
            fill: false,
            tension: 0.15,
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: t('dashboard.rangeLow'),
            data: [...hist.map(() => null), ...data.timeline.map((x) => x.income_worst)],
            borderColor: 'rgba(239,68,68,0.35)',
            borderDash: [4, 4],
            pointRadius: 0,
            borderWidth: 1,
            fill: false,
            tension: 0.15,
          },
          {
            label: t('dashboard.rangeHigh'),
            data: [...hist.map(() => null), ...data.timeline.map((x) => x.income_best)],
            borderColor: 'rgba(16,185,129,0.45)',
            borderDash: [4, 4],
            pointRadius: 0,
            borderWidth: 1,
            fill: '-1',
            backgroundColor: 'rgba(16,185,129,0.08)',
            tension: 0.15,
          },
        ],
      }
    }

    const cashKey =
      scenario === 'best' ? 'cash_best' : scenario === 'worst' ? 'cash_worst' : 'cash_likely'
    const todayCash = data.summary.cash_today
    return {
      labels: [t('dashboard.todayLabel'), ...data.timeline.map((x) => x.date.slice(5))],
      datasets: [
        {
          label: t('dashboard.cashBalance'),
          data: [todayCash, ...data.timeline.map((x) => x[cashKey])],
          borderColor: scenario === 'worst' ? '#ef4444' : scenario === 'best' ? '#10b981' : '#1b4332',
          backgroundColor: 'rgba(27,67,50,0.1)',
          fill: true,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    }
  }, [data, scenario, view, t])

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('dashboard.title')}</h1>
          <p className="muted">
            {data
              ? t('dashboard.meta', {
                  name: data.business.name,
                  model: data.model,
                  days: data.history_days,
                  baseline: money(data.baseline_daily || 0),
                  scale: data.calibration_scale ?? 1,
                })
              : t('dashboard.loadingMeta')}
          </p>
          {data?.as_of && (
            <p className="muted">
              {t('dashboard.asOf', { asOf: data.as_of, starts: data.forecast_starts })}
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
              {t('dashboard.chartDays', { days: h })}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <p className="muted">{t('dashboard.computing')}</p>}

      {data && (
        <>
          {data.backtest?.enabled && (
            <div className="card warn-note" style={{ marginBottom: '1rem' }}>
              <strong>{t('dashboard.backtestTitle')}</strong>
              <p className="muted" style={{ margin: '0.35rem 0 0' }}>
                {t('dashboard.backtestBody', {
                  days: data.backtest.holdout_days,
                  start: data.backtest.holdout_start,
                  end: data.backtest.holdout_end,
                  actual: money(data.backtest.actual_sum),
                  predicted: money(data.backtest.predicted_sum),
                  error: data.backtest.error_pct,
                  starts: data.forecast_starts,
                })}
              </p>
            </div>
          )}

          <h3 className="section-title">
            {t('dashboard.futureSales')}
          </h3>
          <p className="muted" style={{ marginTop: 0 }}>
            {t('dashboard.rangeHint')}
          </p>
          <div className="grid grid-4" style={{ marginBottom: '1.25rem' }}>
            <div className="card">
              <div className="label">{t('dashboard.avgDaily')}</div>
              <div className="metric small">{money(data.summary.avg_daily_sales)}</div>
              <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>
                {money(data.summary.avg_daily_sales_low ?? data.summary.avg_daily_sales)}
                {' – '}
                {money(data.summary.avg_daily_sales_high ?? data.summary.avg_daily_sales)}
              </div>
            </div>
            <div className="card">
              <div className="label">{t('dashboard.sales30')}</div>
              <div className="metric small">{money(data.summary.sales_30)}</div>
              <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>
                {money(data.summary.sales_30_low ?? data.summary.sales_30)}
                {' – '}
                {money(data.summary.sales_30_high ?? data.summary.sales_30)}
              </div>
            </div>
            <div className="card">
              <div className="label">{t('dashboard.sales60')}</div>
              <div className="metric small">{money(data.summary.sales_60)}</div>
              <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>
                {money(data.summary.sales_60_low ?? data.summary.sales_60)}
                {' – '}
                {money(data.summary.sales_60_high ?? data.summary.sales_60)}
              </div>
            </div>
            <div className="card">
              <div className="label">{t('dashboard.sales90')}</div>
              <div className="metric small">{money(data.summary.sales_90)}</div>
              <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>
                {money(data.summary.sales_90_low ?? data.summary.sales_90)}
                {' – '}
                {money(data.summary.sales_90_high ?? data.summary.sales_90)}
              </div>
            </div>
          </div>

          <h3 className="section-title">
            {t('dashboard.cashTitle')}
          </h3>
          <p className="muted" style={{ marginTop: 0 }}>
            {t('dashboard.cashHint', { amount: money(data.summary.cash_today) })}
          </p>
          <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
            <div className="card">
              <div className="label">{t('dashboard.cashNow')}</div>
              <div className="metric">{money(data.summary.cash_today)}</div>
            </div>
            <div className="card">
              <div className="label">{t('dashboard.cash30')}</div>
              <div className="metric small">{money(data.summary.cash_30)}</div>
              {(data.summary.cash_30_low != null || data.summary.cash_30_high != null) && (
                <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>
                  {money(data.summary.cash_30_low)}
                  {' – '}
                  {money(data.summary.cash_30_high)}
                </div>
              )}
            </div>
            <div className="card">
              <div className="label">{t('dashboard.cash60')}</div>
              <div className="metric small">{money(data.summary.cash_60)}</div>
              {(data.summary.cash_60_low != null || data.summary.cash_60_high != null) && (
                <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.9rem' }}>
                  {money(data.summary.cash_60_low)}
                  {' – '}
                  {money(data.summary.cash_60_high)}
                </div>
              )}
            </div>
            <div className="card">
              <div className="label">{t('dashboard.daysUntilDanger')}</div>
              <div className="metric small">
                {data.summary.days_until_danger == null
                  ? '—'
                  : t('dashboard.days', { n: data.summary.days_until_danger })}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: '1rem' }}>
            <div className="row" style={{ marginBottom: '0.75rem' }}>
              <h2 style={{ margin: 0 }}>{t('dashboard.chart')}</h2>
              <div className="row" style={{ marginLeft: 'auto' }}>
                <button className={`btn ${view === 'sales' ? '' : 'ghost'}`} onClick={() => setView('sales')}>
                  {t('dashboard.sales')}
                </button>
                <button className={`btn ${view === 'cash' ? '' : 'ghost'}`} onClick={() => setView('cash')}>
                  {t('dashboard.cash')}
                </button>
                {['worst', 'likely', 'best'].map((s) => (
                  <button
                    key={s}
                    className={`btn ${scenario === s ? '' : 'ghost'}`}
                    onClick={() => setScenario(s)}
                  >
                    {t(`dashboard.${s}`)}
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
              <h3>{t('dashboard.holidays')}</h3>
              {data.holiday_markers.slice(0, 8).map((m) => (
                <div key={`${m.key}-${m.date}`} className="cart-line">
                  <div>
                    <strong>{lang === 'ka' ? (m.name_ka || m.name) : (m.name || m.name_ka)}</strong>
                    <div className="muted">{m.date}</div>
                  </div>
                  <span className={`badge ${m.direction === 'down' ? 'yellow' : 'green'}`}>
                    {m.direction === 'down' ? t('dashboard.dirDown') : t('dashboard.dirUp')}
                  </span>
                </div>
              ))}
              {!data.holiday_markers.length && <p className="muted">{t('dashboard.noMarkers')}</p>}
            </div>
            <div className="card">
              <h3>{t('dashboard.futureExpenses')}</h3>
              {data.expense_markers.slice(0, 8).map((m) => (
                <div key={m.date + m.amount} className="cart-line">
                  <div>
                    <strong>{m.date}</strong>
                    <div className="muted">{m.items.map((i) => i.name).join(', ')}</div>
                  </div>
                  <strong>-{money(m.amount)}</strong>
                </div>
              ))}
              {!data.expense_markers.length && <p className="muted">{t('dashboard.noExpenses')}</p>}
            </div>
          </div>
        </>
      )}
    </>
  )
}
