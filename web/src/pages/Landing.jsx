import { Link } from 'react-router-dom'
import { useAuth } from '../auth'
import { LanguageSwitcher, useI18n } from '../i18n'
import { ThemeToggle } from '../theme'

const FEATURES = [
  ['posTitle', 'posBody'],
  ['lensTitle', 'lensBody'],
  ['forecastTitle', 'forecastBody'],
  ['alertsTitle', 'alertsBody'],
  ['csvTitle', 'csvBody'],
  ['expensesTitle', 'expensesBody'],
]

export default function Landing() {
  const { user, loading } = useAuth()
  const { t } = useI18n()
  const signedIn = !loading && user
  const appPath = user?.onboarding_complete ? '/pos' : '/onboarding'

  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand">
          <div className="brand-mark landing-mark">B</div>
          <div>
            <strong>{t('brand.name')}</strong>
            <span>{t('brand.tagline')}</span>
          </div>
        </div>
        <div className="row">
          <LanguageSwitcher variant="light" />
          <ThemeToggle />
          {signedIn ? (
            <Link className="btn" to={appPath}>{t('landing.openApp')}</Link>
          ) : (
            <>
              <Link className="btn ghost" to="/login">{t('landing.login')}</Link>
              <Link className="btn" to="/register">{t('landing.register')}</Link>
            </>
          )}
        </div>
      </header>

      <section className="landing-hero">
        <p className="label">{t('landing.kicker')}</p>
        <h1>{t('landing.heroTitle')}</h1>
        <p className="muted landing-lead">{t('landing.heroBody')}</p>
        <div className="row">
          {signedIn ? (
            <>
              <Link className="btn" to={appPath}>{t('landing.openApp')}</Link>
              <p className="muted" style={{ margin: 0 }}>{t('landing.stayLoggedIn')}</p>
            </>
          ) : (
            <>
              <Link className="btn" to="/register">{t('landing.register')}</Link>
              <Link className="btn secondary" to="/login">{t('landing.login')}</Link>
            </>
          )}
        </div>
        {!signedIn && <p className="muted" style={{ marginTop: '1rem' }}>{t('landing.demo')}</p>}
      </section>

      <section>
        <h2>{t('landing.featuresTitle')}</h2>
        <div className="grid grid-3">
          {FEATURES.map(([title, body]) => (
            <div className="card" key={title}>
              <h3>{t(`landing.features.${title}`)}</h3>
              <p className="muted" style={{ margin: 0 }}>{t(`landing.features.${body}`)}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>{t('landing.howTitle')}</h2>
        <div className="grid grid-3">
          {[1, 2, 3].map((n) => (
            <div className="card" key={n}>
              <div className="landing-step">{n}</div>
              <p style={{ margin: 0 }}>{t(`landing.how${n}`)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
