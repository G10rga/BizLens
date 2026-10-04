import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { api, getToken, money as formatMoney } from '../api'
import { useAuth } from '../auth'
import en from './en'
import ka from './ka'

const LANG_KEY = 'bizlens_lang'
const dictionaries = { ka, en }

function readStoredLang() {
  try {
    const v = localStorage.getItem(LANG_KEY)
    if (v === 'en' || v === 'ka') return v
  } catch {
    /* ignore */
  }
  return 'ka'
}

function lookup(dict, path) {
  return path.split('.').reduce((obj, key) => (obj && obj[key] != null ? obj[key] : undefined), dict)
}

function interpolate(str, vars) {
  if (!vars) return str
  return str.replace(/\{(\w+)\}/g, (_, key) => (vars[key] != null ? String(vars[key]) : `{${key}}`))
}

const I18nContext = createContext(null)

export const switchPairStyle = {
  display: 'flex',
  flexDirection: 'row',
  flexGrow: 0,
  flexShrink: 0,
  alignItems: 'center',
  height: 36,
  minHeight: 36,
  maxHeight: 36,
  overflow: 'hidden',
  boxSizing: 'border-box',
}

export const switchBtnStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flex: '1 1 0',
  height: 36,
  minHeight: 36,
  maxHeight: 36,
  margin: 0,
  padding: '0 12px',
  boxSizing: 'border-box',
  lineHeight: 1,
}

export function I18nProvider({ children }) {
  const { user, refresh } = useAuth()
  const [lang, setLangState] = useState(readStoredLang)
  const lastUserId = useRef(null)

  const applyLang = useCallback((next) => {
    setLangState(next)
    try {
      localStorage.setItem(LANG_KEY, next)
    } catch {
      /* ignore */
    }
    document.documentElement.lang = next
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
  }, [lang])

  useEffect(() => {
    if (!user) {
      lastUserId.current = null
      return
    }
    const isNewSession = lastUserId.current !== user.id
    lastUserId.current = user.id
    if (!isNewSession) return

    const stored = readStoredLang()
    if (stored !== user.language) {
      applyLang(stored)
      api('/settings', { method: 'PUT', body: JSON.stringify({ language: stored }) }).catch(() => {})
      return
    }
    if (user.language === 'ka' || user.language === 'en') {
      applyLang(user.language)
    }
  }, [user, applyLang])

  const setLanguage = useCallback(
    async (next) => {
      if (next !== 'ka' && next !== 'en') return
      applyLang(next)
      if (!getToken()) return
      try {
        await api('/settings', {
          method: 'PUT',
          body: JSON.stringify({ language: next }),
        })
        await refresh()
      } catch {
        /* keep local choice even if save fails */
      }
    },
    [applyLang, refresh]
  )

  const t = useCallback(
    (key, vars) => {
      const value = lookup(dictionaries[lang], key) ?? lookup(dictionaries.ka, key) ?? key
      return typeof value === 'string' ? interpolate(value, vars) : key
    },
    [lang]
  )

  const money = useCallback((n) => formatMoney(n, lang), [lang])

  const value = useMemo(
    () => ({ lang, setLanguage, t, money }),
    [lang, setLanguage, t, money]
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error('useI18n must be used inside I18nProvider')
  return ctx
}

export function LanguageSwitcher({ variant = 'dark' }) {
  const { lang, setLanguage, t } = useI18n()

  return (
    <div
      className={`lang-switch ${variant}`}
      role="group"
      aria-label={t('common.language')}
      style={switchPairStyle}
    >
      <button
        type="button"
        className={lang === 'ka' ? 'active' : ''}
        aria-pressed={lang === 'ka'}
        onClick={() => setLanguage('ka')}
        style={switchBtnStyle}
      >
        ქარ
      </button>
      <button
        type="button"
        className={lang === 'en' ? 'active' : ''}
        aria-pressed={lang === 'en'}
        onClick={() => setLanguage('en')}
        style={switchBtnStyle}
      >
        EN
      </button>
    </div>
  )
}
