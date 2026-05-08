import { motion } from 'framer-motion'

export default function ConfidenceBar({ value, prediction }) {
  const color = prediction === 'FAKE'
    ? 'bg-red-500'
    : prediction === 'GENUINE'
    ? 'bg-green-500'
    : 'bg-slate-400'

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Confidence</span>
        <span className="text-sm font-bold text-slate-900">{value}%</span>
      </div>
      <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}
