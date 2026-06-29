import { useState } from 'react'
import { searchPattern } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'

const PATTERNS = [
  { label: 'p2p -> c2p', en: 'Route leak: peer to uphill', zh: 'Route leak: peer→上坡' },
  { label: 'p2c -> c2p', en: 'Valley violation: down then up', zh: 'Valley 违规: 下坡→上坡' },
  { label: 'p2c -> p2p', en: 'Down then peer', zh: '下坡→peer' },
]

export default function PatternSearch() {
  const { tr, lang } = useLang()
  const [pattern, setPattern] = useState('p2p -> c2p')
  const [paths, setPaths] = useState('3356 4134 4837 9808\n174 2914 3356 4134\n3356 1299 4837 9808')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function onSearch() {
    setLoading(true); setError('')
    try { setData(await searchPattern(pattern, paths.split('\n').map(l => l.trim()).filter(Boolean))) }
    catch (e) { setError(e.response?.data?.detail || e.message) } finally { setLoading(false) }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('pattern.title')}</h1>
      <p className="text-sm text-slate-400">{tr('pattern.desc')}</p>
      <div className="flex flex-wrap gap-2">
        {PATTERNS.map(ex => (
          <button key={ex.label} onClick={() => setPattern(ex.label)} title={lang === 'zh' ? ex.zh : ex.en}
            className={`rounded-lg px-3 py-1.5 font-mono text-xs transition ${pattern === ex.label ? 'bg-sky-500 text-white' : 'bg-[#0b1121] text-slate-400 hover:text-sky-300'}`}>
            {ex.label}
          </button>
        ))}
      </div>
      <div><label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('pattern.pattern')}</label>
        <input className="dk-input mt-1 w-full font-mono" value={pattern} onChange={e => setPattern(e.target.value)} /></div>
      <div><label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('pattern.paths')}</label>
        <textarea className="dk-input mt-1 w-full font-mono text-xs" rows={5} value={paths} onChange={e => setPaths(e.target.value)} /></div>
      <button onClick={onSearch} disabled={loading} className="dk-btn-primary disabled:opacity-50">
        {loading ? tr('pattern.searching') : tr('pattern.search')}</button>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {data && (
        <div className="space-y-4">
          <div className="dk-card p-4">
            <p className="text-sm text-slate-300">
              <code className="text-sky-300">{data.pattern}</code> {tr('pattern.found')} <strong className="text-white">{data.matched_paths}</strong> {tr('pattern.pathsLabel')}</p>
          </div>
          {data.top_middle_asns?.length > 0 && (
            <div className="dk-card overflow-hidden">
              <h3 className="border-b border-sky-500/10 bg-[#0b1121] px-4 py-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('pattern.topMiddle')}</h3>
              <table className="w-full text-sm"><thead><tr><th className="dk-th">ASN</th><th className="dk-th">Org</th><th className="dk-th">Count</th></tr></thead>
                <tbody>{data.top_middle_asns.map(a => (
                  <tr key={a.asn} className="hover:bg-sky-500/5"><td className="dk-td font-mono text-sky-300">AS{a.asn}</td><td className="dk-td">{a.org_name || '—'}</td><td className="dk-td font-bold text-white">{a.count}</td></tr>
                ))}</tbody></table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}