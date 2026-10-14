import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeIconButton, useTheme } from '../theme'

function formatOrderNo(id) {
  return String(id).padStart(4, '0')
}

function formatSoldAt(iso, locale) {
  if (!iso) return { date: '', time: '' }
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  return {
    date: d.toLocaleDateString(locale, { year: 'numeric', month: '2-digit', day: '2-digit' }),
    time: d.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  }
}

export default function Pos() {
  const { refresh, business } = useAuth()
  const { t, money, lang } = useI18n()
  const { theme } = useTheme()
  const [products, setProducts] = useState([])
  const [cart, setCart] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)
  const [showReceipt, setShowReceipt] = useState(false)
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
    const qLower = q.toLowerCase().trim()
    const matchQ =
      !qLower ||
      p.name.toLowerCase().includes(qLower) ||
      (p.barcode && p.barcode.includes(q.trim()))
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
    setShowReceipt(false)
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
      const receipt = {
        ...sale,
        received: payMethod === 'cash' && receivedNum > 0 ? receivedNum : null,
        change: payMethod === 'cash' && receivedNum >= sale.total ? receivedNum - sale.total : null,
      }
      setSuccess(receipt)
      setShowReceipt(true)
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
  const locale = lang === 'ka' ? 'ka-GE' : 'en-GB'
  const soldAt = success ? formatSoldAt(success.sold_at, locale) : { date: '', time: '' }

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
        <div className="success pos-success-bar">
          <span>
            {t('pos.sold', {
              id: success.id,
              total: money(success.total),
              method: methodLabel(success.payment_method),
            })}
          </span>
          <button type="button" className="btn ghost pos-receipt-btn" onClick={() => setShowReceipt(true)}>
            {t('pos.viewReceipt')}
          </button>
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
                  title={p.barcode ? `${p.name} · ${p.barcode}` : p.name}
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

      {showReceipt && success && (
        <div className="receipt-overlay" role="dialog" aria-modal="true" aria-label={t('pos.receiptTitle')}>
          <div className="receipt-panel no-print">
            <div className="receipt-panel-actions">
              <button type="button" className="btn" onClick={() => window.print()}>
                {t('pos.printReceipt')}
              </button>
              <button type="button" className="btn ghost" onClick={() => setShowReceipt(false)}>
                {t('pos.closeReceipt')}
              </button>
            </div>
          </div>
          <div className="receipt-sheet" id="pos-receipt">
            <div className="receipt-brand">{business?.name || 'BizLens'}</div>
            {business?.city && <div className="receipt-place">{business.city}</div>}
            <div className="receipt-sep">--------------------------------</div>
            <div className="receipt-meta">
              <div>
                <span>{t('pos.receiptOrder')}</span>
                <strong>#{formatOrderNo(success.id)}</strong>
              </div>
              <div>
                <span>{t('pos.receiptDate')}</span>
                <strong>{soldAt.date}</strong>
              </div>
              <div>
                <span>{t('pos.receiptTime')}</span>
                <strong>{soldAt.time}</strong>
              </div>
              <div>
                <span>{t('pos.receiptPayment')}</span>
                <strong>{methodLabel(success.payment_method)}</strong>
              </div>
            </div>
            <div className="receipt-sep">--------------------------------</div>
            <div className="receipt-lines">
              {(success.items || []).map((item) => (
                <div className="receipt-line" key={item.id || `${item.product_name}-${item.quantity}`}>
                  <div className="receipt-line-name">{item.product_name}</div>
                  <div className="receipt-line-row">
                    <span>
                      {item.quantity} × {money(item.unit_price)}
                    </span>
                    <strong>{money(item.line_total)}</strong>
                  </div>
                </div>
              ))}
            </div>
            <div className="receipt-sep">--------------------------------</div>
            <div className="receipt-total">
              <span>{t('pos.receiptTotal')}</span>
              <strong>{money(success.total)}</strong>
            </div>
            {success.payment_method === 'cash' && success.received != null && (
              <>
                <div className="receipt-sub">
                  <span>{t('pos.received')}</span>
                  <span>{money(success.received)}</span>
                </div>
                {success.change != null && (
                  <div className="receipt-sub">
                    <span>{t('pos.change')}</span>
                    <span>{money(success.change)}</span>
                  </div>
                )}
              </>
            )}
            <div className="receipt-sep">--------------------------------</div>
            <div className="receipt-thanks">{t('pos.receiptThanks')}</div>
          </div>
        </div>
      )}
    </div>
  )
}
