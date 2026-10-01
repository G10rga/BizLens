import { useEffect, useMemo, useState } from 'react'
import { api, money } from '../api'
import { useAuth } from '../auth'

const emptyItems = () => [{ product_name: '', quantity: 1, unit_price: 0, line_total: 0 }]

function round2(n) {
  return Math.round(Number(n) * 100) / 100
}

export default function Lens() {
  const { refresh } = useAuth()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [step, setStep] = useState('capture') // capture | review | items | done
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
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api('/lens/scan', { method: 'POST', body: fd })
      applyParsed(res.capture, res.parsed)
      if (res.parsed?.warnings?.length) {
        setSuccess(res.parsed.warnings.join(' · '))
      }
    } catch (e) {
      setError(e.message)
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
      setSuccess('Demo receipt parsed — review fields and confirm')
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
      setSuccess(`Saved ${money(res.sale.total)} · ${res.sale.payment_method} · #${res.sale.id}`)
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
      setSuccess(`Daily target: ${res.lens_expected_receipts_per_day} receipts`)
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
    if (capturePct >= 80) return { text: 'High confidence', cls: 'green' }
    if (capturePct >= 50) return { text: 'Medium confidence', cls: 'yellow' }
    return { text: 'Low confidence — capture more receipts', cls: 'red' }
  }, [capturePct])

  return (
    <>
      <div className="topbar">
        <div>
          <h1>Lens Mode</h1>
          <p className="muted">
            Photograph a fiscal receipt — free OCR extracts the total and saves it to your sales database
          </p>
        </div>
        <button className="btn secondary" disabled={busy} onClick={scanDemo}>
          Demo receipt
        </button>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      {ocrInfo && (
        <div className="card" style={{ marginBottom: '1rem', background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <strong>Free OCR</strong>
          <p className="muted" style={{ margin: '0.35rem 0 0' }}>
            Tesseract: {ocrInfo.tesseract ? 'ready' : 'not installed'} · OCR.space:{' '}
            {ocrInfo.ocr_space ? (ocrInfo.ocr_space_key_set ? 'API key set' : 'demo key') : 'off'}
            {ocrInfo.openai_vision ? ' · OpenAI Vision optional' : ''}
            . Photos use free OCR first — always review before confirm.
          </p>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div>
            <div className="label">Data completeness (14d)</div>
            <div className="metric small">{capturePct}%</div>
            <span className={`badge ${confidenceLabel.cls}`}>{confidenceLabel.text}</span>
          </div>
          <div>
            <div className="label">Forecast confidence</div>
            <div className="metric small">{confidencePct}%</div>
            <p className="muted" style={{ margin: 0, fontSize: '0.85rem' }}>
              Range widen ×{completeness?.range_widen_factor ?? 1}
            </p>
          </div>
          <div style={{ minWidth: 200 }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Expected receipts / day</label>
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
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
        {today && (
          <p className="muted" style={{ marginBottom: 0, marginTop: '0.75rem' }}>
            Today: {today.captured} / {today.expected} receipts
            {today.captured < today.expected
              ? ' — missing captures widen the forecast range'
              : ' — good capture rate'}
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
            <h2>1. Photograph the receipt</h2>
            <div className="dropzone lens-drop">
              <p><strong>Camera or gallery</strong></p>
              <p className="muted">Printed receipt or terminal screen</p>
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
              <img src={previewUrl} alt="Receipt preview" className="lens-preview" />
            )}
            <div className="row" style={{ marginTop: '1rem' }}>
              <button className="btn" disabled={!file || busy} onClick={scanFile}>
                {busy ? 'Processing…' : 'AI parse'}
              </button>
            </div>
          </div>
          <div className="card">
            <h2>Recent receipts</h2>
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Total</th>
                  <th>Status</th>
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
                    <td colSpan={3} className="muted">No receipts yet</td>
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
            <h2>2. Review</h2>
            <p className="muted">
              Engine: {capture?.ocr_engine || '—'} · confidence{' '}
              {Math.round((capture?.parse_confidence || 0) * 100)}%
            </p>
            {previewUrl && <img src={previewUrl} alt="Receipt" className="lens-preview" />}
            {parsed?.raw_text && <pre className="ocr-text">{parsed.raw_text}</pre>}
          </div>
          <div className="card">
            <h2>Extracted fields</h2>
            <div className="field">
              <label>Date</label>
              <input
                type="date"
                value={form.receipt_date}
                onChange={(e) => setForm({ ...form, receipt_date: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Time</label>
              <input
                type="time"
                value={form.receipt_time || ''}
                onChange={(e) => setForm({ ...form, receipt_time: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Total (GEL)</label>
              <input
                type="number"
                step="0.01"
                value={form.total}
                onChange={(e) => setForm({ ...form, total: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Payment</label>
              <select
                value={form.payment_method}
                onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
              >
                <option value="cash">Cash</option>
                <option value="card">Card</option>
              </select>
            </div>
            <div className="field">
              <label>TIN (optional)</label>
              <input
                value={form.tin}
                onChange={(e) => setForm({ ...form, tin: e.target.value })}
              />
            </div>
            <p style={{ fontWeight: 600, color: 'var(--pine)' }}>
              Do you want to record what you sold?
            </p>
            <div className="row">
              <button className="btn" disabled={busy} onClick={() => setStep('items')}>
                Yes, add items
              </button>
              <button
                className="btn secondary"
                disabled={busy || !form.total}
                onClick={() => confirmSale(false)}
              >
                Skip — total only
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
              Back
            </button>
          </div>
        </div>
      )}

      {step === 'items' && (
        <div className="card">
          <h2>3. Items (lightweight log)</h2>
          <p className="muted">
            Not a full POS — quick item notes that improve forecasting over time
          </p>
          {items.map((item, idx) => (
            <div className="row" key={idx} style={{ marginBottom: '0.5rem' }}>
              <input
                placeholder="Product"
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
                placeholder="Price"
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
              + Line
            </button>
            <button className="btn" disabled={busy} onClick={() => confirmSale(true)}>
              Save with items
            </button>
            <button className="btn secondary" disabled={busy} onClick={() => confirmSale(false)}>
              Total only
            </button>
            <button className="btn ghost" onClick={() => setStep('review')}>
              Back
            </button>
          </div>
        </div>
      )}

      {step === 'done' && (
        <div className="card">
          <h2>Saved</h2>
          <p>
            Receipt added to sales and daily revenue. The dashboard forecast will use this data.
          </p>
          <button
            className="btn"
            onClick={() => {
              setStep('capture')
              setSuccess('')
            }}
          >
            New receipt
          </button>
        </div>
      )}
    </>
  )
}
