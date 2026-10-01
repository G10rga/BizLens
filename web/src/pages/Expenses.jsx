import { useEffect, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { useI18n } from '../i18n'

export default function Expenses() {
  const { refresh } = useAuth()
  const { t, money } = useI18n()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [cash, setCash] = useState('')
  const [expenses, setExpenses] = useState([])
  const [suppliers, setSuppliers] = useState([])

  const load = async () => {
    const res = await api('/expenses')
    setData(res)
    setCash(String(res.cash_on_hand ?? ''))
    setExpenses(res.expenses.length ? res.expenses : [
      { name: 'rent', amount: 0, due_day: 1 },
      { name: 'salaries', amount: 0, due_day: 1 },
      { name: 'utilities', amount: 0, due_day: 10 },
    ])
    setSuppliers(res.suppliers)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api('/expenses', {
        method: 'PUT',
        body: JSON.stringify({
          cash_on_hand: Number(cash || 0),
          expenses: expenses.map((x) => ({
            name: x.name,
            amount: Number(x.amount),
            due_day: Number(x.due_day),
          })),
          suppliers: suppliers.map((s) => ({
            name: s.name,
            amount: Number(s.amount),
            every_n_days: Number(s.every_n_days),
            next_due_date: s.next_due_date,
          })),
        }),
      })
      await refresh()
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="topbar">
        <div>
          <h1>{t('expenses.title')}</h1>
          <p className="muted">{t('expenses.subtitle', { amount: data ? money(data.cash_on_hand) : '—' })}</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      <form className="card" onSubmit={save}>
        <div className="field">
          <label>{t('expenses.cashNow')}</label>
          <input type="number" step="0.01" value={cash} onChange={(e) => setCash(e.target.value)} />
        </div>
        <h3>{t('expenses.fixed')}</h3>
        {expenses.map((exp, i) => (
          <div className="row" key={i}>
            <div className="field" style={{ flex: 2 }}>
              <label>{t('common.name')}</label>
              <input value={exp.name} onChange={(e) => {
                const n = [...expenses]; n[i] = { ...exp, name: e.target.value }; setExpenses(n)
              }} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>{t('common.amount')}</label>
              <input type="number" value={exp.amount} onChange={(e) => {
                const n = [...expenses]; n[i] = { ...exp, amount: e.target.value }; setExpenses(n)
              }} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>{t('common.day')}</label>
              <input type="number" min="1" max="28" value={exp.due_day} onChange={(e) => {
                const n = [...expenses]; n[i] = { ...exp, due_day: e.target.value }; setExpenses(n)
              }} />
            </div>
          </div>
        ))}
        <h3>{t('expenses.suppliers')}</h3>
        {suppliers.map((s, i) => (
          <div className="row" key={i}>
            <div className="field" style={{ flex: 2 }}>
              <label>{t('common.name')}</label>
              <input value={s.name} onChange={(e) => {
                const n = [...suppliers]; n[i] = { ...s, name: e.target.value }; setSuppliers(n)
              }} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>{t('common.amount')}</label>
              <input type="number" value={s.amount} onChange={(e) => {
                const n = [...suppliers]; n[i] = { ...s, amount: e.target.value }; setSuppliers(n)
              }} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>{t('expenses.everyNDays')}</label>
              <input type="number" value={s.every_n_days} onChange={(e) => {
                const n = [...suppliers]; n[i] = { ...s, every_n_days: e.target.value }; setSuppliers(n)
              }} />
            </div>
            <div className="field" style={{ flex: 1 }}>
              <label>{t('expenses.nextDue')}</label>
              <input type="date" value={s.next_due_date?.slice?.(0, 10) || s.next_due_date} onChange={(e) => {
                const n = [...suppliers]; n[i] = { ...s, next_due_date: e.target.value }; setSuppliers(n)
              }} />
            </div>
          </div>
        ))}
        <button type="button" className="btn ghost" onClick={() => setSuppliers([
          ...suppliers,
          { name: 'Supplier', amount: 0, every_n_days: 14, next_due_date: new Date().toISOString().slice(0, 10) },
        ])}>{t('expenses.addSupplier')}</button>
        <div style={{ marginTop: '1rem' }}>
          <button className="btn" disabled={busy}>{busy ? t('common.saving') : t('common.save')}</button>
        </div>
      </form>
    </>
  )
}
