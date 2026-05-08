import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import ProtectedRoute from './router/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ForgotPassword from './pages/ForgotPassword'
import Dashboard from './pages/Dashboard'
import ScreenshotDetection from './pages/ScreenshotDetection'
import SMSDetection from './pages/SMSDetection'
import Reports from './pages/Reports'
import Settings from './pages/Settings'

export default function App() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/signup" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Protected dashboard shell */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/screenshot" element={<ScreenshotDetection />} />
          <Route path="/dashboard/sms" element={<SMSDetection />} />
          <Route path="/dashboard/reports" element={<Reports />} />
          <Route path="/dashboard/settings" element={<Settings />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
