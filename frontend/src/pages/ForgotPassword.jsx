import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Mail, ArrowLeft, AlertCircle } from 'lucide-react'
import Logo from '../components/ui/Logo'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')

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
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center mb-4">
                <Mail size={18} className="text-blue-600" />
              </div>
              <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Reset your password</h1>
              <p className="text-sm text-slate-500 mt-1">Password recovery for your TransferNet account.</p>
            </div>

            <div className="flex items-start gap-2.5 bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-xl mb-5">
              <AlertCircle size={15} className="shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-xs">Not yet available</p>
                <p className="text-xs mt-0.5 leading-relaxed">
                  Password reset is not available in this prototype. Please contact the administrator or register a new account.
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <Link
                to="/signup"
                className="btn-primary w-full py-2.5 text-sm text-center block"
              >
                Create a new account
              </Link>
              <p className="text-center text-xs text-slate-500">
                <Link to="/login" className="text-blue-600 font-semibold hover:text-blue-700 inline-flex items-center gap-1">
                  <ArrowLeft size={11} /> Back to sign in
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
