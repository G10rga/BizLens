import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import { useI18n } from './i18n'
import Layout from './Layout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Onboarding from './pages/Onboarding'
import Pos from './pages/Pos'
import Products from './pages/Products'
import TodaySales from './pages/TodaySales'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import CsvUpload from './pages/CsvUpload'
import Lens from './pages/Lens'
import Expenses from './pages/Expenses'
import Settings from './pages/Settings'

function Protected({ children, needOnboardingDone = true }) {
  const { user, loading } = useAuth()
  const { t } = useI18n()
  if (loading) return <div className="auth-page"><p>{t('common.loading')}</p></div>
  if (!user) return <Navigate to="/login" replace />
  if (needOnboardingDone && !user.onboarding_complete) {
    return <Navigate to="/onboarding" replace />
  }
  if (!needOnboardingDone && user.onboarding_complete) {
    return <Navigate to="/pos" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/onboarding"
        element={
          <Protected needOnboardingDone={false}>
            <Onboarding />
          </Protected>
        }
      />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route path="pos" element={<Pos />} />
        <Route path="products" element={<Products />} />
        <Route path="today" element={<TodaySales />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="csv" element={<CsvUpload />} />
        <Route path="lens" element={<Lens />} />
        <Route path="expenses" element={<Expenses />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
