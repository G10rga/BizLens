import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { useI18n } from '../i18n'

const emptyItems = () => [{ product_name: '', quantity: 1, unit_price: 0, line_total: 0 }]

function round2(n) {
  return Math.round(Number(n) * 100) / 100
}

export default function Lens() {
  const { refresh } = useAuth()
  const { t, money } = useI18n()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [step, setStep] = useState('capture')
  const [capture, setCapture] = useState(null)
  const [parsed, setParsed] = useState(null)
  const [form, setForm] = useState({
    receipt_date: '',
    receipt_time: '',
    total: '',
    payment_method: 'cash',
    tin: '',
  })
  const [items, setItems] = useState(emptyItems())
  const [completeness, setCompleteness] = useState(null)
  const [history, setHistory] = useState([])
  const [expected, setExpected] = useState(10)
  const [ocrInfo, setOcrInfo] = useState(null)

  const loadMeta = async () => {
    const [comp, hist, ocr] = await Promise.all([
      api('/lens/completeness?days=14'),
      api('/lens/history'),
      api('/lens/ocr-status'),
    ])
    setCompleteness(comp)
    setExpected(comp.expected_per_day || 10)
    setHistory(hist.captures || [])
    setOcrInfo(ocr)
  }

  useEffect(() => {
    loadMeta().catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!file) {
      setPreviewUrl('')
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const applyParsed = (cap, p) => {
    setCapture(cap)
    setParsed(p)
    setForm({
      receipt_date: p?.receipt_date || cap?.receipt_date || '',
      receipt_time: p?.receipt_time || cap?.receipt_time || '',
      total: p?.total ?? cap?.total ?? '',
      payment_method:
        (p?.payment_method || cap?.payment_method) === 'card' ? 'card' : 'cash',
      tin: p?.tin || cap?.tin || '',
    })
    const parsedItems = p?.items?.length ? p.items : cap?.items || []
    setItems(
      parsedItems.length
        ? parsedItems.map((i) => ({
            product_name: i.product_name || '',
            quantity: i.quantity || 1,
            unit_price: i.unit_price || 0,
            line_total: i.line_total || 0,
          }))
        : emptyItems()
    )
    setStep('review')
  }

  const scanFile = async () => {
    if (!file) return
    setBusy(true)
    setError('')
    setSuccess('')
    const postScan = async (skipOcr = false) => {
      const fd = new FormData()
      fd.append('file', file)
      if (skipOcr) fd.append('skip_ocr', 'true')
      return api('/lens/scan', { method: 'POST', body: fd })
    }
    try {
      const res = await postScan(false)
      applyParsed(res.capture, res.parsed)
      if (res.parsed?.warnings?.length) {
        setSuccess(res.parsed.warnings.join(' · '))
      } else if (res.parsed?.ocr_engine === 'manual') {
        setSuccess('Could not read text — enter the total manually, then confirm')
      }
    } catch (e) {
      // 502 / worker crash — retry without OCR so user can still save the sale
      try {
        const res = await postScan(true)
        applyParsed(res.capture, res.parsed)
        setSuccess('OCR crashed — enter the total manually, then confirm')
        setError('')
      } catch (e2) {
        setError(e2.message || e.message || 'Scan failed')
      }
    } finally {
      setBusy(false)
    }
  }

  const scanDemo = async () => {
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const res = await api('/lens/scan-demo', { method: 'POST', body: '{}' })
      applyParsed(res.capture, res.parsed)
      setSuccess(t('lens.demoParsed'))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const confirmSale = async (addItems) => {
    if (!capture) return
    setBusy(true)
    setError('')
    try {
      const body = {
        capture_id: capture.id,
        ...form,
        total: Number(form.total),
        add_items: addItems,
        items: addItems
          ? items
              .filter((i) => i.product_name.trim())
              .map((i) => ({
                ...i,
                quantity: Number(i.quantity) || 1,
                unit_price: Number(i.unit_price) || 0,
                line_total:
                  Number(i.line_total) ||
                  Number(i.unit_price || 0) * Number(i.quantity || 1),
              }))
          : [],
      }
      const res = await api('/lens/confirm', {
        method: 'POST',
        body: JSON.stringify(body),
      })
      setSuccess(
        t('lens.savedSale', {
          total: money(res.sale.total),
          method: res.sale.payment_method === 'card' ? t('common.card') : t('common.cash'),
          id: res.sale.id,
        })
      )
      setCompleteness(res.completeness)
      setStep('done')
      setFile(null)
      setCapture(null)
      await refresh()
      await loadMeta()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const saveExpected = async () => {
    setBusy(true)
    try {
      const res = await api('/lens/expected-receipts', {
        method: 'POST',
        body: JSON.stringify({ expected_per_day: Number(expected) || 10 }),
      })
      setCompleteness(res.completeness)
      setSuccess(t('lens.dailyTarget', { n: res.lens_expected_receipts_per_day }))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const today = completeness?.today
  const confidencePct = Math.round((completeness?.average_confidence || 0) * 100)
  const capturePct = Math.round((completeness?.average_capture_rate || 0) * 100)

  const confidenceLabel = useMemo(() => {
    if (capturePct >= 80) return { text: t('lens.confHigh'), cls: 'green' }
    if (capturePct >= 50) return { text: t('lens.confMed'), cls: 'yellow' }
    return { text: t('lens.confLow'), cls: 'red' }
  }, [capturePct, t])

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('lens.title')}</h1>
          <p className="muted">{t('lens.subtitle')}</p>
          <h1>Lens Mode</h1>
          <p className="muted">
            Photograph a fiscal receipt — free OCR extracts the total and saves it to your sales database
          </p>
        </div>
        <button className="btn secondary" disabled={busy} onClick={scanDemo}>
          {t('lens.demo')}
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {ocrInfo && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <strong>Local OCR (no API keys)</strong>
          <p className="muted" style={{ margin: '0.35rem 0 0' }}>
            RapidOCR: {ocrInfo.rapidocr ? 'ready' : 'missing — pip install rapidocr-onnxruntime'} ·
            Tesseract: {ocrInfo.tesseract ? 'ready' : 'optional'} ·
            Cloud: {ocrInfo.ocr_space || ocrInfo.openai_vision ? 'optional key set' : 'off'}
            . Runs on your machine — review totals before confirm.
          </p>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div>
            <div className="label">{t('lens.completeness')}</div>
            <div className="metric small">{capturePct}%</div>
            <span className={`badge ${confidenceLabel.cls}`}>{confidenceLabel.text}</span>
          </div>
          <div>
            <div className="label">{t('lens.forecastConf')}</div>
            <div className="metric small">{confidencePct}%</div>
            <p className="muted" style={{ margin: 0, fontSize: '0.85rem' }}>
              {t('lens.rangeWiden', { n: completeness?.range_widen_factor ?? 1 })}
            </p>
          </div>
          <div style={{ minWidth: 200 }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{t('lens.expected')}</label>
              <div className="row">
                <input
                  type="number"
                  min={1}
                  max={200}
                  value={expected}
                  onChange={(e) => setExpected(e.target.value)}
                  style={{ width: 90 }}
                />
                <button className="btn ghost" disabled={busy} onClick={saveExpected}>
                  {t('common.save')}
                </button>
              </div>
            </div>
          </div>
        </div>
        {today && (
          <p className="muted" style={{ marginBottom: 0, marginTop: '0.75rem' }}>
            {t('lens.todayLine', { captured: today.captured, expected: today.expected })}
            {today.captured < today.expected ? t('lens.todayMissing') : t('lens.todayGood')}
          </p>
        )}
        <div className="completeness-bars">
          {(completeness?.daily || []).slice(-14).map((d) => (
            <div
              key={d.date}
              title={`${d.date}: ${d.captured}/${d.expected}`}
              className="completeness-bar"
              style={{ opacity: 0.35 + 0.65 * d.capture_rate }}
            >
              <div style={{ height: `${Math.max(8, d.capture_rate * 100)}%` }} />
            </div>
          ))}
        </div>
      </div>

      {(step === 'capture' || step === 'done') && (
        <div className="grid grid-2">
          <div className="card">
            <h2>{t('lens.step1')}</h2>
            <div className="dropzone lens-drop">
              <p><strong>{t('lens.camera')}</strong></p>
              <p className="muted">{t('lens.cameraHint')}</p>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => {
                  setFile(e.target.files?.[0] || null)
                  setStep('capture')
                  setSuccess('')
                }}
              />
            </div>
            {previewUrl && (
              <img src={previewUrl} alt="" className="lens-preview" />
            )}
            <div className="row" style={{ marginTop: '1rem' }}>
              <button className="btn" disabled={!file || busy} onClick={scanFile}>
                {busy ? t('lens.processing') : t('lens.parse')}
              </button>
            </div>
          </div>
          <div className="card">
            <h2>{t('lens.recent')}</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>{t('common.date')}</th>
                  <th>{t('common.total')}</th>
                  <th>{t('common.status')}</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 12).map((h) => (
                  <tr key={h.id}>
                    <td>{h.receipt_date || '—'}</td>
                    <td>{h.total != null ? money(h.total) : '—'}</td>
                    <td>{h.status}</td>
                  </tr>
                ))}
                {!history.length && (
                  <tr>
                    <td colSpan={3} className="muted">{t('lens.noReceipts')}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {step === 'review' && (
        <div className="grid grid-2">
          <div className="card">
            <h2>{t('lens.step2')}</h2>
            <p className="muted">
              {t('lens.engine', {
                engine: capture?.ocr_engine || '—',
                pct: Math.round((capture?.parse_confidence || 0) * 100),
              })}
            </p>
            {previewUrl && <img src={previewUrl} alt="" className="lens-preview" />}
            {parsed?.raw_text && <pre className="ocr-text">{parsed.raw_text}</pre>}
          </div>
          <div className="card">
            <h2>{t('lens.fields')}</h2>
            <div className="field">
              <label>{t('lens.date')}</label>
              <input
                type="date"
                value={form.receipt_date}
                onChange={(e) => setForm({ ...form, receipt_date: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{t('lens.time')}</label>
              <input
                type="time"
                value={form.receipt_time || ''}
                onChange={(e) => setForm({ ...form, receipt_time: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{t('lens.totalGel')}</label>
              <input
                type="number"
                step="0.01"
                value={form.total}
                onChange={(e) => setForm({ ...form, total: e.target.value })}
              />
            </div>
            <div className="field">
              <label>{t('lens.payment')}</label>
              <select
                value={form.payment_method}
                onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
              >
                <option value="cash">{t('common.cash')}</option>
                <option value="card">{t('common.card')}</option>
              </select>
            </div>
            <div className="field">
              <label>{t('lens.tin')}</label>
              <input
                value={form.tin}
                onChange={(e) => setForm({ ...form, tin: e.target.value })}
              />
            </div>
            <p style={{ fontWeight: 600, color: 'var(--heading)' }}>
              {t('lens.recordItems')}
            </p>
            <div className="row">
              <button className="btn" disabled={busy} onClick={() => setStep('items')}>
                {t('lens.addItems')}
              </button>
              <button
                className="btn secondary"
                disabled={busy || !form.total}
                onClick={() => confirmSale(false)}
              >
                {t('lens.skipTotal')}
              </button>
            </div>
            <button
              className="btn ghost"
              style={{ marginTop: '0.75rem' }}
              onClick={() => {
                setStep('capture')
                setCapture(null)
              }}
            >
              {t('common.back')}
            </button>
          </div>
        </div>
      )}

      {step === 'items' && (
        <div className="card">
          <h2>{t('lens.step3')}</h2>
          <p className="muted">{t('lens.step3Hint')}</p>
          {items.map((item, idx) => (
            <div className="row" key={idx} style={{ marginBottom: '0.5rem' }}>
              <input
                placeholder={t('lens.product')}
                value={item.product_name}
                onChange={(e) => {
                  const next = [...items]
                  next[idx] = { ...next[idx], product_name: e.target.value }
                  setItems(next)
                }}
                style={{ flex: 2 }}
              />
              <input
                type="number"
                min={1}
                value={item.quantity}
                onChange={(e) => {
                  const next = [...items]
                  const quantity = Number(e.target.value) || 1
                  next[idx] = {
                    ...next[idx],
                    quantity,
                    line_total: round2(quantity * Number(next[idx].unit_price || 0)),
                  }
                  setItems(next)
                }}
                style={{ width: 70 }}
              />
              <input
                type="number"
                step="0.01"
                placeholder={t('lens.price')}
                value={item.unit_price}
                onChange={(e) => {
                  const next = [...items]
                  const unit_price = Number(e.target.value) || 0
                  next[idx] = {
                    ...next[idx],
                    unit_price,
                    line_total: round2(unit_price * Number(next[idx].quantity || 1)),
                  }
                  setItems(next)
                }}
                style={{ width: 100 }}
              />
              <span style={{ minWidth: 80 }}>{money(item.line_total || 0)}</span>
            </div>
          ))}
          <div className="row" style={{ marginTop: '0.75rem' }}>
            <button className="btn ghost" onClick={() => setItems([...items, ...emptyItems()])}>
              {t('lens.addLine')}
            </button>
            <button className="btn" disabled={busy} onClick={() => confirmSale(true)}>
              {t('lens.saveItems')}
            </button>
            <button className="btn secondary" disabled={busy} onClick={() => confirmSale(false)}>
              {t('lens.totalOnly')}
            </button>
            <button className="btn ghost" onClick={() => setStep('review')}>
              {t('common.back')}
            </button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="card">
          <h2>{t('lens.savedTitle')}</h2>
          <p>{t('lens.savedBody')}</p>
          <button
            className="btn"
            onClick={() => {
              setStep('capture')
              setSuccess('')
            }}
          >
            {t('lens.newReceipt')}
          </button>
        </div>
      )}
    </>
  )
}
