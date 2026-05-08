import { motion } from 'framer-motion'

export default function StatCard({ icon: Icon, value, label, sub, accent = 'blue', index = 0 }) {
  const accents = {
    blue:   { bar: 'bg-slate-900',  icon: 'bg-slate-100 text-slate-700' },
    red:    { bar: 'bg-red-500',    icon: 'bg-red-50 text-red-600'      },
    green:  { bar: 'bg-green-500',  icon: 'bg-green-50 text-green-600'  },
    amber:  { bar: 'bg-amber-500',  icon: 'bg-amber-50 text-amber-600'  },
  }
  const a = accents[accent] || accents.blue

  return (
    <motion.div
      className="card p-5 relative overflow-hidden"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.35 }}
    >
      <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${a.bar}`} />
      <div className={`w-9 h-9 rounded-xl ${a.icon} flex items-center justify-center mb-4`}>
        {Icon && <Icon size={17} strokeWidth={2} />}
      </div>
      <div className="text-3xl font-extrabold text-slate-900 tracking-tight leading-none mb-1">
        {value}
      </div>
      <div className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-0.5">{label}</div>
      {sub && <div className="text-xs text-slate-400">{sub}</div>}
    </motion.div>
  )
}
