import { useEffect, useState } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

export default function CsvUpload() {
  const { t, money, lang } = useI18n()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [history, setHistory] = useState([])
  const [dailyDays, setDailyDays] = useState(0)
  const [replace, setReplace] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [busy, setBusy] = useState(false)

  const loadHistory = async () => {
    const res = await api('/csv/history')
    if (Array.isArray(res)) {
      setHistory(res)
      setDailyDays(0)
    } else {
      setHistory(res.imports || [])
      setDailyDays(res.daily_sales_days || 0)
    }
  }

  useEffect(() => {
    loadHistory().catch((e) => setError(e.message))
  }, [])

  const formData = () => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('replace', replace ? 'true' : 'false')
    return fd
  }

  const doPreview = async () => {
    if (!file) return
    setBusy(true)
    setError('')
    try {
      setPreview(await api('/csv/preview', { method: 'POST', body: formData() }))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const doImport = async () => {
    if (!file) return
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const res = await api('/csv/import', { method: 'POST', body: formData() })
      setSuccess(
        `${res.replaced ? t('csv.replaced') : ''}${t('csv.imported', { rows: res.rows_imported })}`
      )
      setPreview(null)
      setFile(null)
      await loadHistory()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const doClear = async () => {
    const ok = window.confirm(t('csv.confirmClear'))
    if (!ok) return
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const res = await api('/csv/data', {
        method: 'DELETE',
        body: JSON.stringify({ include_pos: true }),
      })
      setSuccess(
        t('csv.cleared', {
          days: res.daily_sales_deleted,
          imports: res.imports_deleted,
          pos: res.pos_sales_deleted,
        })
      )
      setPreview(null)
      setFile(null)
      await loadHistory()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('csv.title')}</h1>
          <p className="muted">
            {t('csv.subtitle')}
            {dailyDays ? t('csv.daysInDb', { days: dailyDays }) : ''}
          </p>
        </div>
        <button className="btn danger" disabled={busy || (!dailyDays && !history.length)} onClick={doClear}>
          {t('csv.clear')}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <div className="grid grid-2">
        <div className="card">
          <div className="dropzone">
            <p><strong>{t('csv.pickFile')}</strong></p>
            <p className="muted">{t('csv.example')}</p>
            <input
              type="file"
              accept=".xlsx,.xls,.xlsm,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              onChange={(e) => {
                setFile(e.target.files?.[0] || null)
                setPreview(null)
              }}
            />
          </div>
          <label className="row" style={{ marginTop: '1rem', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={replace}
              onChange={(e) => setReplace(e.target.checked)}
            />
            <span>{t('csv.replace')}</span>
          </label>
          <div className="row" style={{ marginTop: '1rem' }}>
            <button className="btn secondary" disabled={!file || busy} onClick={doPreview}>{t('csv.preview')}</button>
            <button className="btn" disabled={!file || busy} onClick={doImport}>{t('csv.import')}</button>
          </div>
          {preview && (
            <div style={{ marginTop: '1rem' }}>
              <p>
                {t('csv.previewMeta', { rows: preview.total_rows, from: preview.date_from, to: preview.date_to })}
              </p>
              <table className="table">
                <thead><tr><th>{t('csv.date')}</th><th>{t('csv.revenue')}</th></tr></thead>
                <tbody>
                  {preview.preview.map((r) => (
                    <tr key={r.date}><td>{r.date}</td><td>{money(r.revenue)}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="card">
          <h2>{t('csv.history')}</h2>
          <table className="table">
            <thead>
              <tr>
                <th>{t('csv.file')}</th>
                <th>{t('csv.status')}</th>
                <th>{t('csv.rows')}</th>
                <th>{t('csv.time')}</th>
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.filename}</td>
                  <td>{h.status}</td>
                  <td>{h.rows_imported}</td>
                  <td>{new Date(h.created_at).toLocaleString(lang === 'ka' ? 'ka-GE' : 'en-US')}</td>
                </tr>
              ))}
              {!history.length && <tr><td colSpan="4" className="muted">{t('csv.empty')}</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
