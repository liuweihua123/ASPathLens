import { useLang } from '../i18n/context.jsx'

const levelStyle = {
  normal: 'text-emerald-400',
  uncertain: 'text-amber-400',
  suspicious: 'text-orange-400',
  'highly suspicious': 'text-rose-400',
}
const levelBg = {
  normal: 'bg-emerald-500/15', uncertain: 'bg-amber-500/15',
  suspicious: 'bg-orange-500/15', 'highly suspicious': 'bg-rose-500/15',
}
const levelZh = { normal: '正常', uncertain: '不确定', suspicious: '可疑', 'highly suspicious': '高度可疑' }

export default function RiskCard({ risk, coverage }) {
  const { lang, tr } = useLang()
  if (!risk) return null
  return (
    <div className="dk-card p-5">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('risk.title')}</h3>
      <p className="mt-2 text-3xl font-extrabold text-white">
        {risk.score}{' '}
        <span className={`rounded-full px-2 py-0.5 text-sm font-semibold ${levelStyle[risk.level] || ''} ${levelBg[risk.level] || ''}`}>
          {lang === 'zh' ? levelZh[risk.level] || risk.level : risk.level}
        </span>
      </p>
      {coverage && (
        <p className="mt-2 text-xs text-slate-500">
          {tr('risk.coverage')}: {coverage.known_ratio} ({coverage.coverage_level})
        </p>
      )}
      <ul className="mt-3 list-inside list-disc space-y-0.5 text-xs text-slate-400">
        {risk.evidence?.map((e) => <li key={e}>{e}</li>)}
      </ul>
    </div>
  )
}