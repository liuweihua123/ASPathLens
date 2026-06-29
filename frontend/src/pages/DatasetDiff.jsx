import { useEffect, useState } from 'react'
import { getDatasetVersions, getDatasetDiff } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'

function StatCard({ label, value }) {
  return <div className="dk-card p-4"><p className="text-xs text-slate-500">{label}</p><p className="text-2xl font-bold text-white">{value ?? '—'}</p></div>
}

export default function DatasetDiff() {
  const { tr, lang } = useLang()
  const [versions, setVersions] = useState({ as_relationship: [], as2org: [] })
  const [dataset, setDataset] = useState('as_relationship')
  const [oldV, setOldV] = useState('')
  const [newV, setNewV] = useState('')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getDatasetVersions().then(v => {
      setVersions(v)
      const f = v.as_relationship || []
      if (f.length >= 2) { setOldV(f[f.length - 2].version); setNewV(f[f.length - 1].version) }
    }).catch(() => {})
  }, [])

  async function onDiff() {
    if (!oldV || !newV) { setError(lang === 'zh' ? '请选择两个版本' : 'Select both versions'); return }
    setLoading(true); setError('')
    try { setData(await getDatasetDiff(dataset, oldV, newV)) }
    catch (e) { setError(e.response?.data?.detail || e.message) } finally { setLoading(false) }
  }

  const files = versions[dataset] || []
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('ddiff.title')}</h1>
      <p className="text-sm text-slate-400">{tr('ddiff.desc')}</p>
      <div className="flex flex-wrap items-end gap-4">
        <div><label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('ddiff.dataset')}</label>
          <select className="dk-input mt-1 block" value={dataset} onChange={e => setDataset(e.target.value)}>
            <option value="as_relationship">{tr('ds.asrel')}</option><option value="as2org">{tr('ds.as2org')}</option></select></div>
        <div><label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('ddiff.oldVersion')}</label>
          <select className="dk-input mt-1 block" value={oldV} onChange={e => setOldV(e.target.value)}>
            <option value="">—</option>{files.map(f => <option key={f.version} value={f.version}>{f.version}</option>)}</select></div>
        <div><label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('ddiff.newVersion')}</label>
          <select className="dk-input mt-1 block" value={newV} onChange={e => setNewV(e.target.value)}>
            <option value="">—</option>{files.map(f => <option key={f.version} value={f.version}>{f.version}</option>)}</select></div>
        <button onClick={onDiff} disabled={loading} className="dk-btn-primary disabled:opacity-50">
          {loading ? tr('diff.comparing') : tr('diff.compare')}</button>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {data && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {dataset === 'as_relationship' ? (<>
              <StatCard label={tr('ddiff.oldEdges')} value={data.old_edge_count} />
              <StatCard label={tr('ddiff.newEdges')} value={data.new_edge_count} />
              <StatCard label={tr('ddiff.added')} value={data.added_edges} />
              <StatCard label={tr('ddiff.removed')} value={data.removed_edges} />
              <StatCard label={tr('ddiff.relChanges')} value={data.changed_relationships} />
            </>) : (<>
              <StatCard label={lang === 'zh' ? '旧 ASN 数' : 'Old ASNs'} value={data.old_asn_count} />
              <StatCard label={lang === 'zh' ? '新 ASN 数' : 'New ASNs'} value={data.new_asn_count} />
              <StatCard label={lang === 'zh' ? '新增 ASN' : 'New ASNs added'} value={data.new_asns} />
              <StatCard label={lang === 'zh' ? '移除 ASN' : 'Removed ASNs'} value={data.removed_asns} />
            </>)}
          </div>
          {data.top_changed_asns?.length > 0 && (
            <div className="dk-card overflow-hidden">
              <h3 className="border-b border-sky-500/10 bg-[#0b1121] px-4 py-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('ddiff.topChanged')}</h3>
              <table className="w-full text-sm"><thead><tr><th className="dk-th">ASN</th><th className="dk-th">{lang === 'zh' ? '变化边数' : 'Changed edges'}</th></tr></thead>
                <tbody>{data.top_changed_asns.slice(0, 15).map(a => (
                  <tr key={a.asn} className="hover:bg-sky-500/5"><td className="dk-td font-mono text-sky-300">AS{a.asn}</td><td className="dk-td font-bold text-white">{a.changed_edges}</td></tr>
                ))}</tbody></table>
            </div>
          )}
          {data.type_changes && Object.keys(data.type_changes).length > 0 && (
            <div className="dk-card p-4">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('ddiff.typeChanges')}</h3>
              <ul className="mt-2 space-y-1 text-sm">{Object.entries(data.type_changes).map(([k, v]) => (
                <li key={k} className="text-slate-400"><code className="text-rose-400/80">{k}</code> — {v}</li>
              ))}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}