import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Camera, MessageSquare, ShieldAlert, ShieldCheck, Activity, ArrowRight, Clock } from 'lucide-react'
import StatCard from '../components/ui/StatCard'
import { getStats, getLog } from '../api/reports'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getStats(), getLog(1, 5)])
      .then(([s, l]) => {
        setStats(s.data)
        setRecent(l.data.entries || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const statCards = stats
    ? [
        { icon: Activity,    value: stats.total,        label: 'Total Scans',       accent: 'blue'  },
        { icon: ShieldAlert, value: stats.fake,         label: 'Fake Detected',     accent: 'red'   },
        { icon: ShieldCheck, value: stats.genuine,      label: 'Genuine',           accent: 'green' },
        { icon: Activity,    value: `${stats.accuracy}%`, label: 'Accuracy',        accent: 'amber' },
      ]
    : Array(4).fill(null)

  return (
    <div className="flex flex-col flex-1">
      <div className="page-header">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Overview of your fraud detection activity</p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/dashboard/screenshot" className="btn-primary flex items-center gap-2 text-sm px-4 py-2">
            <Camera size={14} /> New scan
          </Link>
        </div>
      </div>

      <div className="px-8 py-6 space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) =>
          loading || !card ? (
            <div key={i} className="card p-5 animate-pulse h-28 bg-slate-100" />
          ) : (
            <StatCard key={card.label} {...card} index={i} />
          )
        )}
      </div>

      {/* Quick actions */}
      <div className="grid md:grid-cols-2 gap-4">
        {[
          {
            to: '/dashboard/screenshot',
            icon: Camera,
            title: 'Verify Screenshot',
            desc: 'Upload a payment screenshot to check if it\'s genuine.',
            accent: 'blue',
          },
          {
            to: '/dashboard/sms',
            icon: MessageSquare,
            title: 'Verify SMS',
            desc: 'Paste an SMS debit/credit alert to detect spoofing.',
            accent: 'slate',
          },
        ].map((item, i) => (
          <motion.div
            key={item.to}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 + i * 0.07, duration: 0.35 }}
          >
            <Link
              to={item.to}
              className="card p-5 flex items-start gap-4 group hover:shadow-card-lg transition-shadow duration-200"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${item.accent === 'blue' ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-600'}`}>
                <item.icon size={18} strokeWidth={2} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-bold text-slate-900 text-sm mb-1">{item.title}</p>
                <p className="text-xs text-slate-500 leading-relaxed">{item.desc}</p>
              </div>
              <ArrowRight size={16} className="text-slate-300 group-hover:text-slate-500 transition-colors shrink-0 mt-0.5" />
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Recent activity */}
      <motion.div
        className="card"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.35 }}
      >
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-slate-400" />
            <span className="font-bold text-slate-900 text-sm">Recent scans</span>
          </div>
          <Link to="/dashboard/reports" className="text-xs text-blue-600 hover:text-blue-700 font-semibold">
            View all
          </Link>
        </div>

        {loading ? (
          <div className="p-5 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : recent.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <p className="text-sm text-slate-400">No scans yet. Run your first verification above.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {recent.map((entry, i) => (
              <div key={i} className="px-5 py-3.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${entry.pipeline === 'screenshot' ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-600'}`}>
                    {entry.pipeline === 'screenshot' ? <Camera size={13} /> : <MessageSquare size={13} />}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-700 capitalize">{entry.pipeline || 'scan'}</p>
                    <p className="text-xs text-slate-400">{entry.timestamp}</p>
                  </div>
                </div>
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${entry.prediction === 'FAKE' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                  {entry.prediction}
                </span>
              </div>
            ))}
          </div>
        )}
      </motion.div>
      </div>
    </div>
  )
}
