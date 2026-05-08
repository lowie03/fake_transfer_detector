import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Send, X, AlertCircle } from 'lucide-react'
import ResultCard from '../components/ui/ResultCard'
import { detectSMS } from '../api/detect'

const EXAMPLES = [
  'Your GTBank account 0012345678 has been credited with NGN 50,000.00 on 01-05-26. Bal: NGN 135,200.00. Ref: 2605011234567.',
  'Dear Customer, NGN 10,000 has been debited from your UBA account ending 4321. Avail Bal: NGN 22,500. If not you, call 0700-225-0000.',
]

const BANK_OPTIONS = [
  { label: 'GTBank (GTWorld)', value: 'GTBank' },
  { label: 'Moniepoint MFB',   value: 'Moniepoint' },
  { label: 'Zenith Bank',      value: 'Zenith' },
];

export default function SMSDetection() {
  const [text, setText]       = useState('')
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const [bank, setBank]       = useState('GTBank')

  const handleSubmit = async e => {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return
    setLoading(true)
    setError('')
    try {
      const res = await detectSMS(trimmed, bank)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const clear = () => { setText(''); setResult(null); setError('') }

  return (
    <div className="flex flex-col flex-1">
      <div className="page-header">
       <div className="mb-4">
        <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Select Bank</label>
        <select
          value={bank}
          onChange={(e) => setBank(e.target.value)}
          className="w-full mt-1.5 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-blue-400"
        >
          {BANK_OPTIONS.map(b => (
            <option key={b.value} value={b.value}>{b.label}</option>
          ))}
        </select>
      </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">SMS Verification</h1>
          <p className="text-sm text-slate-500 mt-0.5">Paste a bank debit/credit SMS to detect spoofing</p>
        </div>
      </div>

      <div className="px-8 py-6 space-y-6">
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Input panel */}
          <motion.div
            className="card p-6"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
          >
            <p className="section-label mb-4">Paste SMS Text</p>

            {error && (
              <div className="mb-4 flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                <AlertCircle size={15} className="shrink-0 mt-0.5" />
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <textarea
                  value={text}
                  onChange={e => { setText(e.target.value); setResult(null) }}
                  rows={6}
                  placeholder={`Paste the full SMS text here…\n\nExample: Your GTBank account has been credited with NGN 50,000.00 on 01-05-26.`}
                  className="input-field resize-none leading-relaxed text-sm"
                />
                {text && (
                  <button
                    type="button"
                    onClick={clear}
                    className="absolute top-3 right-3 w-6 h-6 bg-slate-100 rounded-full flex items-center justify-center hover:bg-slate-200 transition-colors"
                  >
                    <X size={11} className="text-slate-500" />
                  </button>
                )}
              </div>

              <div className="flex items-center justify-between text-xs text-slate-400">
                <span>{text.length} characters</span>
                <span>{text.trim().split(/\s+/).filter(Boolean).length} words</span>
              </div>

              <button
                type="submit"
                disabled={!text.trim() || loading}
                className="btn-blue w-full py-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <Send size={14} />
                    Analyze SMS
                  </>
                )}
              </button>
            </form>

            <div className="mt-6">
              <p className="section-label mb-2.5">Example messages</p>
              <div className="space-y-2">
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => { setText(ex); setResult(null); setError('') }}
                    className="w-full text-left text-xs text-slate-500 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl px-4 py-3 leading-relaxed transition-colors"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Result panel */}
          <div>
            <AnimatePresence mode="wait">
              {result ? (
                <ResultCard key="result" result={result} />
              ) : (
                <motion.div
                  key="placeholder"
                  className="card p-6 flex flex-col items-center justify-center text-center min-h-48"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <MessageSquare size={32} className="text-slate-200 mb-3" />
                  <p className="text-sm font-semibold text-slate-400">Result will appear here</p>
                  <p className="text-xs text-slate-300 mt-1 max-w-xs">Paste an SMS and click Analyze to see the AI verdict</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Tips */}
        <motion.div
          className="card p-5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.35 }}
        >
          <p className="section-label mb-3">What to look for</p>
          <ul className="text-xs text-slate-500 space-y-1.5 leading-relaxed">
            <li className="flex gap-2"><span className="text-blue-400 font-bold">•</span> Paste the complete SMS without editing — partial text reduces accuracy.</li>
            <li className="flex gap-2"><span className="text-blue-400 font-bold">•</span> The model checks sender patterns, number formats, keyword placement, and syntax anomalies.</li>
            <li className="flex gap-2"><span className="text-blue-400 font-bold">•</span> Always cross-verify large transactions directly through your bank's official app.</li>
          </ul>
        </motion.div>
      </div>
    </div>
  )
}
