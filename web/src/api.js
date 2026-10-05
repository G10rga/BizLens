const TOKEN_KEY = 'bizlens_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`/api${path}`, { ...options, headers })
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    // Flask/nginx HTML error pages — don't dump markup into the UI
    const stripped = text.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
    const short =
      stripped.slice(0, 180) ||
      (res.status === 502
        ? 'Server unavailable (502)'
        : res.status === 500
          ? 'Server error (500)'
          : 'Invalid response')
    data = { error: short }
  }
  if (!res.ok) {
    const err = new Error(data?.error || `Request failed (${res.status})`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

export const money = (n, lang = 'ka') =>
  `${Number(n || 0).toLocaleString(lang === 'ka' ? 'ka-GE' : 'en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} ₾`
