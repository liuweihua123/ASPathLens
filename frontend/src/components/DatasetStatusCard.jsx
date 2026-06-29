import { Link } from 'react-router-dom'
import { useLang } from '../i18n/context.jsx'

function Stat({ label, value }) {
  return (
    <div className="flex justify-between border-t border-sky-500/10 py-1.5 text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-200">{value ?? '—'}</span>
    </div>
  )
}

export default function DatasetStatusCard({ data }) {
  const { tr, lang } = useLang()
  const rel = data.as_relationship || {}
  const org = data.as2org || {}
  const api = data.asrank_api || {}

  const badge = (s) => {
    const cls = s === 'fresh' ? 'dk-badge-green' : s === 'missing' ? 'dk-badge-amber' : s === 'api_unreachable' ? 'dk-badge-rose' : 'dk-badge-sky'
    return <span className={cls}>{s}</span>
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="dk-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold text-white">{tr('ds.asrel')}</h3>
            {badge(rel.status)}
          </div>
          <Stat label={tr('ds.file')} value={rel.file_name || '—'} />
          <Stat label={tr('ds.date')} value={rel.dataset_date} />
          <Stat label={tr('ds.edges')} value={rel.loaded_edge_count} />
          <Stat label={tr('ds.uniqueAsns')} value={rel.unique_asn_count} />
          <Stat label={tr('ds.p2c')} value={rel.p2c_count} />
          <Stat label={tr('ds.p2p')} value={rel.p2p_count} />
          <Stat label={tr('ds.size')} value={rel.size_bytes ? `${(rel.size_bytes / 1e6).toFixed(1)} MB` : null} />
          {!rel.loaded_edge_count && <p className="mt-3 text-xs text-amber-400/80">{tr('ds.downloadHint')}</p>}
        </div>
        <div className="dk-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold text-white">{tr('ds.as2org')}</h3>
            {badge(org.status)}
          </div>
          <Stat label={tr('ds.file')} value={org.file_name || '—'} />
          <Stat label={tr('ds.date')} value={org.dataset_date} />
          <Stat label={tr('ds.uniqueAsns')} value={org.loaded_asn_count} />
          <Stat label={tr('ds.orgs')} value={org.org_count} />
          <Stat label={tr('ds.countries')} value={org.country_count} />
          <Stat label={tr('ds.size')} value={org.size_bytes ? `${(org.size_bytes / 1e6).toFixed(1)} MB` : null} />
          {!org.loaded_asn_count && <p className="mt-3 text-xs text-amber-400/80">{tr('ds.downloadHint')}</p>}
        </div>
        <div className="dk-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold text-white">{tr('ds.asrank')}</h3>
            {badge(api.status)}
          </div>
          <p className="text-sm text-slate-400">{api.message}</p>
          <p className="mt-2 text-xs text-slate-500">{tr('ds.enhancementOnly')}</p>
          {api.status === 'api_unreachable' && <p className="mt-2 text-xs text-amber-400/80">{tr('asn.asrankUnavailable')}</p>}
        </div>
      </div>
      <div className="dk-card p-5">
        <h3 className="font-semibold text-white">{tr('ds.ready')}</h3>
        <div className="mt-3 flex flex-wrap gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className={`inline-block h-2.5 w-2.5 rounded-full ${rel.loaded_edge_count && org.loaded_asn_count ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            {tr('ds.pathReady')} {rel.loaded_edge_count && org.loaded_asn_count ? tr('ds.readyLabel') : tr('ds.needsData')}
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className={`inline-block h-2.5 w-2.5 rounded-full ${api.status === 'fresh' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
            ASN Explorer {api.status === 'fresh' ? tr('ds.online') : tr('ds.offline')}
          </div>
        </div>
      </div>
      <Link to="/analyzer" className="block text-sm text-sky-400 hover:text-sky-300">
        {lang === 'zh' ? '分析路径 →' : 'Analyze a path →'}
      </Link>
    </div>
  )
}