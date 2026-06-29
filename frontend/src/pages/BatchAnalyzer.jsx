import { useRef, useState } from 'react'
import { batchAnalyzeFile, batchAnalyzeJson } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'

const SAMPLE_CSV = `path_id,as_path\n1,"3356 4134 4837 9808"\n2,"174 2914 3356 4134"\n`

export default function BatchAnalyzer() {
  const { tr, lang } = useLang()
  const fileRef = useRef(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [paste, setPaste] = useState(SAMPLE_CSV)

  async function onUpload() {
    const f = fileRef.current?.files?.[0]
    if (!f) { setError(lang === 'zh' ? '请选择文件' : 'Choose a file'); return }
    setLoading(true); setError('')
    try { setResult(await batchAnalyzeFile(f)) } catch (e) { setError(e.response?.data?.detail || e.message) } finally { setLoading(false) }
  }
  async function onPasteCsv() {
    setLoading(true); setError('')
    try { setResult(await batchAnalyzeFile(new File([new Blob([paste], { type: 'text/csv' })], 'paste.csv'))) }
    catch (e) { setError(e.response?.data?.detail || e.message) } finally { setLoading(false) }
  }
  async function onQuickJson() {
    setLoading(true); setError('')
    try { setResult(await batchAnalyzeJson(['3356 4134 4837 9808', '174 2914 3356 4134'])) }
    catch (e) { setError(e.response?.data?.detail || e.message) } finally { setLoading(false) }
  }
  function download(ext) {
    if (!result?.export_rows?.length) return
    const keys = Object.keys(result.export_rows[0])
    const content = ext === 'json'
      ? JSON.stringify(result.export_rows, null, 2)
      : [keys.join(','), ...result.export_rows.map(r => keys.map(k => `"${String(r[k] ?? '').replace(/"/g, '""')}"`).join(','))].join('\n')
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([content])); a.download = `aspathlens-batch.${ext}`; a.click()
  }

  const rows = result?.export_rows || []
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('batch.title')}</h1>
      <p className="text-sm text-slate-400">{tr('batch.desc')}</p>
      <div className="flex flex-wrap gap-3">
        <input ref={fileRef} type="file" accept=".csv,.txt,.json" className="text-sm text-slate-400 file:mr-3 file:rounded file:border-0 file:bg-sky-500/10 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-sky-400" />
        <button onClick={onUpload} disabled={loading} className="dk-btn-primary disabled:opacity-50">{tr('batch.analyzeFile')}</button>
        <button onClick={onQuickJson} disabled={loading} className="dk-btn-ghost">{tr('batch.demo')}</button>
      </div>
      <div>
        <label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('batch.pasteCsv')}</label>
        <textarea className="dk-input mt-1 w-full font-mono text-xs" rows={4} value={paste} onChange={(e) => setPaste(e.target.value)} />
        <button onClick={onPasteCsv} disabled={loading} className="dk-btn-ghost mt-2">{tr('batch.analyzePaste')}</button>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {result && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[[tr('batch.total'), result.total_paths, 'text-sky-400'], [tr('batch.valleyFree'), result.valley_free_valid_count, 'text-emerald-400'],
              [tr('batch.suspicious'), result.suspicious_count, 'text-amber-400'], [tr('batch.unknownHeavy'), result.unknown_heavy_count, 'text-slate-400']
            ].map(([label, val, c]) => (
              <div key={label} className="dk-card p-4"><p className="text-xs text-slate-500">{label}</p><p className={`text-2xl font-bold ${c}`}>{val}</p></div>
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="dk-card p-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('batch.topPatterns')}</h3>
              <ul className="mt-2 space-y-1 text-sm">{result.top_violation_patterns?.length
                ? result.top_violation_patterns.map(p => <li key={p.pattern}><span className="font-mono text-rose-400/80">{p.pattern}</span><span className="text-slate-500"> — {p.count}</span></li>)
                : <li className="text-slate-600">{lang === 'zh' ? '无' : 'None'}</li>}</ul>
            </div>
            <div className="dk-card p-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('batch.topSuspicious')}</h3>
              <ul className="mt-2 space-y-1 text-sm">{result.top_suspicious_asns?.length
                ? result.top_suspicious_asns.map(a => <li key={a.asn}><span className="font-mono text-amber-400">AS{a.asn}</span>{a.org_name ? <span className="text-slate-500"> ({a.org_name})</span> : null}<span className="text-slate-500"> — {a.count}</span></li>)
                : <li className="text-slate-600">{lang === 'zh' ? '无' : 'None'}</li>}</ul>
            </div>
          </div>
          {rows.length > 0 && (
            <div className="dk-card overflow-hidden">
              <h3 className="border-b border-sky-500/10 bg-[#0b1121] px-4 py-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('batch.perPath')} ({rows.length})</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs"><thead><tr>{['ID','Path','Sequence','VF','Violation','Leaker','Risk','Level','Cov'].map(h =>
                  <th key={h} className="dk-th">{h}</th>)}</tr></thead><tbody>{rows.map(r => (
                  <tr key={r.path_id} className="hover:bg-sky-500/5">
                    <td className="dk-td">{r.path_id}</td>
                    <td className="dk-td max-w-[14rem] truncate font-mono">{r.normalized_path}</td>
                    <td className="dk-td max-w-[10rem] truncate font-mono text-[11px] text-sky-300/70">{r.relationship_sequence}</td>
                    <td className="dk-td">{r.is_valley_free === true ? <span className="text-emerald-400">✓</span> : r.is_valley_free === false ? <span className="text-rose-400">✗</span> : '?'}</td>
                    <td className="dk-td max-w-[10rem] truncate font-mono text-rose-400/70">{r.violation_pattern || '—'}</td>
                    <td className="dk-td font-mono text-amber-400">{r.candidate_leaker_asn || '—'}</td>
                    <td className="dk-td font-bold text-white">{r.risk_score}</td>
                    <td className="dk-td"><span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${r.risk_level === 'suspicious' || r.risk_level === 'highly suspicious' ? 'bg-rose-500/15 text-rose-400' : r.risk_level === 'uncertain' ? 'bg-amber-500/15 text-amber-400' : 'bg-emerald-500/15 text-emerald-400'}`}>{r.risk_level}</span></td>
                    <td className="dk-td text-slate-500">{r.known_edge_ratio}</td>
                  </tr>))}</tbody></table>
              </div>
            </div>
          )}
          <div className="flex gap-2">
            <button onClick={() => download('csv')} className="dk-btn-ghost">{tr('batch.downloadCsv')}</button>
            <button onClick={() => download('json')} className="dk-btn-ghost">{tr('batch.downloadJson')}</button>
          </div>
          <p className="text-xs text-slate-600">batch_result_id: {result.batch_result_id}</p>
        </>
      )}
    </div>
  )
}