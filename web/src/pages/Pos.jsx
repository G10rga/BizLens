import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeIconButton, useTheme } from '../theme'

export default function Pos() {
  const { refresh, business } = useAuth()
  const { t, money } = useI18n()
  const { theme } = useTheme()
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const [busy, setBusy] = useState(false)
  const [q, setQ] = useState('')
  const [cat, setCat] = useState('all')
  const [payMethod, setPayMethod] = useState('cash')
  const [received, setReceived] = useState('')
  const [clock, setClock] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 30000)
    return () => clearInterval(id)
  }, [])

  const load = async () => {
    const data = await api('/products')
    setProducts(data)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const categories = useMemo(() => {
    const set = new Set(products.map((p) => p.category).filter(Boolean))
    return [...set]
  }, [products])

  const filtered = products.filter((p) => {
    const matchQ = p.name.toLowerCase().includes(q.toLowerCase())
    const matchCat = cat === 'all' || p.category === cat
    return matchQ && matchCat
  })

  const total = useMemo(
    () => cart.reduce((s, i) => s + i.unit_price * i.quantity, 0),
    [cart]
  )
  const units = useMemo(() => cart.reduce((s, i) => s + i.quantity, 0), [cart])
  const receivedNum = Number(received)
  const change = payMethod === 'cash' && receivedNum >= total ? receivedNum - total : 0

  const qtyOf = (id) => cart.find((i) => i.product_id === id)?.quantity || 0

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
          category: product.category,
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

  const charge = async () => {
    if (!cart.length) return
    setBusy(true)
    setError('')
    try {
      const sale = await api('/sales', {
        method: 'POST',
        body: JSON.stringify({ payment_method: payMethod, items: cart }),
      })
      setSuccess(sale)
      setCart([])
      setReceived('')
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const methodLabel = (method) => (method === 'card' ? t('common.card') : t('common.cash'))
  const tone = theme === 'dark' ? 'dark' : 'light'
  const timeLabel = clock.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return (
    <div className="pos-desk">
      <div className="pos-head">
        <div>
          <h1>{t('pos.title')}</h1>
          {business?.name && <p className="pos-store">▾ {business.name}</p>}
        </div>
        <div className="pos-head-tools">
          <LanguageSwitcher variant={tone} />
          <ThemeIconButton />
          <span className="pos-clock">{timeLabel}</span>
        </div>
      </div>
      {error && <div className="error">{error}</div>}
      {success && (
        <div className="success">
          {t('pos.sold', { id: success.id, total: money(success.total), method: methodLabel(success.payment_method) })}
        </div>
      )}
      <div className="pos-layout">
        <div className="pos-catalog">
          <div className="pos-cat-head">
            <h2>{t('pos.products')}</h2>
            <span className="muted">{t('pos.productCount', { count: products.length })}</span>
          </div>
          <div className="pos-search-wrap">
            <input
              className="pos-search"
              placeholder={t('pos.search')}
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <div className="pos-chips">
            <button type="button" className={cat === 'all' ? 'on' : ''} onClick={() => setCat('all')}>
              {t('pos.all')} {products.length}
            </button>
            {categories.map((c) => (
              <button type="button" key={c} className={cat === c ? 'on' : ''} onClick={() => setCat(c)}>
                {c} {products.filter((p) => p.category === c).length}
              </button>
            ))}
          </div>
          <p className="pos-hint">{t('pos.hint')}</p>
          {!filtered.length && <p className="muted">{t('pos.emptyProducts')}</p>}
          <div className="product-grid">
            {filtered.map((p) => {
              const qty = qtyOf(p.id)
              return (
                <button
                  key={p.id}
                  type="button"
                  className={`product-tile${qty ? ' in-cart' : ''}`}
                  title={p.name}
                  onClick={() => add(p)}
                >
                  {qty > 0 && <span className="tile-qty">✓ {qty}</span>}
                  <span className="tile-cat">{p.category || '\u00a0'}</span>
                  <strong>{p.name}</strong>
                  <span className="price">{money(p.price)}</span>
                  <span className="tile-add" aria-hidden="true">+</span>
                </button>
              )
            })}
          </div>
        </div>
        <aside className="pos-cart">
          <div className="pos-cart-h">
            <h2>{t('pos.cart')}</h2>
            <button type="button" className="pos-trash" onClick={() => setCart([])} aria-label={t('common.delete')}>
              ⌫
            </button>
          </div>
          <input className="pos-customer" readOnly value={t('pos.customer')} />
          {!cart.length && <p className="muted">{t('pos.emptyCart')}</p>}
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
          {!!cart.length && (
            <p className="pos-cart-meta">
              {t('pos.cartMeta', { products: cart.length, units })}
            </p>
          )}
          <div className="pos-cart-total">
            <span>{t('pos.total')}</span>
            <strong>{money(total)}</strong>
          </div>
          <div className="pos-pay">
            <button type="button" className={payMethod === 'cash' ? 'on' : ''} onClick={() => setPayMethod('cash')}>
              {t('common.cash')}
            </button>
            <button type="button" className={payMethod === 'card' ? 'on' : ''} onClick={() => setPayMethod('card')}>
              {t('common.card')}
            </button>
          </div>
          {payMethod === 'cash' && (
            <div className="pos-cash-row">
              <label>
                {t('pos.received')}
                <input
                  inputMode="decimal"
                  value={received}
                  onChange={(e) => setReceived(e.target.value)}
                  placeholder="0.00"
                />
              </label>
              <label>
                {t('pos.change')}
                <input readOnly value={change ? money(change) : ''} />
              </label>
            </div>
          )}
          <button className="pos-complete" disabled={!cart.length || busy} onClick={charge}>
            ✓ {t('pos.complete')} →
          </button>
        </aside>
      </div>
    </div>
  )
}
