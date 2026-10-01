import { useEffect, useState } from 'react'
import { api } from '../api'
import { useI18n } from '../i18n'

const empty = { name: '', price: '', category: '' }

export default function Products() {
  const { t, money } = useI18n()
  const [products, setProducts] = useState([])
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = async () => setProducts(await api('/products?active=false'))

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = {
        name: form.name,
        price: Number(form.price),
        category: form.category || null,
        active: true,
      }
      if (editing) {
        await api(`/products/${editing}`, { method: 'PUT', body: JSON.stringify(payload) })
      } else {
        await api('/products', { method: 'POST', body: JSON.stringify(payload) })
      }
      setForm(empty)
      setEditing(null)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const startEdit = (p) => {
    setEditing(p.id)
    setForm({ name: p.name, price: String(p.price), category: p.category || '' })
  }

  const remove = async (id) => {
    await api(`/products/${id}`, { method: 'DELETE' })
    await load()
  }

  const active = products.filter((p) => p.active)

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
          <div className="row">
            <button className="btn" disabled={busy}>{busy ? t('common.saving') : t('common.save')}</button>
            {editing && (
              <button type="button" className="btn ghost" onClick={() => { setEditing(null); setForm(empty) }}>
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
                <th></th>
              </tr>
            </thead>
            <tbody>
              {active.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.name}</strong>
                    {p.category && <div className="muted">{p.category}</div>}
                  </td>
                  <td>{money(p.price)}</td>
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
