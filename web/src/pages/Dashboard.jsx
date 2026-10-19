import { useEffect, useMemo, useState } from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import { api } from '../api'
import { useI18n } from '../i18n'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Filler,
  Tooltip,
  Legend,
)

/** Vertical divider where history ends / forecast begins. */
const forecastDividerPlugin = {
  id: 'forecastDivider',
  afterDraw(chart) {
    const idx = chart.options.plugins?.forecastDivider?.atIndex
    if (idx == null || idx < 0) return
    const { ctx, chartArea, scales } = chart
    const xScale = scales.x
    if (!xScale || !chartArea) return
    const x = xScale.getPixelForValue(idx)
    if (x < chartArea.left || x > chartArea.right) return
    ctx.save()
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.55)'
    ctx.setLineDash([6, 4])
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(x, chartArea.top)
    ctx.lineTo(x, chartArea.bottom)
    ctx.stroke()
    ctx.restore()
  },
}

/** Soft danger / caution bands behind the cash balance line. */
const cashZonesPlugin = {
  id: 'cashZones',
  beforeDatasetsDraw(chart) {
    const cfg = chart.options.plugins?.cashZones
    if (!cfg?.enabled) return
    const { ctx, chartArea, scales } = chart
    const yScale = scales.y
    if (!yScale || !chartArea) return
    const yellow = Number(cfg.yellow) || 500
    const green = Number(cfg.green) || 1500
    const yTop = chartArea.top
    const yBottom = chartArea.bottom
    const yGreen = Math.min(yBottom, Math.max(yTop, yScale.getPixelForValue(green)))
    const yYellow = Math.min(yBottom, Math.max(yTop, yScale.getPixelForValue(yellow)))

    ctx.save()
    // Safe zone (above green threshold)
    ctx.fillStyle = 'rgba(16, 185, 129, 0.06)'
    ctx.fillRect(chartArea.left, yTop, chartArea.right - chartArea.left, Math.max(0, yGreen - yTop))
    // Caution (yellow → green)
    ctx.fillStyle = 'rgba(245, 158, 11, 0.08)'
    ctx.fillRect(chartArea.left, yGreen, chartArea.right - chartArea.left, Math.max(0, yYellow - yGreen))
    // Danger (below yellow)
    ctx.fillStyle = 'rgba(239, 68, 68, 0.10)'
    ctx.fillRect(chartArea.left, yYellow, chartArea.right - chartArea.left, Math.max(0, yBottom - yYellow))
    ctx.restore()
  },
}

/** Holiday season ticks on the cash/sales timeline. */
const holidayMarksPlugin = {
  id: 'holidayMarks',
  afterDatasetsDraw(chart) {
    const marks = chart.options.plugins?.holidayMarks?.items
    if (!marks?.length) return
    const { ctx, chartArea, scales } = chart
    const xScale = scales.x
    if (!xScale || !chartArea) return
    ctx.save()
    for (const m of marks) {
      if (m.index == null || m.index < 0) continue
      const x = xScale.getPixelForValue(m.index)
      if (x < chartArea.left || x > chartArea.right) continue
      ctx.strokeStyle = m.down ? 'rgba(245, 158, 11, 0.7)' : 'rgba(16, 185, 129, 0.65)'
      ctx.setLineDash([2, 3])
      ctx.lineWidth = 1.25
      ctx.beginPath()
      ctx.moveTo(x, chartArea.top)
      ctx.lineTo(x, chartArea.bottom)
      ctx.stroke()
    }
    ctx.restore()
  },
}

ChartJS.register(forecastDividerPlugin, cashZonesPlugin, holidayMarksPlugin)

function expenseLabel(name, t) {
  const key = `onboarding.expenses.${String(name || '').toLowerCase()}`
  const translated = t(key)
  return translated === key ? name : translated
}

export default function Dashboard() {
  const { t, money, lang } = useI18n()
  const [data, setData] = useState(null)
  const [horizon, setHorizon] = useState(90)
  const [view, setView] = useState('cash')
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

  const holidayIndexByDate = useMemo(() => {
    if (!data) return {}
    const map = {}
    const labels = view === 'cash'
      ? [null, ...data.timeline.map((x) => x.date)]
      : [
          ...data.history.slice(-90).map((h) => h.date),
          ...data.timeline.map((x) => x.date),
        ]
    labels.forEach((d, i) => {
      if (d) map[d] = i
    })
    return map
  }, [data, view])

  const holidayMarks = useMemo(() => {
    if (!data?.holiday_markers) return []
    return data.holiday_markers
      .map((m) => ({
        index: holidayIndexByDate[m.date],
        down: m.direction === 'down',
        label: lang === 'ka' ? (m.name_ka || m.name) : (m.name || m.name_ka),
      }))
      .filter((m) => m.index != null)
  }, [data, holidayIndexByDate, lang])

  const chart = useMemo(() => {
    if (!data) return null
    const hist = data.history.slice(-90)
    const histLen = hist.length
    const accent = scenario === 'worst' ? '#ef4444' : scenario === 'best' ? '#10b981' : '#1b4332'

    if (view === 'sales') {
      const incomeKey =
        scenario === 'best' ? 'income_best' : scenario === 'worst' ? 'income_worst' : 'income_likely'
      const labels = [
        ...hist.map((h) => h.date.slice(5)),
        ...data.timeline.map((x) => x.date.slice(5)),
      ]
      const lastHist = hist.length ? hist[hist.length - 1].revenue : null
      return {
        labels,
        dividerIndex: histLen > 0 ? histLen - 0.5 : null,
        datasets: [
          {
            label: t('dashboard.histSales'),
            data: [
              ...hist.map((h) => h.revenue),
              ...data.timeline.map((_, i) => (i === 0 ? lastHist : null)),
            ],
            borderColor: '#0f172a',
            backgroundColor: 'transparent',
            tension: 0.15,
            pointRadius: 0,
            borderWidth: 2.5,
            spanGaps: false,
          },
          {
            label: t('dashboard.futureSalesLine'),
            data: [...hist.map(() => null), ...data.timeline.map((x) => x[incomeKey])],
            borderColor: accent,
            borderDash: [6, 4],
            backgroundColor: 'rgba(16,185,129,0.08)',
            fill: false,
            tension: 0.15,
            pointRadius: 0,
            borderWidth: 2,
            spanGaps: false,
          },
          {
            label: t('dashboard.rangeLow'),
            data: [...hist.map(() => null), ...data.timeline.map((x) => x.income_worst)],
            borderColor: 'rgba(239,68,68,0.35)',
            borderDash: [3, 3],
            pointRadius: 0,
            borderWidth: 1,
            fill: false,
            tension: 0.15,
          },
          {
            label: t('dashboard.rangeHigh'),
            data: [...hist.map(() => null), ...data.timeline.map((x) => x.income_best)],
            borderColor: 'rgba(16,185,129,0.45)',
            borderDash: [3, 3],
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
    const labels = [t('dashboard.todayLabel'), ...data.timeline.map((x) => x.date.slice(5))]
    const cashSeries = [todayCash, ...data.timeline.map((x) => x[cashKey])]
    const cashLow = [todayCash, ...data.timeline.map((x) => x.cash_worst)]
    const cashHigh = [todayCash, ...data.timeline.map((x) => x.cash_best)]

    const expenseByDate = Object.fromEntries(
      (data.expense_markers || []).map((m) => [m.date, m]),
    )
    const maxExp = Math.max(1, ...Object.values(expenseByDate).map((m) => Number(m.amount) || 0))
    const expensePoints = [
      null,
      ...data.timeline.map((x) => (expenseByDate[x.date] != null ? x[cashKey] : null)),
    ]
    const expenseMeta = [
      null,
      ...data.timeline.map((x) => expenseByDate[x.date] || null),
    ]
    const expenseRadii = expensePoints.map((v, i) => {
      if (v == null || !expenseMeta[i]) return 0
      const amt = Number(expenseMeta[i].amount) || 0
      return 4 + Math.round((amt / maxExp) * 10)
    })

    return {
      labels,
      dividerIndex: 0.5,
      expenseMeta,
      datasets: [
        {
          label: t('dashboard.rangeHigh'),
          data: cashHigh,
          borderColor: 'rgba(16,185,129,0.35)',
          backgroundColor: 'rgba(16,185,129,0.10)',
          borderWidth: 1,
          pointRadius: 0,
          fill: '+1',
          tension: 0.25,
          order: 3,
        },
        {
          label: t('dashboard.rangeLow'),
          data: cashLow,
          borderColor: 'rgba(239,68,68,0.35)',
          backgroundColor: 'transparent',
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
          tension: 0.25,
          order: 2,
        },
        {
          label: t('dashboard.cashBalance'),
          data: cashSeries,
          borderColor: accent,
          backgroundColor: 'rgba(27,67,50,0.14)',
          fill: true,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2.75,
          order: 1,
        },
        {
          label: t('dashboard.expenseDrops'),
          data: expensePoints,
          borderColor: '#b91c1c',
          backgroundColor: '#dc2626',
          showLine: false,
          pointRadius: expenseRadii,
          pointHoverRadius: expenseRadii.map((r) => (r ? r + 2 : 0)),
          pointStyle: 'circle',
          order: 0,
        },
      ],
    }
  }, [data, scenario, view, t])

  const outflowBars = useMemo(() => {
    if (!data?.expense_markers?.length) return null
    const top = [...data.expense_markers]
      .sort((a, b) => Number(b.amount) - Number(a.amount))
      .slice(0, 8)
    const maxAmt = Math.max(...top.map((m) => Number(m.amount) || 0), 1)
    return {
      labels: top.map((m) => {
        const names = (m.items || []).map((i) => expenseLabel(i.name, t)).join(', ')
        return `${m.date.slice(5)} · ${names || t('dashboard.futureExpenses')}`
      }),
      amounts: top.map((m) => Number(m.amount) || 0),
      maxAmt,
      raw: top,
    }
  }, [data, t])

  const chartOptions = useMemo(() => {
    const yellow = data?.thresholds?.yellow ?? 500
    const green = data?.thresholds?.green ?? 1500
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 12, usePointStyle: true, padding: 14 },
        },
        forecastDivider: { atIndex: chart?.dividerIndex },
        cashZones: { enabled: view === 'cash', yellow, green },
        holidayMarks: { items: holidayMarks },
        tooltip: {
          callbacks: {
            title(items) {
              const idx = items?.[0]?.dataIndex
              if (view === 'cash' && idx === 0) return t('dashboard.todayLabel')
              return items?.[0]?.label || ''
            },
            label(ctx) {
              const v = ctx.parsed?.y
              if (v == null || Number.isNaN(v)) return undefined
              if (ctx.dataset.label === t('dashboard.expenseDrops') && chart?.expenseMeta) {
                const meta = chart.expenseMeta[ctx.dataIndex]
                if (meta) {
                  const names = (meta.items || []).map((i) => expenseLabel(i.name, t)).join(', ')
                  return `${t('dashboard.expenseDrops')}: −${money(meta.amount)}${names ? ` (${names})` : ''}`
                }
              }
              return `${ctx.dataset.label}: ${money(v)}`
            },
            afterBody(items) {
              const idx = items?.[0]?.dataIndex
              const hit = holidayMarks.find((m) => m.index === idx)
              if (!hit) return []
              return [
                `${t('dashboard.holidays')}: ${hit.label} (${hit.down ? t('dashboard.dirDown') : t('dashboard.dirUp')})`,
              ]
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(148,163,184,0.18)' },
          ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 10 },
        },
        y: {
          grid: { color: 'rgba(148,163,184,0.22)' },
          ticks: { callback: (v) => `${v} ₾` },
        },
      },
    }
  }, [chart, data, holidayMarks, money, t, view])

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

          <h3 className="section-title">{t('dashboard.cashTitle')}</h3>
          <p className="muted" style={{ marginTop: 0 }}>
            {t('dashboard.cashHint', { amount: money(data.summary.cash_today) })}
          </p>
          <div className="grid grid-4" style={{ marginBottom: '1rem' }}>
            <div className="card">
              <div className="label">{t('dashboard.cashNow')}</div>
              <div className="metric">{money(data.summary.cash_today)}</div>
              {data.summary.available_cash != null && (
                <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.85rem' }}>
                  {t('dashboard.taxAvailable')}: {money(data.summary.available_cash)}
                </div>
              )}
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

          <div className="card cashflow-hero" style={{ marginBottom: '1rem' }}>
            <div className="row" style={{ marginBottom: '0.75rem' }}>
              <h2 style={{ margin: 0 }}>{t('dashboard.cashflowChart')}</h2>
              <div className="row" style={{ marginLeft: 'auto' }}>
                <button className={`btn ${view === 'cash' ? '' : 'ghost'}`} onClick={() => setView('cash')}>
                  {t('dashboard.cash')}
                </button>
                <button className={`btn ${view === 'sales' ? '' : 'ghost'}`} onClick={() => setView('sales')}>
                  {t('dashboard.sales')}
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
            <p className="muted" style={{ marginTop: 0, marginBottom: '0.75rem' }}>
              {view === 'sales' ? t('dashboard.chartSalesHint') : t('dashboard.chartCashHint')}
            </p>
            {view === 'cash' && (
              <div className="cash-zone-legend" aria-hidden="true">
                <span><i className="zone safe" />{t('dashboard.zoneSafe')}</span>
                <span><i className="zone caution" />{t('dashboard.zoneCaution')}</span>
                <span><i className="zone danger" />{t('dashboard.zoneDanger')}</span>
                <span><i className="zone expense" />{t('dashboard.expenseDrops')}</span>
                <span><i className="zone season" />{t('dashboard.holidays')}</span>
              </div>
            )}
            <div className="chart-wrap chart-wrap-lg">
              {chart && <Line data={chart} options={chartOptions} />}
            </div>
            {!!holidayMarks.length && (
              <div className="season-strip">
                {data.holiday_markers.slice(0, 6).map((m) => (
                  <span
                    key={`${m.key}-${m.date}`}
                    className={`season-chip ${m.direction === 'down' ? 'down' : 'up'}`}
                  >
                    <strong>{lang === 'ka' ? (m.name_ka || m.name) : (m.name || m.name_ka)}</strong>
                    <em>{m.date.slice(5)}</em>
                  </span>
                ))}
              </div>
            )}
          </div>

          {outflowBars && (
            <div className="card" style={{ marginBottom: '1.25rem' }}>
              <h3 style={{ marginTop: 0 }}>{t('dashboard.outflowPressure')}</h3>
              <p className="muted" style={{ marginTop: 0 }}>{t('dashboard.outflowPressureHint')}</p>
              <div className="chart-wrap chart-wrap-bars">
                <Bar
                  data={{
                    labels: outflowBars.labels,
                    datasets: [
                      {
                        label: t('dashboard.futureExpenses'),
                        data: outflowBars.amounts,
                        backgroundColor: outflowBars.amounts.map(
                          (a) => `rgba(185, 28, 28, ${0.35 + 0.55 * (a / outflowBars.maxAmt)})`,
                        ),
                        borderRadius: 6,
                        borderSkipped: false,
                      },
                    ],
                  }}
                  options={{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: { display: false },
                      tooltip: {
                        callbacks: {
                          label(ctx) {
                            return `−${money(ctx.parsed.x)}`
                          },
                        },
                      },
                    },
                    scales: {
                      x: {
                        ticks: { callback: (v) => `${v} ₾` },
                        grid: { color: 'rgba(148,163,184,0.2)' },
                      },
                      y: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } },
                      },
                    },
                  }}
                />
              </div>
            </div>
          )}

          {data.tax_summary && (
            <>
              <h3 className="section-title">{t('dashboard.taxTitle')}</h3>
              <p className="muted" style={{ marginTop: 0 }}>{t('dashboard.taxHint')}</p>
              <div className="grid grid-4" style={{ marginBottom: '1.25rem' }}>
                <div className="card">
                  <div className="label">{t('dashboard.taxIncome')}</div>
                  <div className="metric small">{money(data.tax_summary.income_total)}</div>
                </div>
                <div className="card">
                  <div className="label">{t('dashboard.taxExpenses')}</div>
                  <div className="metric small">{money(data.tax_summary.expense_total)}</div>
                </div>
                <div className="card">
                  <div className="label">{t('dashboard.taxReserve')}</div>
                  <div className="metric small">{money(data.tax_summary.total_tax_reserve)}</div>
                  {data.tax_summary.vat_reserve > 0 && (
                    <div className="muted" style={{ marginTop: '0.35rem', fontSize: '0.85rem' }}>
                      {t('dashboard.taxVatReserve')}: {money(data.tax_summary.vat_reserve)}
                    </div>
                  )}
                </div>
                <div className="card">
                  <div className="label">{t('dashboard.taxAvailable')}</div>
                  <div className="metric small">{money(data.tax_summary.available_cash)}</div>
                </div>
              </div>
            </>
          )}

          <h3 className="section-title">{t('dashboard.futureSales')}</h3>
          <p className="muted" style={{ marginTop: 0 }}>{t('dashboard.rangeHint')}</p>
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
        </>
      )}
    </>
  )
}
