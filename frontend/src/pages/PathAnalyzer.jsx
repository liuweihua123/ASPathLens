import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { analyzePath, normalizePath } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'
import PathGraph from '../components/PathGraph.jsx'
import RiskCard from '../components/RiskCard.jsx'
import ValleyFreeCard from '../components/ValleyFreeCard.jsx'
import RelationshipTable from '../components/RelationshipTable.jsx'

export default function PathAnalyzer() {
  const location = useLocation()
  const navigate = useNavigate()
  const { lang, tr, explain } = useLang()
  const [input, setInput] = useState('3356 4134 4837 9808')
  const [norm, setNorm] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { if (location.state?.path) setInput(location.state.path) }, [location.state])

  async function onNormalize() {
    setError('')
    try { setNorm(await normalizePath(input)) } catch (e) { setError(e.message) }
  }

  async function onAnalyze() {
    setLoading(true); setError('')
    try {
      const data = await analyzePath(input, true)
      setResult(data)
      setNorm({ raw_path: data.raw_path, normalized_path: data.normalized_path, warnings: data.normalization_warnings })
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('analyzer.title')}</h1>
      <textarea className="dk-input w-full font-mono" rows={3} value={input}
        onChange={(e) => setInput(e.target.value)} placeholder="3356 4134 4837 9808" />
      <div className="flex gap-2">
        <button onClick={onNormalize} className="dk-btn-outline">{tr('analyzer.normalize')}</button>
        <button onClick={onAnalyze} disabled={loading} className="dk-btn-primary disabled:opacity-50">
          {loading ? tr('analyzer.analyzing') : tr('analyzer.analyze')}
        </button>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {norm && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="dk-card p-4">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('analyzer.rawPath')}</h3>
            <p className="mt-1 font-mono text-sm text-slate-300">{norm.raw_path?.join(' → ')}</p>
          </div>
          <div className="dk-card p-4">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('analyzer.normPath')}</h3>
            <p className="mt-1 font-mono text-sm text-slate-300">{norm.normalized_path?.join(' → ')}</p>
            {norm.warnings?.length > 0 && (
              <ul className="mt-2 list-inside list-disc text-xs text-amber-400/80">
                {norm.warnings.map((w) => <li key={w}>{w}</li>)}
              </ul>
            )}
          </div>
        </div>
      )}
      {result && (
        <>
          <PathGraph path={result.normalized_path} edges={result.edges} nodes={result.as_nodes} />
          <RelationshipTable edges={result.edges} sequence={result.relationship_sequence} />
          <div className="grid gap-4 md:grid-cols-2">
            <ValleyFreeCard vf={result.valley_free} />
            <RiskCard risk={result.risk_score} coverage={result.relationship_coverage} />
          </div>
          {result.route_leak_candidate?.is_candidate && (
            <div className="dk-card border-amber-500/30 p-4">
              <h3 className="text-sm font-semibold text-amber-300">{tr('analyzer.leakTitle')}</h3>
              <p className="mt-1 font-mono text-sm text-slate-300">
                AS{result.route_leak_candidate.candidate_asn} · {result.route_leak_candidate.pattern} · {result.route_leak_candidate.confidence}
              </p>
              <p className="mt-2 text-sm text-slate-400">{explain(result.route_leak_candidate)}</p>
            </div>
          )}
          <div className="dk-card p-4">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('analyzer.orgPath')}</h3>
            <p className="mt-1 font-mono text-xs text-slate-400">{result.org_path?.join(' → ')}</p>
            <p className="mt-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('analyzer.compressedOrg')}</p>
            <p className="mt-1 font-mono text-xs text-slate-400">{result.compressed_org_path?.join(' → ')}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigate('/kg', { state: { mode: 'path', input } })} className="dk-btn-outline">
              {lang === 'zh' ? '查看知识图谱' : 'View as Knowledge Graph'} →
            </button>
          </div>
          <p className="text-xs text-slate-600">{tr('risk.disclaimer')}</p>
        </>
      )}
    </div>
  )
}