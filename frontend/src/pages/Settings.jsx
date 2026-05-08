import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Eye, EyeOff, CheckCircle, AlertCircle, Save, Lock } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { updateProfile } from '../api/auth'

function Section({ title, children, index = 0 }) {
  return (
    <motion.div
      className="card p-6"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.35 }}
    >
      <p className="section-label mb-5">{title}</p>
      {children}
    </motion.div>
  )
}

function Toast({ type, msg, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t) }, [onClose])
  return (
    <motion.div
      className={`fixed bottom-6 right-6 flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-sm font-medium z-50 ${type === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-700'}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
    >
      {type === 'success' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
      {msg}
    </motion.div>
  )
}

export default function Settings() {
  const { user, updateUser } = useAuth()

  const [profile, setProfile] = useState({
    name: user?.name || '',
    business_name: user?.business_name || '',
  })
  const [pw, setPw]         = useState({ current: '', next: '', confirm: '' })
  const [showPw, setShowPw] = useState(false)
  const [saving, setSaving] = useState(false)
  const [toast, setToast]   = useState(null)
  const [notifs, setNotifs] = useState({ scan_complete: true, weekly_report: false })

  const showToast = (type, msg) => setToast({ type, msg })

  const saveProfile = async e => {
    e.preventDefault()
    setSaving(true)
    try {
      const res = await updateProfile({ name: profile.name, business_name: profile.business_name })
      updateUser(res.data)
      showToast('success', 'Profile updated successfully.')
    } catch (err) {
      showToast('error', err.response?.data?.detail || 'Failed to update profile.')
    } finally {
      setSaving(false)
    }
  }

  const savePassword = async e => {
    e.preventDefault()
    if (pw.next !== pw.confirm) { showToast('error', 'New passwords do not match.'); return }
    if (pw.next.length < 8)    { showToast('error', 'Password must be at least 8 characters.'); return }
    setSaving(true)
    try {
      await updateProfile({ current_password: pw.current, new_password: pw.next })
      setPw({ current: '', next: '', confirm: '' })
      showToast('success', 'Password changed successfully.')
    } catch (err) {
      showToast('error', err.response?.data?.detail || 'Failed to change password.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col flex-1">
      <div className="page-header">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Settings</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage your account and preferences</p>
        </div>
      </div>

      <div className="px-8 py-6 space-y-5 max-w-2xl">
        {/* Profile */}
        <Section title="Profile" index={0}>
          <form onSubmit={saveProfile} className="space-y-4">
            <div className="flex items-center gap-4 mb-2">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white text-xl font-extrabold shrink-0">
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div>
                <p className="font-bold text-slate-900 text-sm">{user?.name || 'User'}</p>
                <p className="text-xs text-slate-500">{user?.email}</p>
              </div>
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Full name</label>
                <input
                  value={profile.name}
                  onChange={e => setProfile(p => ({ ...p, name: e.target.value }))}
                  className="input-field"
                  placeholder="Your name"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Business name</label>
                <input
                  value={profile.business_name}
                  onChange={e => setProfile(p => ({ ...p, business_name: e.target.value }))}
                  className="input-field"
                  placeholder="Optional"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">Email address</label>
              <input
                value={user?.email || ''}
                disabled
                className="input-field opacity-60 cursor-not-allowed"
              />
              <p className="text-xs text-slate-400 mt-1">Email cannot be changed</p>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={saving}
                className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5 disabled:opacity-60"
              >
                <Save size={14} />
                {saving ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </form>
        </Section>

        {/* Password */}
        <Section title="Password" index={1}>
          <form onSubmit={savePassword} className="space-y-4">
            {[
              { key: 'current', label: 'Current password',     placeholder: '••••••••' },
              { key: 'next',    label: 'New password',         placeholder: 'Min. 8 characters' },
              { key: 'confirm', label: 'Confirm new password', placeholder: 'Re-enter' },
            ].map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">{label}</label>
                <div className="relative">
                  <input
                    type={showPw ? 'text' : 'password'}
                    value={pw[key]}
                    onChange={e => setPw(p => ({ ...p, [key]: e.target.value }))}
                    placeholder={placeholder}
                    className="input-field pr-10"
                  />
                  {key === 'current' && (
                    <button
                      type="button"
                      onClick={() => setShowPw(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                    >
                      {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={saving || !pw.current || !pw.next || !pw.confirm}
                className="btn-primary flex items-center gap-2 text-sm px-5 py-2.5 disabled:opacity-50"
              >
                <Lock size={14} />
                {saving ? 'Saving…' : 'Update password'}
              </button>
            </div>
          </form>
        </Section>

        {/* Notifications */}
        <Section title="Notifications" index={2}>
          <div className="space-y-5">
            {[
              { key: 'scan_complete', label: 'Scan complete alerts',  desc: 'Get notified when a fraud scan finishes.' },
              { key: 'weekly_report', label: 'Weekly summary report', desc: 'Receive a weekly digest of your detection activity.' },
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-700">{label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setNotifs(n => ({ ...n, [key]: !n[key] }))}
                  className={`relative w-10 h-[22px] rounded-full transition-colors duration-200 shrink-0 ${notifs[key] ? 'bg-blue-600' : 'bg-slate-200'}`}
                >
                  <span className={`absolute top-[3px] w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200 ${notifs[key] ? 'translate-x-[22px]' : 'translate-x-[3px]'}`} />
                </button>
              </div>
            ))}
          </div>
        </Section>

        {/* Danger zone */}
        <Section title="Account" index={3}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-700">Delete account</p>
              <p className="text-xs text-slate-400 mt-0.5">Permanently remove your account and all detection history.</p>
            </div>
            <button
              type="button"
              onClick={() => showToast('error', 'Contact support to delete your account.')}
              className="text-xs font-bold text-red-600 border border-red-200 px-4 py-2 rounded-xl hover:bg-red-50 transition-colors shrink-0"
            >
              Delete account
            </button>
          </div>
        </Section>
      </div>

      {toast && <Toast type={toast.type} msg={toast.msg} onClose={() => setToast(null)} />}
    </div>
  )
}
