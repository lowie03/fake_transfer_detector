export default function Badge({ label, variant }) {
  const map = {
    FAKE:    'bg-red-50 text-red-700 border border-red-200',
    GENUINE: 'bg-green-50 text-green-700 border border-green-200',
    HIGH:    'bg-red-50 text-red-700 border border-red-200',
    MEDIUM:  'bg-amber-50 text-amber-700 border border-amber-200',
    LOW:     'bg-yellow-50 text-yellow-700 border border-yellow-200',
    SAFE:    'bg-green-50 text-green-700 border border-green-200',
    UNKNOWN: 'bg-slate-50 text-slate-600 border border-slate-200',
  }
  const cls = map[variant || label?.toUpperCase()] || map.UNKNOWN
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wide ${cls}`}>
      {label}
    </span>
  )
}
