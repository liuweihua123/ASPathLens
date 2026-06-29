import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAsnProfile } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'

const roleZh = {
  'large transit provider': '大型 Transit 提供商',
  'large ISP / content-heavy network': '大型 ISP / 内容网络',
  'stub / enterprise / access network': 'Stub / 企业 / 接入网络',
  'large organization / telecom group': '大型组织 / 电信集团',
  'unknown': '未知',
}

export default function ASNExplorer() {
  const { tr, lang } = useLang()
  const navigate = useNavigate()
  const [asn, setAsn] = useState('4134')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function onSearch() {
    setLoading(true); setError('')
    try { setData(await getAsnProfile(asn)) }
    catch (e) { setError(e.response?.data?.detail || e.message) }
    finally { setLoading(false) }
  }

  const local = data?.local || {}
  const asrank = data?.asrank || {}

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('asn.title')}</h1>
      <div className="flex gap-2">
        <input className="dk-input w-48 font-mono" value={asn} onChange={(e) => setAsn(e.target.value)} placeholder="4134" />
        <button onClick={onSearch} disabled={loading} className="dk-btn-primary disabled:opacity-50">
          {loading ? tr('asn.loading') : tr('asn.search')}
        </button>
      </div>
      {error && <p className="text-sm text-rose-400">{error}</p>}
      {data && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="dk-card p-5">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('asn.orgTitle')}</h3>
            <dl className="mt-3 space-y-1 text-sm">
              {[
                [tr('asn.orgName'), local.org_name],
                [tr('asn.asName'), local.as_name],
                [tr('asn.country'), local.country],
                [tr('asn.orgId'), local.org_id],
                [tr('asn.role'), lang === 'zh' ? (roleZh[local.role_heuristic] || local.role_heuristic) : local.role_heuristic],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between border-t border-sky-500/10 py-1">
                  <dt className="text-slate-500">{k}</dt>
                  <dd className="font-medium text-slate-200">{v || '—'}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-3 text-xs text-slate-600">{lang === 'zh' ? '该角色为启发式估计，不是真实分类。' : local.role_disclaimer}</p>
          </div>
          <div className="dk-card p-5">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('asn.relTitle')}</h3>
            <div className="mt-3 grid grid-cols-3 gap-3 text-center">
              {[[tr('asn.providers'), local.provider_count, '#60a5fa'],
                [tr('asn.peers'), local.peer_count, '#34d399'],
                [tr('asn.customers'), local.customer_count, '#a78bfa']].map(([k, v, c]) => (
                <div key={k} className="rounded-lg border border-sky-500/10 bg-[#0b1121] p-3">
                  <p className="text-2xl font-bold" style={{ color: c }}>{v ?? 0}</p>
                  <p className="text-[11px] text-slate-500">{k}</p>
                </div>
              ))}
            </div>
            {local.same_org_asns?.length > 0 && (
              <div className="mt-4">
                <h4 className="text-xs font-semibold text-amber-400">{tr('asn.sameOrg')}</h4>
                <p className="mt-1 font-mono text-xs text-slate-400">
                  {local.same_org_asns.slice(0, 20).join(', ')}
                  {local.same_org_asns.length > 20 ? ` ... (+${local.same_org_asns.length - 20})` : ''}
                </p>
              </div>
            )}
          </div>
          <div className="dk-card p-5 md:col-span-2">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('asn.asrankTitle')}</h3>
            {asrank.available ? (
              <dl className="mt-3 grid grid-cols-2 gap-x-6 text-sm">
                {[['Rank', asrank.rank], ['Degree', asrank.degree], [tr('asn.country'), asrank.organization?.country], [tr('asn.orgName'), asrank.organization?.orgName]].map(([k, v]) => (
                  <div key={k} className="flex justify-between border-t border-sky-500/10 py-1">
                    <dt className="text-slate-500">{k}</dt>
                    <dd className="font-medium text-slate-200">{v ?? '—'}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="mt-2 text-sm text-amber-400/80">{tr('asn.asrankUnavailable')}</p>
            )}
          </div>
          <button onClick={() => navigate('/kg', { state: { mode: 'asn', input: asn } })} className="dk-btn-outline">
            {lang === 'zh' ? '查看 ASN 邻域图谱' : 'View ASN Neighborhood Graph'} →
          </button>
        </div>
      )}
    </div>
  )
}