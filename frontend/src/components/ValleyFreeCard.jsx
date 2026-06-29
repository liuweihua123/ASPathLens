import { useLang } from '../i18n/context.jsx'

export default function ValleyFreeCard({ vf }) {
  const { tr, explain } = useLang()
  if (!vf) return null
  const label = vf.uncertain ? tr('vf.uncertain') : vf.is_valid ? tr('vf.valid') : tr('vf.invalid')
  const border = vf.is_valid === false ? 'border-rose-500/30' : vf.uncertain ? 'border-amber-500/20' : 'border-emerald-500/20'
  return (
    <div className={`dk-card p-5 ${border}`}>
      <h3 className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">{tr('vf.title')}</h3>
      <p className={`mt-2 text-lg font-bold ${
        vf.is_valid === false ? 'text-rose-400' : vf.uncertain ? 'text-amber-400' : 'text-emerald-400'
      }`}>{label}</p>
      {vf.violation_pattern && <p className="mt-1 font-mono text-sm text-rose-400/80">{vf.violation_pattern}</p>}
      <p className="mt-3 text-sm leading-relaxed text-slate-400">{explain(vf)}</p>
    </div>
  )
}