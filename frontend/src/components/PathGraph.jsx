import { useLang } from '../i18n/context.jsx'

const relColor = { p2c: '#60a5fa', c2p: '#a78bfa', p2p: '#34d399', unknown: '#64748b' }

export default function PathGraph({ path, edges, nodes, highlightAsns }) {
  if (!path?.length) return null
  const nodeMap = Object.fromEntries((nodes || []).map((n) => [n.asn, n]))
  const hi = highlightAsns || new Set()
  return (
    <div className="dk-card overflow-x-auto p-5">
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-widest text-sky-400/70">Path graph</h3>
      <div className="flex min-w-max items-center gap-2">
        {path.map((asn, i) => (
          <div key={`${asn}-${i}`} className="flex items-center gap-2">
            <div className={`flex flex-col items-center rounded-lg border px-3 py-2 text-center ${
              hi.has(asn) ? 'border-rose-500/50 bg-rose-500/10' : 'border-sky-500/20 bg-[#0b1121]'
            }`}>
              <span className="font-mono text-sm font-bold text-white">AS{asn}</span>
              <span className="max-w-[8rem] truncate text-[10px] text-slate-500">{nodeMap[asn]?.org_name || '—'}</span>
            </div>
            {i < path.length - 1 && edges?.[i] ? (
              <div className="flex flex-col items-center px-1">
                <span className="font-mono text-[11px] font-semibold" style={{ color: relColor[edges[i].relationship] || relColor.unknown }}>
                  {edges[i].relationship}
                  {edges[i].same_org ? ' · org' : ''}
                </span>
                <span className="text-slate-600">→</span>
              </div>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  )
}