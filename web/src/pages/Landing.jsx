import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeIconButton } from '../theme'
import './landing.css'

const CHART = [5.55, 5.58, 5.62, 5.6, 5.55, 4.15, 4.35, 6.05, 6.35, 6.55, 6.84]

function gel(n, digits) {
  const d = digits ?? (Number.isInteger(n) ? 0 : 2)
  return `${Number(n).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })} ₾`
}

function ForecastChart() {
  const w = 520
  const h = 160
  const max = 8.2
  const min = 2
  const pts = CHART.map((v, i) => {
    const x = (i / (CHART.length - 1)) * w
    const y = h - ((v - min) / (max - min)) * h
    return [x, y]
  })
  const line = pts.map(([x, y]) => `${x},${y}`).join(' ')
  const area = `0,${h} ${line} ${w},${h}`
  const hi = pts.map(([x, y]) => `${x},${Math.max(8, y - 18)}`).join(' ')
  const lo = pts.map(([x, y]) => `${x},${Math.min(h - 8, y + 22)}`).join(' ')
  const band = `${hi} ${[...pts].reverse().map(([x, y]) => `${x},${Math.min(h - 8, y + 22)}`).join(' ')}`
  return (
    <svg className="lp-chart" viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
      <polygon points={band} fill="rgba(123, 227, 200, 0.35)" />
      <polyline points={hi} fill="none" stroke="rgba(123,227,200,0.0)" />
      <polyline points={lo} fill="none" stroke="rgba(123,227,200,0.0)" />
      <polygon points={area} fill="rgba(123, 227, 200, 0.18)" />
      <polyline points={line} fill="none" stroke="#2f9d7a" strokeWidth="2.6" strokeLinejoin="round" />
    </svg>
  )
}

const MOCK = [
  { name: 'ჩირი', cat: 'ჩირის ნაწარმი', meta: '1 ცალი · 3.2%', price: 4.8, qty: 2 },
  { name: 'შოთის პური', cat: 'პურეული', meta: '1 ცალი', price: 2.5, qty: 1 },
  { name: 'კექსები', cat: 'საცხობი', meta: '10 ცალი', price: 7.2, qty: 1 },
  { name: 'წყალი', cat: 'სასმელი', meta: '500 მლ', price: 1.5, qty: 3 },
]

const WHO = [
  ['whoBakery', 'whoBakeryBody', '🥐'],
  ['whoCafe', 'whoCafeBody', '☕'],
  ['whoRetail', 'whoRetailBody', '🧾'],
  ['whoPharmacy', 'whoPharmacyBody', '💊'],
  ['whoSalon', 'whoSalonBody', '✂'],
  ['whoOther', 'whoOtherBody', '⌂'],
]

function Title({ children }) {
  return <h2 className="lp-display">{children}</h2>
}

export default function Landing() {
  const { user, loading } = useAuth()
  const { t } = useI18n()
  const signedIn = !loading && user
  const appPath = user?.onboarding_complete ? '/pos' : '/onboarding'
  const [menuOpen, setMenuOpen] = useState(false)
  const [range, setRange] = useState(30)
  const close = () => setMenuOpen(false)

  const cta = signedIn ? (
    <Link className="lp-btn" to={appPath}>{t('landing.openApp')} →</Link>
  ) : (
    <Link className="lp-btn" to="/register">{t('landing.register')} →</Link>
  )

  return (
    <div className="lp">
      <header className="lp-nav">
        <div className="lp-brand">
          <div className="lp-mark">B</div>
          <div>
            <strong>{t('brand.name')}</strong>
            <span>{t('brand.tagline')}</span>
          </div>
        </div>
        <nav className={`lp-links${menuOpen ? ' open' : ''}`}>
          <a href="#features" onClick={close}>{t('landing.navFeatures')}</a>
          <a href="#how" onClick={close}>{t('landing.navHow')}</a>
          <a href="#faq" onClick={close}>{t('landing.navFaq')}</a>
        </nav>
        <div className="lp-nav-actions">
          <LanguageSwitcher variant="light" />
          <ThemeIconButton />
          {signedIn ? (
            <Link className="lp-btn" to={appPath}>{t('landing.openApp')}</Link>
          ) : (
            <>
              <Link className="lp-btn ghost" to="/login">{t('landing.login')}</Link>
              <Link className="lp-btn" to="/register">{t('landing.register')} →</Link>
            </>
          )}
          <button type="button" className="lp-burger" aria-label="menu" onClick={() => setMenuOpen((v) => !v)}>
            ☰
          </button>
        </div>
      </header>

      <section className="lp-hero lp-wrap">
        <div>
          <p className="lp-kicker">{t('landing.kicker')}</p>
          <h1 className="lp-display">{t('landing.heroTitle')}</h1>
          <p className="lp-lead">{t('landing.heroBody')}</p>
          <div className="lp-cta-row">
            {signedIn ? (
              <Link className="lp-btn" to={appPath}>{t('landing.openApp')} →</Link>
            ) : (
              <>
                <Link className="lp-btn" to="/register">{t('landing.register')} →</Link>
                <Link className="lp-btn ghost" to="/login">{t('landing.login')}</Link>
              </>
            )}
          </div>
          <p className="lp-caption">{signedIn ? t('landing.stayLoggedIn') : t('landing.builtFor')}</p>
        </div>
        <aside className="lp-preview">
          <div className="lp-preview-top">
            <h3>{t('landing.previewTitle')}</h3>
            <span>{t('landing.previewStore')}</span>
          </div>
          <div className="lp-preview-stats">
            <div>
              <span>{t('landing.previewSold')}</span>
              <strong>{gel(1248)}</strong>
            </div>
            <div>
              <span>{t('landing.previewBalance')}</span>
              <strong>{gel(5628)}</strong>
            </div>
          </div>
          <div className="lp-preview-chart">
            <div className="lp-preview-chart-h">
              <span>{t('landing.previewForecast')}</span>
              <div className="lp-pills">
                {[30, 60, 90].map((d) => (
                  <button key={d} type="button" className={range === d ? 'on' : ''} onClick={() => setRange(d)}>
                    {t(`landing.d${d}`)}
                  </button>
                ))}
              </div>
            </div>
            <ForecastChart />
            <div className="lp-preview-chart-f">
              <span>{t('landing.previewRange')}</span>
              <strong>{gel(6840)}</strong>
            </div>
          </div>
          <p className="lp-preview-note">{t('landing.previewNote')}</p>
        </aside>
      </section>

      <section className="lp-strip lp-wrap">
        <div><span className="lp-ico">↺</span>{t('landing.stripSell')}</div>
        <div><span className="lp-ico">▣</span>{t('landing.stripCosts')}</div>
        <div><span className="lp-ico">↗</span>{t('landing.stripForecast')}</div>
      </section>

      <section className="lp-band" id="features">
        <div className="lp-wrap lp-split">
          <div>
            <p className="lp-kicker">{t('landing.clarityKicker')}</p>
            <Title>{t('landing.clarityTitle')}</Title>
          </div>
          <p className="lp-lead">{t('landing.clarityBody')}</p>
        </div>
        <div className="lp-wrap lp-steps3">
          {[1, 2, 3].map((n) => (
            <article key={n}>
              <span>0{n}</span>
              <h3>{t(`landing.step${n}Title`)}</h3>
              <p>{t(`landing.step${n}Body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="lp-wrap lp-pos-sec">
        <div className="lp-pos-copy">
          <p className="lp-kicker">{t('landing.posKicker')}</p>
          <Title>{t('landing.posTitle')}</Title>
          <p className="lp-lead">{t('landing.posBody')}</p>
          <div className="lp-inline-chip">
            <span className="lp-ico">↺</span>
            <div>
              <strong>{t('landing.posChip')}</strong>
              <p>{t('landing.posChipBody')}</p>
            </div>
          </div>
        </div>
        <div className="lp-pos-mock">
          <div className="lp-pos-mock-h">
            <strong>{t('landing.posChip')}</strong>
            <span>მზიური საცხობი · #0048</span>
          </div>
          <input className="lp-pos-search" readOnly value={t('landing.posSearch')} />
          <div className="lp-pos-mock-grid">
            {MOCK.map((p) => (
              <div className="lp-pos-tile" key={p.name}>
                <span className="lp-pos-tile-cat">{p.cat} <em>✓ {p.qty}</em></span>
                <strong>{p.name}</strong>
                <span className="muted">{p.meta}</span>
                <div className="lp-pos-tile-f">
                  <b>{gel(p.price, 2)}</b>
                  <span className="lp-plus">+</span>
                </div>
              </div>
            ))}
          </div>
          <aside className="lp-pos-cart">
            <h4>{t('landing.posCartTitle')}</h4>
            {MOCK.map((p) => (
              <div className="lp-pos-line" key={p.name}>
                <span>{p.name} × {p.qty}</span>
                <b>{gel(p.price * p.qty, 2)}</b>
              </div>
            ))}
            <div className="lp-pos-line total">
              <span>სულ</span>
              <b>{gel(23.8, 2)}</b>
            </div>
            <div className="lp-pos-pay">
              <button type="button" className="on">{t('landing.posCash')}</button>
              <button type="button">{t('landing.posCard')}</button>
            </div>
            <button type="button" className="lp-btn lp-pos-done">{t('landing.posComplete')}</button>
            <p className="lp-preview-note">{t('landing.posNote')}</p>
          </aside>
        </div>
      </section>

      <section className="lp-wrap lp-capture">
        <p className="lp-kicker">{t('landing.captureKicker')}</p>
        <Title>{t('landing.captureTitle')}</Title>
        <p className="lp-lead">{t('landing.captureBody')}</p>
        <div className="lp-capture-grid">
          <article className="lp-panel">
            <div className="lp-panel-h">
              <span className="lp-ico">📷</span>
              <h3>{t('landing.lensTitle')}</h3>
            </div>
            <p>{t('landing.lensBody')}</p>
            <div className="lp-receipt">
              <div className="lp-receipt-paper">
                <strong>საცხობი "მზიური"</strong>
                <span>ქვითარი · #0048</span>
                <ul>
                  <li><span>ჩირი × 2</span><b>9.60 ₾</b></li>
                  <li><span>შოთის პური</span><b>2.50 ₾</b></li>
                  <li><span>კექსები</span><b>7.20 ₾</b></li>
                  <li><span>წყალი × 3</span><b>4.50 ₾</b></li>
                </ul>
                <div className="lp-pos-line total"><span>სულ 23.80 ₾</span></div>
                <div className="lp-barcode" />
              </div>
              <div className="lp-scan">
                <span>{t('landing.lensScan')}</span>
                <strong>{gel(23.8, 2)}</strong>
                <small>{t('landing.lensHint')}</small>
              </div>
            </div>
            <p className="lp-preview-note">{t('landing.posNote')}</p>
          </article>
          <article className="lp-panel">
            <div className="lp-panel-h">
              <span className="lp-ico">▤</span>
              <h3>{t('landing.csvTitle')}</h3>
            </div>
            <p>{t('landing.csvBody')}</p>
            <div className="lp-csv-file">
              <span className="lp-ico">▤</span>
              <div>
                <strong>sales-october.csv</strong>
                <small>{t('landing.csvFile')}</small>
              </div>
            </div>
            <div className="lp-csv-table">
              <div className="lp-csv-row head">
                <span>{t('landing.csvDate')}</span>
                <span>{t('landing.csvSales')}</span>
              </div>
              {[['11.10.2026', '1,180.00 ₾'], ['12.10.2026', '1,096.00 ₾'], ['13.10.2026', '1,248.00 ₾']].map(([d, v]) => (
                <div className="lp-csv-row" key={d}>
                  <span>{d}</span>
                  <b>{v}</b>
                </div>
              ))}
            </div>
            <p className="lp-caption">{t('landing.csvHint')}</p>
            <p className="lp-preview-note">{t('landing.posNote')}</p>
            <p className="lp-preview-note">{t('landing.csvFoot')}</p>
          </article>
        </div>
      </section>

      <section className="lp-wrap lp-money">
        <div className="lp-split">
          <div>
            <p className="lp-kicker">{t('landing.moneyKicker')}</p>
            <Title>{t('landing.moneyTitle')}</Title>
          </div>
          <p className="lp-lead">{t('landing.moneyLead')}</p>
        </div>
        <div className="lp-money-grid">
          <article className="lp-panel">
            <div className="lp-panel-h">
              <span className="lp-ico">▣</span>
              <h3>{t('landing.moneyCardTitle')}</h3>
            </div>
            <p>{t('landing.moneyCardBody')}</p>
            <div className="lp-money-rows">
              <div><span>{t('landing.moneyStart')}</span><b>4,800 ₾</b></div>
              <div className="up"><span>{t('landing.moneyIn')}</span><b>+1,248 ₾</b></div>
              <div className="down"><span>{t('landing.moneyOut')}</span><b>−420 ₾</b></div>
              <div className="now"><span>{t('landing.moneyNow')}</span><b>5,628 ₾</b></div>
            </div>
            <p className="lp-preview-note">{t('landing.posNote')}</p>
          </article>
          <article className="lp-panel mint">
            <div className="lp-panel-h">
              <span className="lp-ico">🔔</span>
              <h3>{t('landing.alertTitle')}</h3>
            </div>
            <p>{t('landing.alertBody')}</p>
            <div className="lp-alert">
              <strong>⚠ {t('landing.alertWarn')}</strong>
              <p>{t('landing.alertWarnBody')}</p>
              <Link to="/register">{t('landing.alertCta')}</Link>
            </div>
            <div className="lp-alert soft">
              <strong>⌂ {t('landing.alertSeason')}</strong>
            </div>
            <p className="lp-preview-note">{t('landing.posNote')}</p>
          </article>
        </div>
      </section>

      <section className="lp-forecast-band">
        <div className="lp-wrap">
          <div className="lp-split">
            <div>
              <p className="lp-kicker">{t('landing.forecastKicker')}</p>
              <Title>{t('landing.forecastTitle')}</Title>
            </div>
            <p className="lp-lead">{t('landing.forecastLead')}</p>
          </div>
          <div className="lp-forecast-grid">
            <article className="lp-panel">
              <div className="lp-preview-chart-h">
                <h3>{t('landing.forecastCard')}</h3>
                <div className="lp-pills">
                  <button type="button" className="on">{t('landing.d30')}</button>
                  <button type="button">{t('landing.d60')}</button>
                  <button type="button">{t('landing.d90')}</button>
                </div>
              </div>
              <div className="lp-fc-nums">
                <div>
                  <span>{t('landing.forecastAvg')}</span>
                  <strong>{gel(6840)}</strong>
                </div>
                <div>
                  <span>{t('landing.forecastBand')}</span>
                  <strong>5,200 - 8,100 ₾</strong>
                </div>
              </div>
              <ForecastChart />
              <p className="lp-preview-note">{t('landing.posNote')}</p>
            </article>
            <article className="lp-panel">
              <h3>{t('landing.forecastWhy')}</h3>
              <p>{t('landing.forecastWhyBody')}</p>
              <div className="lp-money-rows">
                <div><span>{t('landing.forecastNow')}</span><b>5,628 ₾</b></div>
                <div className="up"><span>{t('landing.forecastIn')}</span><b>+28,600 ₾</b></div>
                <div className="down"><span>{t('landing.forecastOut')}</span><b>−27,388 ₾</b></div>
                <div className="now"><span>{t('landing.forecastEnd')}</span><b>6,840 ₾</b></div>
              </div>
              <div className="lp-range-card">
                <span>{t('landing.forecastRange')}</span>
                <strong>24,000 - 33,000 ₾</strong>
              </div>
              <p className="lp-preview-note">{t('landing.forecastStar')}</p>
            </article>
          </div>
          <p className="lp-disclaimer">{t('landing.forecastDisclaimer')}</p>
        </div>
      </section>

      <section className="lp-wrap lp-how-sec" id="how">
        <div className="lp-how-head">
          <div>
            <p className="lp-kicker">{t('landing.howKicker')}</p>
            <Title>{t('landing.howTitle')}</Title>
          </div>
          {cta}
        </div>
        <div className="lp-how-steps">
          {[1, 2, 3].map((n) => (
            <article key={n}>
              <div className="lp-how-n">
                <strong>0{n}</strong>
                <span className="lp-ico">{n === 1 ? '⌂' : n === 2 ? '▤' : '↗'}</span>
              </div>
              <h3>{t(`landing.how${n}Title`)}</h3>
              <p>{t(`landing.how${n}Body`)}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="lp-who">
        <div className="lp-wrap">
          <div className="lp-split">
            <div>
              <p className="lp-kicker">{t('landing.whoKicker')}</p>
              <Title>{t('landing.whoTitle')}</Title>
            </div>
            <p className="lp-lead">{t('landing.whoLead')}</p>
          </div>
          <div className="lp-who-grid">
            {WHO.map(([title, body, ico]) => (
              <article key={title}>
                <span className="lp-ico">{ico}</span>
                <div>
                  <h3>{t(`landing.${title}`)}</h3>
                  <p>{t(`landing.${body}`)}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="lp-wrap lp-faq-sec" id="faq">
        <div className="lp-faq-copy">
          <p className="lp-kicker">{t('landing.faqKicker')}</p>
          <Title>{t('landing.faqTitle')}</Title>
          <p className="lp-lead">{t('landing.faqLead')}</p>
        </div>
        <div className="lp-faq">
          {[1, 2, 3, 4, 5].map((n) => (
            <details key={n} open={n === 1}>
              <summary>{t(`landing.faq${n}q`)}</summary>
              <p>{t(`landing.faq${n}a`)}</p>
            </details>
          ))}
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-wrap lp-footer-cta">
          <div>
            <p className="lp-kicker light">{t('landing.footerKicker')}</p>
            <h2 className="lp-display">{t('landing.footerTitle')}</h2>
            <p>{t('landing.footerBody')}</p>
          </div>
          <div className="lp-footer-actions">
            {cta}
            {!signedIn && <Link className="lp-text-link" to="/login">{t('landing.footerAlready')}</Link>}
          </div>
        </div>
        <div className="lp-wrap lp-footer-cols">
          <div>
            <div className="lp-brand">
              <div className="lp-mark">B</div>
              <div>
                <strong>{t('brand.name')}</strong>
                <span>{t('brand.tagline')}</span>
              </div>
            </div>
            <p className="lp-caption">{t('landing.kicker')}</p>
          </div>
          <div>
            <h4>{t('landing.footerColProduct')}</h4>
            <a href="#features">{t('landing.footerPos')}</a>
            <a href="#features">{t('landing.footerLens')}</a>
            <a href="#features">{t('landing.footerCash')}</a>
          </div>
          <div>
            <h4>{t('landing.footerColStart')}</h4>
            <a href="#how">{t('landing.footerHow')}</a>
            <Link to="/register">{t('landing.footerRegister')}</Link>
            <Link to="/login">{t('landing.footerLogin')}</Link>
          </div>
          <div>
            <h4>{t('landing.footerColMore')}</h4>
            <a href="#how">{t('landing.footerAbout')}</a>
            <a href="#faq">{t('landing.footerQa')}</a>
            <span>{t('landing.footerLang')}</span>
          </div>
        </div>
        <div className="lp-wrap lp-footer-legal">
          <span>{t('landing.footerCopy')}</span>
          <span>{t('landing.footerLegal')}</span>
        </div>
      </footer>
    </div>
  )
}
