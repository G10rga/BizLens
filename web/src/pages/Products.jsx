import { useEffect, useState } from 'react'
import { api, authMediaUrl } from '../api'
import BarcodePreview from '../components/BarcodePreview'
import { useI18n } from '../i18n'

const empty = { name: '', price: '', category: '', barcode: '' }

/** Simple EAN-13-style numeric code (12 random digits + check digit). */
function generateBarcode() {
  let body = ''
  for (let i = 0; i < 12; i += 1) {
    body += String(Math.floor(Math.random() * 10))
  }
  let sum = 0
  for (let i = 0; i < 12; i += 1) {
    const n = Number(body[i])
    sum += i % 2 === 0 ? n : n * 3
  }
  const check = (10 - (sum % 10)) % 10
  return body + String(check)
}

export default function Products() {
  const { t, money } = useI18n()
  const [products, setProducts] = useState([])
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [existingImageUrl, setExistingImageUrl] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [clearImage, setClearImage] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = async () => setProducts(await api('/products?active=false'))

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  useEffect(() => {
    if (!imageFile) {
      setImagePreview(null)
      return undefined
    }
    const url = URL.createObjectURL(imageFile)
    setImagePreview(url)
    return () => URL.revokeObjectURL(url)
  }, [imageFile])

  const resetForm = () => {
    setForm(empty)
    setEditing(null)
    setExistingImageUrl(null)
    setImageFile(null)
    setClearImage(false)
  }

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = {
        name: form.name.trim(),
        price: Number(form.price),
        category: form.category.trim() || null,
        barcode: form.barcode.trim() || null,
        active: true,
      }
      if (editing && clearImage && !imageFile) {
        payload.clear_image = true
      }
      // JSON for fields (compatible), then optional photo upload
      let product
      if (editing) {
        product = await api(`/products/${editing}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        })
      } else {
        product = await api('/products', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
      }
      if (imageFile) {
        const fd = new FormData()
        fd.append('image', imageFile, imageFile.name || 'product.jpg')
        product = await api(`/products/${product.id}/image`, {
          method: 'POST',
          body: fd,
        })
      }
      resetForm()
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const startEdit = (p) => {
    setEditing(p.id)
    setForm({
      name: p.name,
      price: String(p.price),
      category: p.category || '',
      barcode: p.barcode || '',
    })
    setExistingImageUrl(p.image_url || null)
    setImageFile(null)
    setClearImage(false)
  }

  const remove = async (id) => {
    await api(`/products/${id}`, { method: 'DELETE' })
    await load()
  }

  const previewSrc = imagePreview || (!clearImage && existingImageUrl ? authMediaUrl(existingImageUrl) : null)
  const active = products.filter((p) => p.active)

  const printBarcode = () => {
    const svg = document.getElementById('product-barcode-svg')
    if (!svg) return
    const win = window.open('', '_blank', 'noopener,noreferrer,width=520,height=360')
    if (!win) return
    win.document.write(`<!doctype html><html><head><title>${form.barcode.trim()}</title>
      <style>
        body{margin:24px;display:grid;place-items:center;font-family:system-ui,sans-serif}
        svg{max-width:100%;height:auto}
        p{margin:8px 0 0;text-align:center;font-size:14px;letter-spacing:0.04em}
      </style></head><body>
      ${svg.outerHTML}
      <p>${form.name.trim() || form.barcode.trim()}</p>
      </body></html>`)
    win.document.close()
    win.focus()
    win.print()
  }

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('products.title')}</h1>
          <p className="muted">{t('products.activeCount', { count: active.length })}</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="grid grid-2">
        <form className="card" onSubmit={save}>
          <h2>{editing ? t('products.editProduct') : t('products.newProduct')}</h2>
          <div className="field">
            <label>{t('products.name')}</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </div>
          <div className="field">
            <label>{t('products.price')}</label>
            <input required type="number" min="0" step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
          </div>
          <div className="field">
            <label>{t('products.category')}</label>
            <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          </div>
          <div className="field">
            <label>{t('products.image')}</label>
            <p className="muted" style={{ margin: '0 0 0.45rem', fontSize: '0.82rem' }}>
              {t('products.imageHint')}
            </p>
            {previewSrc ? (
              <img src={previewSrc} alt="" className="product-form-preview" />
            ) : (
              <div className="product-form-preview empty">{t('products.noImage')}</div>
            )}
            <div className="row" style={{ gap: '0.5rem', marginTop: '0.55rem', flexWrap: 'wrap' }}>
              <label className="btn ghost" style={{ cursor: 'pointer', margin: 0 }}>
                {t('products.chooseImage')}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  hidden
                  onChange={(e) => {
                    const file = e.target.files?.[0] || null
                    setImageFile(file)
                    setClearImage(false)
                    e.target.value = ''
                  }}
                />
              </label>
              {(previewSrc || imageFile) && (
                <button
                  type="button"
                  className="btn ghost"
                  onClick={() => {
                    setImageFile(null)
                    setClearImage(true)
                    setExistingImageUrl(null)
                  }}
                >
                  {t('products.removeImage')}
                </button>
              )}
            </div>
          </div>
          <div className="field">
            <label>{t('products.barcode')}</label>
            <p className="muted" style={{ margin: '0 0 0.45rem', fontSize: '0.82rem' }}>
              {t('products.barcodeHint')}
            </p>
            <div className="row" style={{ gap: '0.5rem', alignItems: 'stretch' }}>
              <input
                value={form.barcode}
                onChange={(e) => setForm({ ...form, barcode: e.target.value })}
                placeholder={t('products.barcodePlaceholder')}
                inputMode="numeric"
                style={{ flex: 1 }}
              />
              <button
                type="button"
                className="btn ghost"
                onClick={() => setForm({ ...form, barcode: generateBarcode() })}
              >
                {t('products.generateBarcode')}
              </button>
            </div>
            {form.barcode.trim() && (
              <div className="barcode-preview-wrap">
                <BarcodePreview value={form.barcode.trim()} svgId="product-barcode-svg" />
                <div className="row" style={{ gap: '0.5rem', marginTop: '0.45rem', flexWrap: 'wrap' }}>
                  <button type="button" className="btn ghost" onClick={printBarcode}>
                    {t('products.printBarcode')}
                  </button>
                  <button
                    type="button"
                    className="btn ghost"
                    onClick={() => setForm({ ...form, barcode: '' })}
                  >
                    {t('products.clearBarcode')}
                  </button>
                </div>
              </div>
            )}
          </div>
          <div className="row">
            <button className="btn" disabled={busy}>{busy ? t('common.saving') : t('common.save')}</button>
            {editing && (
              <button type="button" className="btn ghost" onClick={resetForm}>
                {t('common.cancel')}
              </button>
            )}
          </div>
        </form>
        <div className="card">
          <h2>{t('products.catalog')}</h2>
          <table className="table">
            <thead>
              <tr>
                <th>{t('products.name')}</th>
                <th>{t('products.priceCol')}</th>
                <th>{t('products.barcodeCol')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {active.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div className="product-catalog-cell">
                      {p.image_url ? (
                        <img src={authMediaUrl(p.image_url)} alt="" className="product-catalog-thumb" />
                      ) : (
                        <span className="product-catalog-thumb empty" aria-hidden="true" />
                      )}
                      <div>
                        <strong>{p.name}</strong>
                        {p.category && <div className="muted">{p.category}</div>}
                      </div>
                    </div>
                  </td>
                  <td>{money(p.price)}</td>
                  <td className="muted" style={{ fontVariantNumeric: 'tabular-nums', fontSize: '0.85rem' }}>
                    {p.barcode || '—'}
                  </td>
                  <td className="row">
                    <button className="btn ghost" type="button" onClick={() => startEdit(p)}>{t('common.edit')}</button>
                    <button className="btn danger" type="button" onClick={() => remove(p.id)}>{t('common.delete')}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
