import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { CheckCircle, Zap, BarChart2, Camera, MessageSquare, ArrowRight, Lock } from 'lucide-react'
import Logo from '../components/ui/Logo'

const FEATURES = [
  { icon: Camera,        title: 'Screenshot Analysis',  desc: 'Upload a payment screenshot and get an instant AI verdict with confidence score and explanation.' },
  { icon: MessageSquare, title: 'SMS Verification',     desc: 'Paste the exact debit/credit SMS text and detect spoofed bank messages in real time.' },
  { icon: BarChart2,     title: 'Analytics Dashboard',  desc: 'Track detection history, risk distribution, and model performance across your business.' },
  { icon: Lock,          title: 'Explainable AI',       desc: 'Every result comes with a human-readable explanation — know WHY a transfer was flagged.' },
]

const STATS = [
  { value: '98.4%',  label: 'Detection Accuracy' },
  { value: '<2s',    label: 'Analysis Time'       },
  { value: '10k+',   label: 'Scans Performed'     },
  { value: 'SHAP',   label: 'Explainability'      },
]

const fade = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-100">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Logo size={32} />
            <span className="font-extrabold text-slate-900 text-base tracking-tight">TransferNet</span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-500">
            <a href="#features" className="hover:text-slate-900 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">How it works</a>
            <a href="#stats" className="hover:text-slate-900 transition-colors">Results</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors">
              Sign in
            </Link>
            <Link to="/signup" className="btn-primary text-sm px-4 py-2">
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-24 text-center">
        <motion.div
          variants={fade}
          initial="hidden"
          animate="show"
          transition={{ duration: 0.5 }}
        >
          <span className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 border border-blue-100 text-xs font-bold px-3 py-1 rounded-full mb-6 tracking-wide uppercase">
            <Zap size={11} />
            Final Year Research Project — Explainable AI
          </span>
          <h1 className="text-5xl md:text-6xl font-extrabold text-slate-900 leading-tight tracking-tight mb-5">
            Detect Fake Mobile Money<br />
            <span className="text-blue-600">Transfers Instantly</span>
          </h1>
          <p className="text-lg text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            An AI-powered fraud detection tool built for SMEs. Upload a transfer screenshot or paste an SMS alert to get a real-time verdict with a full explanation.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link to="/signup" className="btn-primary flex items-center gap-2 px-6 py-3 text-sm">
              Start detecting fraud <ArrowRight size={15} />
            </Link>
            <Link to="/login" className="btn-outline flex items-center gap-2 px-6 py-3 text-sm">
              Sign in to dashboard
            </Link>
          </div>
        </motion.div>

        {/* Hero visual */}
        <motion.div
          className="mt-16 rounded-2xl border border-slate-200 bg-slate-50 shadow-card-lg overflow-hidden max-w-3xl mx-auto"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <div className="bg-white border-b border-slate-100 px-5 py-3 flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
            </div>
            <span className="text-xs text-slate-400 font-medium ml-2">TransferNet — Screenshot Analysis</span>
          </div>
          <div className="p-8 flex flex-col items-center gap-4">
            <div className="w-full max-w-sm rounded-xl border-2 border-dashed border-slate-200 bg-white px-6 py-10 flex flex-col items-center gap-3 text-center">
              <Camera size={28} className="text-slate-300" />
              <p className="text-sm text-slate-400 font-medium">Drop a payment screenshot here</p>
              <span className="text-xs text-slate-300">PNG, JPG, JPEG · max 10 MB</span>
            </div>
            <div className="w-full max-w-sm rounded-xl border-2 border-green-200 bg-green-50 px-5 py-4 flex items-center gap-3">
              <CheckCircle size={20} className="text-green-500 shrink-0" />
              <div>
                <p className="text-sm font-bold text-slate-900">Genuine Transaction</p>
                <p className="text-xs text-slate-500 mt-0.5">Confidence 97.2% · Risk: SAFE</p>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Stats */}
      <section id="stats" className="bg-slate-900 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {STATS.map((s, i) => (
              <motion.div
                key={s.label}
                className="text-center"
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.4 }}
              >
                <div className="text-3xl font-extrabold text-white mb-1">{s.value}</div>
                <div className="text-sm text-white/50 font-medium">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-14">
          <p className="section-label mb-3">Features</p>
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Built for SME fraud prevention</h2>
          <p className="text-slate-500 mt-3 max-w-xl mx-auto text-sm leading-relaxed">
            Combines computer vision, NLP, and explainable ML to verify mobile money transfers in under 2 seconds.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              className="card p-6 flex gap-4"
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.07, duration: 0.4 }}
            >
              <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                <f.icon size={18} className="text-blue-600" strokeWidth={2} />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm mb-1">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="bg-slate-50 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <p className="section-label mb-3">Process</p>
            <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">Three steps to a verdict</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Upload evidence',   desc: 'Paste your SMS text or upload a screenshot of the payment alert.' },
              { step: '02', title: 'AI analyzes',       desc: 'Our XGBoost + OCR pipeline extracts features and runs them through the fraud model.' },
              { step: '03', title: 'Get your verdict',  desc: 'Receive a FAKE / GENUINE prediction with confidence score and SHAP-based explanation.' },
            ].map((item, i) => (
              <motion.div
                key={item.step}
                className="text-center"
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
              >
                <div className="w-12 h-12 rounded-full bg-slate-900 text-white font-extrabold text-sm flex items-center justify-center mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-bold text-slate-900 mb-2">{item.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4 }}
        >
          <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-4">
            Ready to protect your business?
          </h2>
          <p className="text-slate-500 mb-8 text-sm max-w-md mx-auto">
            Join SMEs using TransferNet to verify payments before releasing goods or services.
          </p>
          <Link to="/signup" className="btn-primary inline-flex items-center gap-2 px-7 py-3">
            Create free account <ArrowRight size={15} />
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Logo size={24} />
            <span className="text-sm font-bold text-slate-700">TransferNet</span>
          </div>
          <p className="text-xs text-slate-400">Final Year Project — Explainable AI for SME Fraud Detection</p>
          <div className="flex items-center gap-5 text-xs text-slate-400">
            <Link to="/login" className="hover:text-slate-600 transition-colors">Sign in</Link>
            <Link to="/signup" className="hover:text-slate-600 transition-colors">Sign up</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
