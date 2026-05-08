import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, Info, Zap } from 'lucide-react'
import Badge from './Badge'
import ConfidenceBar from './ConfidenceBar'

export default function ResultCard({ result }) {
  const isFake = result.prediction === 'FAKE'

  const borderColor = isFake ? 'border-red-200' : 'border-green-200'
  const headerBg    = isFake ? 'bg-red-50' : 'bg-green-50'
  const Icon        = isFake ? AlertTriangle : CheckCircle
  const iconColor   = isFake ? 'text-red-500' : 'text-green-600'

  return (
    <motion.div
      className={`card border-2 ${borderColor} overflow-hidden`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* Header */}
      <div className={`${headerBg} px-6 py-4 flex items-center justify-between`}>
        <div className="flex items-center gap-3">
          <Icon size={22} className={iconColor} strokeWidth={2} />
          <span className="font-bold text-slate-900 text-base">
            {isFake ? 'Fraudulent Alert Detected' : 'Genuine Transaction'}
          </span>
        </div>
        <Badge label={result.prediction} />
      </div>

      {/* Body */}
      <div className="px-6 py-5 space-y-5">
        <ConfidenceBar value={result.confidence} prediction={result.prediction} />

        {result.risk_level && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Risk Level</span>
            <Badge label={result.risk_level} variant={result.risk_level} />
          </div>
        )}

        {result.explanation && (
          <div className="space-y-1.5">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Info size={12} /> Explanation
            </p>
            <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 rounded-xl px-4 py-3 border border-slate-100">
              {result.explanation}
            </p>
          </div>
        )}

        {result.action && (
          <div className={`rounded-xl px-4 py-3 flex items-start gap-3 ${isFake ? 'bg-red-50 border border-red-100' : 'bg-green-50 border border-green-100'}`}>
            <Zap size={15} className={isFake ? 'text-red-500 mt-0.5 shrink-0' : 'text-green-600 mt-0.5 shrink-0'} />
            <p className={`text-sm font-medium ${isFake ? 'text-red-700' : 'text-green-700'}`}>
              {result.action}
            </p>
          </div>
        )}

        {result.timestamp && (
          <p className="text-xs text-slate-400">
            Analyzed at {result.timestamp} · Pipeline: {result.pipeline || '—'}
          </p>
        )}
      </div>
    </motion.div>
  )
}
