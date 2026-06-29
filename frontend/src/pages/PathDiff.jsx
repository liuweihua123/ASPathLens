import { useState } from 'react'
import { diffPaths } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'
import PathGraph from '../components/PathGraph.jsx'
import RiskCard from '../components/RiskCard.jsx'

export default function PathDiff() {
  const { tr, interp } = useLang()
  const [before, setBefore] = useState('3356 4134 4837 9808')
  const [after, setAfter] = useState('3356 1299 4837 9808')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function onDiff() {
    setLoading(true); setError('')
    try { setData(await diffPaths(before, after)) }
    catch (e) { setError(e.response?.data?.detail || e.message) }
    finally { setLoading(false) }
  }

  const changedAsns = new Set()
  data?.diff?.changed_positions?.forEach((p) => { if (p.before) changedAsns.add(p.before); if (p.after) changedAsns.add(p.after) })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('diff.title')}</h1>
      <p className="text-sm text-slate-400">{tr('diff.desc')}</p>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('diff.before')}</label>
          <textarea className="dk-input mt-1 w-full font-mono" rows={2} value={before} onChange={(e) => setBefore(e.target.value)} />
        </div>
        <div>
          <label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('diff.after')}</label>
          <textarea className="dk-input mt-1 w-full font-mono" rows={2} value={after} onChange={(e) => setAfter(e.target.value)} />
        </div>
      </div>
      <button onClick={onDiff} disabled={loading} className="dk-btn-primary disabled:opacity-50">
        {loading ? tr('diff.comparing') : tr('diff.compare')}
      </button>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {data && (
        <>
          <div className="dk-card p-4">
            <p className="text-sm text-slate-300">
              {tr('diff.riskDelta')}:{' '}
              <strong className={data.diff.risk_delta > 0 ? 'text-rose-400' : data.diff.risk_delta < 0 ? 'text-emerald-400' : 'text-slate-300'}>
                {data.diff.risk_delta > 0 ? '+' : ''}{data.diff.risk_delta}
              </strong>{' '}
              ({data.before.level} → {data.after.level})
            </p>
            <p className="mt-2 text-sm text-slate-400">{interp(data.diff)}</p>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('diff.before')}</h3>
              <PathGraph path={data.before_graph.path} edges={data.before_graph.edges} nodes={data.before_graph.as_nodes} highlightAsns={changedAsns} />
              <p className="mt-2 font-mono text-xs text-slate-500">{data.before.relationship_sequence?.join(' → ')}</p>
              <RiskCard risk={{ score: data.before.risk_score, level: data.before.level, evidence: [] }} />
            </div>
            <div>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('diff.after')}</h3>
              <PathGraph path={data.after_graph.path} edges={data.after_graph.edges} nodes={data.after_graph.as_nodes} highlightAsns={changedAsns} />
              <p className="mt-2 font-mono text-xs text-slate-500">{data.after.relationship_sequence?.join(' → ')}</p>
              <RiskCard risk={{ score: data.after.risk_score, level: data.after.level, evidence: [] }} />
            </div>
          </div>
          <div className="dk-card overflow-hidden">
            <h3 className="border-b border-sky-500/10 bg-[#0b1121] px-4 py-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('diff.changes')}</h3>
            <table className="w-full text-sm">
              <tbody>
                <tr className="hover:bg-sky-500/5"><td className="dk-td font-medium">{tr('diff.addedAsns')}</td><td className="dk-td font-mono">{data.diff.added_asns?.join(', ') || '—'}</td></tr>
                <tr className="hover:bg-sky-500/5"><td className="dk-td font-medium">{tr('diff.removedAsns')}</td><td className="dk-td font-mono">{data.diff.removed_asns?.join(', ') || '—'}</td></tr>
              </tbody>
            </table>
          </div>
          <p className="text-xs text-slate-600">{data.disclaimer}</p>
        </>
      )}
    </div>
  )
}