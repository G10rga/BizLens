import { useEffect, useState } from 'react'
import { api, money } from '../api'

export default function CsvUpload() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [busy, setBusy] = useState(false)

  const loadHistory = async () => setHistory(await api('/csv/history'))

  useEffect(() => {
    loadHistory().catch((e) => setError(e.message))
  }, [])

  const formData = () => {
    const fd = new FormData()
    fd.append('file', file)
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
      setSuccess(`იმპორტირებულია ${res.rows_imported} დღე`)
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
          <h1>CSV / Excel იმპორტი (Pro)</h1>
          <p className="muted">ატვირთეთ POS ექსპორტი · სვეტები: Date + Total</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}
      <div className="grid grid-2">
        <div className="card">
          <div className="dropzone">
            <p><strong>აირჩიეთ Excel ან CSV</strong></p>
            <p className="muted">მაგ: Date = 6/25/2023 (Sun), Total = 80.30</p>
            <input
              type="file"
              accept=".xlsx,.xls,.xlsm,.csv,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              onChange={(e) => {
                setFile(e.target.files?.[0] || null)
                setPreview(null)
              }}
            />
          </div>
          <div className="row" style={{ marginTop: '1rem' }}>
            <button className="btn secondary" disabled={!file || busy} onClick={doPreview}>Preview</button>
            <button className="btn" disabled={!file || busy} onClick={doImport}>Import</button>
          </div>
          {preview && (
            <div style={{ marginTop: '1rem' }}>
              <p>
                {preview.total_rows} დღე · {preview.date_from} → {preview.date_to}
              </p>
              <table className="table">
                <thead><tr><th>თარიღი</th><th>გაყიდვა</th></tr></thead>
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
          <h2>ისტორია</h2>
          <table className="table">
            <thead>
              <tr><th>ფაილი</th><th>სტატუსი</th><th>რიგები</th><th>დრო</th></tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td>{h.filename}</td>
                  <td>{h.status}</td>
                  <td>{h.rows_imported}</td>
                  <td>{new Date(h.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {!history.length && <tr><td colSpan="4" className="muted">იმპორტები არ არის</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
