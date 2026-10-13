const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const NAME_EXTRA = new Set([' ', '-', "'", '’'])

export function isLettersName(value) {
  return [...value].every((ch) => /\p{L}/u.test(ch) || NAME_EXTRA.has(ch))
}

export function isNonNegMoney(value) {
  const s = String(value ?? '').trim()
  if (!/^\d+(\.\d{1,2})?$/.test(s)) return false
  return Number(s) >= 0
}

export function isPositiveMoney(value) {
  return isNonNegMoney(value) && Number(value) > 0
}

export function isIntInRange(value, min, max) {
  const s = String(value ?? '').trim()
  if (!/^-?\d+$/.test(s)) return false
  const n = Number(s)
  return n >= min && n <= max
}

export function validateRegister(form, t) {
  const errors = {}
  const name = (form.full_name || '').trim()
  const email = (form.email || '').trim()
  const password = form.password || ''

  if (!name) errors.full_name = t('validation.nameRequired')
  else if (name.length < 2 || name.length > 50) errors.full_name = t('validation.nameLength')
  else if (!isLettersName(name)) errors.full_name = t('validation.nameChars')

  if (!email) errors.email = t('validation.emailRequired')
  else if (email.length > 254) errors.email = t('validation.emailLength')
  else if (!EMAIL_RE.test(email)) errors.email = t('validation.emailFormat')

  if (!password) errors.password = t('validation.passwordRequired')
  else if (password.length < 8 || password.length > 128) errors.password = t('validation.passwordLength')
  else if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
    errors.password = t('validation.passwordComplexity')
  }

  return errors
}

export function validateBusinessProfile(profile, t) {
  const errors = {}
  const name = (profile.name || '').trim()
  if (!name) errors.name = t('validation.businessNameRequired')
  else if (name.length < 2 || name.length > 80) errors.name = t('validation.businessNameLength')

  if (!profile.business_type) errors.business_type = t('validation.selectType')
  if (!profile.city) errors.city = t('validation.selectCity')
  return errors
}

export function validateExpenses(expenses, t) {
  const errors = {}
  expenses.forEach((exp, i) => {
    if (!isNonNegMoney(exp.amount)) errors[`amount_${i}`] = t('validation.moneyRequired')
    if (!isIntInRange(exp.due_day, 1, 31)) errors[`due_${i}`] = t('validation.paymentDay')
  })
  return errors
}

export function validateSuppliers(suppliers, t) {
  const filled = suppliers.filter((s) => {
    const name = (s.name || '').trim()
    const amount = String(s.amount ?? '').trim()
    const n = String(s.every_n_days ?? '').trim()
    return Boolean(name || amount || n)
  })
  if (filled.length === 0) return { skip: true, errors: {} }

  const errors = {}
  suppliers.forEach((s, i) => {
    const name = (s.name || '').trim()
    const amount = String(s.amount ?? '').trim()
    const n = String(s.every_n_days ?? '').trim()
    const any = Boolean(name || amount || n)
    if (!any) return
    if (name.length < 2 || name.length > 80) errors[`name_${i}`] = t('validation.supplierName')
    if (!isPositiveMoney(s.amount)) errors[`amount_${i}`] = t('validation.supplierAmount')
    if (!isIntInRange(s.every_n_days, 1, 365)) errors[`n_${i}`] = t('validation.everyNDays')
  })
  return { skip: false, errors }
}

export function validateCash(cash, t) {
  if (!isNonNegMoney(cash)) return t('validation.cashRequired')
  return ''
}

export function firstError(errors) {
  return Object.values(errors).find(Boolean) || ''
}
