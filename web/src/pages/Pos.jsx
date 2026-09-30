import { useEffect, useMemo, useState } from 'react'
import { api, money } from '../api'
import { useAuth } from '../auth'

export default function Pos() {
  const { refresh } = useAuth()
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')

  const load = async () => {
    const data = await api('/products')
    setProducts(data)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const filtered = products.filter((p) =>
    p.name.toLowerCase().includes(q.toLowerCase())
  )

  const total = useMemo(
    () => cart.reduce((s, i) => s + i.unit_price * i.quantity, 0),
    [cart]
  )

  const add = (product) => {
    setSuccess(null)
    setCart((prev) => {
      const existing = prev.find((i) => i.product_id === product.id)
      if (existing) {
        return prev.map((i) =>
          i.product_id === product.id ? { ...i, quantity: i.quantity + 1 } : i
        )
      }
      return [
        ...prev,
        {
          product_id: product.id,
          product_name: product.name,
          unit_price: product.price,
          quantity: 1,
        },
      ]
    })
  }

  const setQty = (productId, quantity) => {
    setCart((prev) =>
      prev
        .map((i) => (i.product_id === productId ? { ...i, quantity } : i))
        .filter((i) => i.quantity > 0)
    )
  }

  const charge = async (payment_method) => {
    if (!cart.length) return
    setBusy(true)
    setError('')
    try {
      const sale = await api('/sales', {
        method: 'POST',
        body: JSON.stringify({ payment_method, items: cart }),
      })
      setSuccess(sale)
      setCart([])
      await refresh()
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
          <h1>POS / სალარო</h1>
          <p className="muted">შეეხეთ პროდუქტს · აირჩიეთ ნაღდი ან ბარათი</p>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {success && (
        <div className="success">
          გაყიდვა #{success.id} შენახულია · {money(success.total)} · {success.payment_method}
        </div>
      )}
      <div className="pos-layout">
        <div className="card">
          <input
            placeholder="ძიება..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            style={{ width: '100%', marginBottom: '1rem', padding: '0.7rem', borderRadius: 8, border: '1px solid #cbd5e1' }}
          />
          {!filtered.length && <p className="muted">პროდუქტები არ არის. დაამატეთ პროდუქტების გვერდზე.</p>}
          <div className="product-grid">
            {filtered.map((p) => (
              <button key={p.id} type="button" className="product-tile" onClick={() => add(p)}>
                <strong>{p.name}</strong>
                <div className="price">{money(p.price)}</div>
                {p.category && <div className="muted" style={{ fontSize: '0.8rem' }}>{p.category}</div>}
              </button>
            ))}
          </div>
        </div>
        <div className="card">
          <h2>მიმდინარე შეკვეთა</h2>
          {!cart.length && <p className="muted">კალათა ცარიელია</p>}
          {cart.map((item) => (
            <div className="cart-line" key={item.product_id}>
              <div>
                <strong>{item.product_name}</strong>
                <div className="muted">{money(item.unit_price)}</div>
              </div>
              <div className="qty">
                <button type="button" onClick={() => setQty(item.product_id, item.quantity - 1)}>-</button>
                <span>{item.quantity}</span>
                <button type="button" onClick={() => setQty(item.product_id, item.quantity + 1)}>+</button>
              </div>
              <strong>{money(item.unit_price * item.quantity)}</strong>
            </div>
          ))}
          <div style={{ marginTop: '1rem' }} className="row">
            <span className="label">ჯამი</span>
            <span className="metric" style={{ marginLeft: 'auto' }}>{money(total)}</span>
          </div>
          <div className="row" style={{ marginTop: '1rem' }}>
            <button className="btn mint" style={{ flex: 1 }} disabled={!cart.length || busy} onClick={() => charge('cash')}>
              ნაღდი
            </button>
            <button className="btn" style={{ flex: 1 }} disabled={!cart.length || busy} onClick={() => charge('card')}>
              ბარათი
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
