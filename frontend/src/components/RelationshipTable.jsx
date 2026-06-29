import { useLang } from '../i18n/context.jsx'

export default function RelationshipTable({ edges, sequence }) {
  const { tr } = useLang()
  if (!edges?.length) return null
  return (
    <div className="dk-card overflow-hidden">
      <table className="w-full text-left text-sm">
        <thead>
          <tr>
            <th className="dk-th">{tr('rel.from')}</th>
            <th className="dk-th">{tr('rel.to')}</th>
            <th className="dk-th">{tr('rel.relationship')}</th>
            <th className="dk-th">{tr('rel.sameOrg')}</th>
          </tr>
        </thead>
        <tbody>
          {edges.map((e, i) => (
            <tr key={i} className="hover:bg-sky-500/5">
              <td className="dk-td font-mono">AS{e.from}</td>
              <td className="dk-td font-mono">AS{e.to}</td>
              <td className="dk-td font-mono font-semibold" style={{ color: e.relationship === 'p2c' ? '#60a5fa' : e.relationship === 'c2p' ? '#a78bfa' : e.relationship === 'p2p' ? '#34d399' : '#64748b' }}>
                {e.relationship}
              </td>
              <td className="dk-td">{e.same_org ? tr('rel.yes') : tr('rel.no')}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="border-t border-sky-500/10 px-3 py-2 font-mono text-xs text-slate-500">
        {tr('rel.sequence')}: {sequence?.join(' → ')}
      </div>
    </div>
  )
}