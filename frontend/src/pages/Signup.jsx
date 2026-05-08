import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react'
import Logo from '../components/ui/Logo'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { signup } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ name: '', email: '', business_name: '', password: '', confirm: '' })
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = e => setForm(f => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async e => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      await signup({ name: form.name, email: form.email, business_name: form.business_name, password: form.password })
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const pwStrength = (() => {
    const p = form.password
    if (!p) return null
    if (p.length < 6) return { label: 'Weak', color: 'bg-red-400', w: 'w-1/4' }
    if (p.length < 10) return { label: 'Fair', color: 'bg-amber-400', w: 'w-1/2' }
    return { label: 'Strong', color: 'bg-green-500', w: 'w-full' }
  })()

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="px-8 py-5">
        <Link to="/" className="inline-flex items-center gap-2">
          <Logo size={28} />
          <span className="font-extrabold text-slate-900 text-sm tracking-tight">TransferNet</span>
        </Link>
      </div>

      <div className="flex-1 flex items-center justify-center px-4 pb-12">
        <motion.div
          className="w-full max-w-sm"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="card p-8">
            <div className="mb-7">
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Create your account</h1>
              <p className="text-sm text-slate-500 mt-1">Start detecting fraudulent transfers today</p>
            </div>

            {error && (
              <div className="mb-5 flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                <AlertCircle size={15} className="shrink-0 mt-0.5" />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Full name</label>
                <input
                  name="name"
                  type="text"
                  required
                  value={form.name}
                  onChange={handleChange}
                  placeholder="Ada Okafor"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Business name</label>
                <input
                  name="business_name"
                  type="text"
                  value={form.business_name}
                  onChange={handleChange}
                  placeholder="Okafor Enterprises (optional)"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Email address</label>
                <input
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={form.email}
                  onChange={handleChange}
                  placeholder="ada@company.com"
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    name="password"
                    type={showPw ? 'text' : 'password'}
                    required
                    value={form.password}
                    onChange={handleChange}
                    placeholder="Min. 8 characters"
                    className="input-field pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                  </button>
                </div>
                {pwStrength && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`h-full ${pwStrength.color} ${pwStrength.w} transition-all duration-300`} />
                    </div>
                    <span className="text-xs text-slate-400 font-medium w-12 text-right">{pwStrength.label}</span>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Confirm password</label>
                <div className="relative">
                  <input
                    name="confirm"
                    type={showPw ? 'text' : 'password'}
                    required
                    value={form.confirm}
                    onChange={handleChange}
                    placeholder="Re-enter password"
                    className="input-field pr-10"
                  />
                  {form.confirm && form.password === form.confirm && (
                    <CheckCircle size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500" />
                  )}
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full py-2.5 text-sm mt-1 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creating account…
                  </span>
                ) : 'Create account'}
              </button>
            </form>

            <p className="text-center text-xs text-slate-500 mt-6">
              Already have an account?{' '}
              <Link to="/login" className="text-blue-600 font-semibold hover:text-blue-700">
                Sign in
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
