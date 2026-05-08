import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Camera, Upload, X, AlertCircle } from 'lucide-react'
import ResultCard from '../components/ui/ResultCard'
import { detectScreenshot } from '../api/detect'

const BANK_OPTIONS = [
  { label: 'GTBank (GTWorld)', value: 'GTBank' },
  { label: 'Moniepoint MFB',   value: 'Moniepoint' },
  { label: 'Zenith Bank',      value: 'Zenith' },
];

export default function ScreenshotDetection() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [drag, setDrag] = useState(false)
  const [bank, setBank] = useState('GTBank');
  const inputRef = useRef()

  const accept = f => {
    if (!f) return
    const isImage = f.type.startsWith('image/')
    const isPDF = f.type === 'application/pdf'
    if (!isImage && !isPDF) { setError('Please upload a PNG, JPEG image, or a PDF file.'); return }
    if (f.size > 10 * 1024 * 1024) { setError('File must be under 10 MB.'); return }
    setError('')
    setFile(f)
    setResult(null)
    setPreview({ url: URL.createObjectURL(f), type: f.type })
  }

  const handleDrop = e => {
    e.preventDefault()
    setDrag(false)
    accept(e.dataTransfer.files?.[0])
  }

  const clear = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  // Update your handleSubmit to pass the bank
  const handleSubmit = async e => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    try {
      // Send both the file and the selected bank to the API
      const res = await detectScreenshot(file, bank);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.');
    } finally {
      setLoading(false);
    }
  };

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
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">Screenshot Verification</h1>
          <p className="text-sm text-slate-500 mt-0.5">Upload a payment screenshot or PDF to detect fraud</p>
        </div>
      </div>

      <div className="px-8 py-6 space-y-6">
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Upload panel */}
          <motion.div
            className="card p-6"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
          >
            <p className="section-label mb-4">Upload Screenshot</p>

            {error && (
              <div className="mb-4 flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                <AlertCircle size={15} className="shrink-0 mt-0.5" />
                {error}
              </div>
            )}

            {!preview ? (
              <div
                onDragOver={e => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl px-6 py-14 flex flex-col items-center gap-3 cursor-pointer transition-colors ${drag ? 'border-blue-400 bg-blue-50' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'}`}
              >
                <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center">
                  <Upload size={20} className="text-slate-400" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-700">Drop file here or click to browse</p>
                  <p className="text-xs text-slate-400 mt-1">PNG, JPG, JPEG, PDF · max 10 MB</p>
                </div>
                <input ref={inputRef} type="file" accept="image/*,application/pdf" className="hidden" onChange={e => accept(e.target.files?.[0])} />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-50 flex justify-center">
                  {preview.type === 'application/pdf' ? (
                    <embed src={preview.url} type="application/pdf" className="w-full h-72" />
                  ) : (
                    <img src={preview.url} alt="Preview" className="w-full object-contain max-h-72" />
                  )}
                  <button
                    onClick={clear}
                    className="absolute top-2.5 right-2.5 w-7 h-7 bg-white rounded-full border border-slate-200 flex items-center justify-center shadow-sm hover:bg-slate-50 transition-colors z-10"
                  >
                    <X size={13} className="text-slate-600" />
                  </button>
                </div>
                <p className="text-xs text-slate-500 truncate font-medium">{file.name} · {(file.size / 1024).toFixed(0)} KB</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="mt-5">
              <button
                type="submit"
                disabled={!file || loading}
                className="btn-blue w-full py-2.5 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <Camera size={15} />
                    Analyze Screenshot
                  </>
                )}
              </button>
            </form>
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
                  <Camera size={32} className="text-slate-200 mb-3" />
                  <p className="text-sm font-semibold text-slate-400">Result will appear here</p>
                  <p className="text-xs text-slate-300 mt-1 max-w-xs">Upload a screenshot and click Analyze to see the AI verdict</p>
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
          <p className="section-label mb-3">Tips for best results</p>
          <ul className="text-xs text-slate-500 space-y-1.5 leading-relaxed">
            <li className="flex gap-2"><span className="text-blue-400 font-bold">•</span> Use unedited screenshots directly from your banking or mobile money app.</li>
            <li className="flex gap-2"><span className="text-blue-400 font-bold">•</span> Ensure the transaction amount, reference number, and bank logo are visible.</li>
            <li className="flex gap-2"><span className="text-blue-400 font-bold">•</span> Avoid cropping out the header or footer of the alert screen.</li>
          </ul>
        </motion.div>
      </div>
    </div>
  )
}
