import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { BarChart2, Download, Camera, MessageSquare, RefreshCw, ShieldAlert, ShieldCheck, Activity, TrendingUp } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts'
import StatCard from '../components/ui/StatCard'
import Badge from '../components/ui/Badge'
import { getStats, getLog, exportCSV } from '../api/reports'

const PAGE_SIZE = 10

export default function Reports() {
  const [stats, setStats]     = useState(null)
  const [entries, setEntries] = useState([])
  const [total, setTotal]     = useState(0)
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const load = async (p = 1, showRefresh = false) => {
    if (showRefresh) setRefreshing(true)
    else if (p === 1) setLoading(true)
    try {
      const [s, l] = await Promise.all([getStats(), getLog(p, PAGE_SIZE)])
      setStats(s.data)
      setEntries(l.data.entries || [])
      setTotal(l.data.total || 0)
      setPage(p)
    } catch {}
    finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleExport = async () => {
    try {
      const res = await exportCSV()
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = 'detection_log.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch {}
  }

  const statCards = stats
    ? [
        { icon: Activity,    value: stats.total,            label: 'Total Scans', accent: 'blue'  },
        { icon: ShieldAlert, value: stats.fake,             label: 'Fake',        accent: 'red'   },
        { icon: ShieldCheck, value: stats.genuine,          label: 'Genuine',     accent: 'green' },
        { icon: TrendingUp,  value: `${stats.accuracy}%`,   label: 'Accuracy',    accent: 'amber' },
      ]
    : []

  const pieData = stats
    ? [
        { name: 'Fake',    value: stats.fake,    fill: '#ef4444' },
        { name: 'Genuine', value: stats.genuine, fill: '#22c55e' },
      ]
    : []

  const barData = stats?.daily_counts || []
  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="flex flex-col flex-1">
      <div className="page-header">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Reports</h1>
          <p className="text-sm text-slate-500 mt-0.5">Detection history and model analytics</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => load(page, true)}
            disabled={refreshing}
            className="btn-outline flex items-center gap-1.5 text-sm px-3 py-2 disabled:opacity-50"
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button onClick={handleExport} className="btn-primary flex items-center gap-1.5 text-sm px-3 py-2">
            <Download size={13} />
            Export CSV
          </button>
        </div>
      </div>

      <div className="px-8 py-6 space-y-6">
        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {loading
            ? [...Array(4)].map((_, i) => <div key={i} className="card p-5 animate-pulse h-28 bg-slate-100" />)
            : statCards.map((c, i) => <StatCard key={c.label} {...c} index={i} />)
          }
        </div>

        {/* Charts */}
        {!loading && stats && (
          <div className="grid md:grid-cols-2 gap-6">
            <motion.div
              className="card p-5"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.35 }}
            >
              <p className="section-label mb-4">Daily scan volume</p>
              {barData.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={barData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: 'none' }} cursor={{ fill: '#f8fafc' }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {barData.map((_, i) => <Cell key={i} fill="#3b82f6" />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-44 flex items-center justify-center">
                  <p className="text-xs text-slate-400">No data yet</p>
                </div>
              )}
            </motion.div>

            <motion.div
              className="card p-5"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.22, duration: 0.35 }}
            >
              <p className="section-label mb-4">Prediction breakdown</p>
              {(pieData[0]?.value || pieData[1]?.value) ? (
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3} dataKey="value">
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Pie>
                    <Legend iconType="circle" iconSize={8} formatter={v => <span style={{ fontSize: 11, color: '#64748b' }}>{v}</span>} />
                    <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-44 flex items-center justify-center">
                  <p className="text-xs text-slate-400">No data yet</p>
                </div>
              )}
            </motion.div>
          </div>
        )}

        {/* Log table */}
        <motion.div
          className="card overflow-hidden"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.35 }}
        >
          <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <BarChart2 size={14} className="text-slate-400" />
            <span className="font-bold text-slate-900 text-sm">Detection log</span>
            {!loading && <span className="text-xs text-slate-400 font-medium">({total} total)</span>}
          </div>

          {loading ? (
            <div className="p-5 space-y-3">
              {[...Array(5)].map((_, i) => <div key={i} className="h-10 bg-slate-100 rounded-lg animate-pulse" />)}
            </div>
          ) : entries.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <BarChart2 size={28} className="text-slate-200 mx-auto mb-3" />
              <p className="text-sm text-slate-400 font-medium">No detection history yet</p>
              <p className="text-xs text-slate-300 mt-1">Run your first scan to see logs here.</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50">
                      {['Timestamp', 'Pipeline', 'Prediction', 'Confidence', 'Risk', 'Explanation'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {entries.map((e, i) => (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 text-slate-500 whitespace-nowrap font-mono text-xs">{e.timestamp}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5 text-slate-600 capitalize">
                            {e.pipeline === 'screenshot' ? <Camera size={12} /> : <MessageSquare size={12} />}
                            {e.pipeline || '—'}
                          </div>
                        </td>
                        <td className="px-4 py-3"><Badge label={e.prediction} /></td>
                        <td className="px-4 py-3 text-slate-600 font-semibold">{e.confidence != null ? `${e.confidence}%` : '—'}</td>
                        <td className="px-4 py-3">{e.risk_level ? <Badge label={e.risk_level} variant={e.risk_level} /> : '—'}</td>
                        <td className="px-4 py-3 text-slate-500 max-w-xs truncate">{e.explanation || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="px-5 py-4 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Page {page} of {totalPages}</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => load(page - 1)}
                      disabled={page <= 1}
                      className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => load(page + 1)}
                      disabled={page >= totalPages}
                      className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </motion.div>
      </div>
    </div>
  )
}
