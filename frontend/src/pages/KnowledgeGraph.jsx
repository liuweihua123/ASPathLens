import { useState, useRef, useCallback, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import cytoscape from 'cytoscape'
import { useLang } from '../i18n/context.jsx'
import { getKgAsn, getKgPath, getKgOrg, getKgPattern, exportKg } from '../api/client.js'

const MODES = ['asn', 'path', 'org', 'pattern']
const MODE_LABELS = {
  asn: { en: 'ASN Neighborhood', zh: 'ASN 邻域' },
  path: { en: 'Path Subgraph', zh: '路径子图' },
  org: { en: 'Organization Graph', zh: '组织图谱' },
  pattern: { en: 'Pattern Graph', zh: '模式图谱' },
}
const REL_OPTIONS = ['all', 'provider', 'peer', 'customer', 'same-org', 'unknown']

const relLabelMap = {
  P2C: 'p2c', C2P: 'c2p', P2P: 'p2p', UNKNOWN_REL: 'unknown', SAME_ORG_AS: 'same-org',
  HAS_VIOLATION: 'violation', CANDIDATE_ASN: 'candidate',
  EXT_P2C: 'p2c', EXT_C2P: 'c2p', EXT_P2P: 'p2p',
}

const LAYOUTS = [
  { key: 'cose',         label: { en: 'Force (CoSE)',   zh: '力导向 (CoSE)' } },
  { key: 'concentric',   label: { en: 'Radial',         zh: '辐射布局' } },
  { key: 'breadthfirst', label: { en: 'Hierarchy',      zh: '层级布局' } },
  { key: 'grid',         label: { en: 'Grid',           zh: '网格布局' } },
]

/* ---- Cytoscape style ---- */
function cyStyle() {
  const relColors = {
    P2C: '#60a5fa', C2P: '#a78bfa', P2P: '#34d399', UNKNOWN_REL: '#475569', SAME_ORG_AS: '#fbbf24',
    HAS_VIOLATION: '#f43f5e', CANDIDATE_ASN: '#f43f5e',
    EXT_P2C: '#60a5fa', EXT_C2P: '#a78bfa', EXT_P2P: '#34d399',
  }
  const edgeStyles = Object.entries(relColors).map(([type, c]) => ({
    selector: `edge[type="${type}"]`,
    style: {
      'line-color': c, 'target-arrow-color': c, 'target-arrow-shape': 'triangle', width: 1.8,
      'label': 'data(relLabel)', 'font-size': '9px', color: c,
      'text-outline-color': '#0b1121', 'text-outline-width': 2,
      'text-rotation': 'autorotate', 'text-margin-y': -8,
    },
  }))
  return [
    { selector: 'node', style: {
      label: 'data(label)', 'font-size': '10px', 'text-valign': 'bottom', 'text-margin-y': 5,
      color: '#94a3b8', 'text-outline-color': '#0b1121', 'text-outline-width': 2,
      'text-wrap': 'ellipsis', 'text-max-width': '80px',
    }},
    { selector: 'node[type="ASN"]', style: { 'background-color': '#0ea5e9', shape: 'ellipse', width: 38, height: 38 } },
    { selector: 'node[type="Organization"]', style: { display: 'none' } },
    { selector: 'node[type="Country"]', style: { display: 'none' } },
    { selector: 'node[type="ASPath"]', style: { 'background-color': '#f59e0b', shape: 'round-rectangle', width: 55, height: 28 } },
    { selector: 'node[type="PathSegment"]', style: { 'background-color': '#dc2626', shape: 'rectangle', width: 44, height: 24 } },
    { selector: 'node[type="ViolationPattern"]', style: { 'background-color': '#f43f5e', shape: 'diamond', width: 38, height: 38 } },
    { selector: 'node[?is_candidate_leaker]', style: { 'border-width': 3, 'border-color': '#f43f5e', 'border-style': 'double' } },
    { selector: 'node[?is_expanded]', style: { 'border-width': 2, 'border-color': '#34d399', 'border-style': 'solid' } },
    { selector: 'edge[type="SAME_ORG_AS"]', style: { 'line-style': 'dashed', 'target-arrow-shape': 'none' } },
    { selector: 'edge[type="UNKNOWN_REL"]', style: { 'line-style': 'dotted' } },
    { selector: 'edge[?is_violation_edge]', style: { 'line-color': '#f43f5e', 'target-arrow-color': '#f43f5e', width: 3, 'line-style': 'dashed' } },
    ...edgeStyles,
  ]
}

/* ---- helpers ---- */
function makeCyNode(n) {
  return { data: { ...n.properties, id: n.id, label: n.label, type: n.type } }
}
function makeCyEdge(e) {
  return { data: {
    ...e.properties, id: e.id, source: e.source, target: e.target, type: e.type,
    relLabel: relLabelMap[e.type] ?? (e.properties?.relationship || ''),
    is_violation_edge: e.properties?.is_violation_edge || false,
  }}
}

/* ========================================================= */
export default function KnowledgeGraph() {
  const { tr, lang } = useLang()
  const location = useLocation()
  const cyRef = useRef(null)
  const containerRef = useRef(null)
  const [mode, setMode] = useState('asn')
  const [input, setInput] = useState('4134')
  const [graph, setGraph] = useState(null)
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [expanding, setExpanding] = useState(false)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ depth: 1, limit: 50, relationship: 'all' })
  const [layoutKey, setLayoutKey] = useState('cose')
  const expandedSet = useRef(new Set())  // track which ASNs have been expanded

  useEffect(() => {
    if (location.state?.mode) setMode(location.state.mode)
    if (location.state?.input) setInput(location.state.input)
  }, [location.state])

  /* ---- render fresh graph ---- */
  const renderGraph = useCallback((data, lk) => {
    if (!containerRef.current || !data?.nodes?.length) return
    if (cyRef.current) cyRef.current.destroy()
    expandedSet.current = new Set()

    // Filter: only keep ASN, PathSegment, ViolationPattern, ASPath nodes;
    // strip Org / Country / BELONGS_TO / LOCATED_IN
    const keepNode = new Set(
      (data.nodes || []).filter(n => !['Organization', 'Country'].includes(n.type)).map(n => n.id)
    )
    const nodes = (data.nodes || []).filter(n => keepNode.has(n.id)).map(makeCyNode)
    const edges = (data.edges || [])
      .filter(e => keepNode.has(e.source) && keepNode.has(e.target))
      .filter(e => !['BELONGS_TO', 'LOCATED_IN'].includes(e.type))
      .map(makeCyEdge)

    const cy = cytoscape({
      container: containerRef.current,
      elements: { nodes, edges },
      style: cyStyle(),
      layout: { name: lk || 'cose', animate: true, nodeRepulsion: () => 8000, idealEdgeLength: () => 120, padding: 30 },
      minZoom: 0.15, maxZoom: 4,
    })

    cy.on('tap', 'node', (evt) => {
      const d = evt.target.data()
      setSelected({ kind: 'node', type: d.type, id: d.id, data: d })
    })
    cy.on('tap', 'edge', (evt) => {
      const d = evt.target.data()
      setSelected({ kind: 'edge', type: d.type, id: d.id, data: d })
    })
    cy.on('tap', (evt) => { if (evt.target === cy) setSelected(null) })
    cyRef.current = cy
  }, [])

  /* ---- expand a single ASN node ---- */
  async function expandNode(asn) {
    if (!cyRef.current || expandedSet.current.has(asn)) return
    setExpanding(true); setError('')
    try {
      const data = await getKgAsn(asn, { depth: 1, limit: 20, relationship: 'all', include_org: false, include_asrank: false })
      const cy = cyRef.current

      // Only accept ASN-type nodes to avoid org/country cruft
      const asnNodeIds = new Set(
        (data.nodes || []).filter(n => n.type === 'ASN').map(n => n.id)
      )
      const existingIds = new Set(cy.nodes().map(n => n.id()))

      // Add new ASN nodes
      const newNodes = (data.nodes || [])
        .filter(n => n.type === 'ASN' && !existingIds.has(n.id))
        .map(makeCyNode)
      if (newNodes.length) cy.add(newNodes.map(n => ({ group: 'nodes', data: n.data })))

      // Merge back the set of all known node ids (existing + newly added)
      const knownIds = new Set([...existingIds, ...asnNodeIds])

      // Add only edges whose both endpoints exist among known nodes
      const existingEdgeIds = new Set(cy.edges().map(e => e.id()))
      const newEdges = (data.edges || [])
        .filter(e => knownIds.has(e.source) && knownIds.has(e.target) && !existingEdgeIds.has(e.id))
        .filter(e => !['BELONGS_TO', 'LOCATED_IN'].includes(e.type))  // never add org edges
        .map(makeCyEdge)
      if (newEdges.length) cy.add(newEdges.map(e => ({ group: 'edges', data: e.data })))

      // Mark the expanded node
      const targetNode = cy.getElementById(`asn:${asn}`)
      if (targetNode.length) targetNode.data('is_expanded', true)

      expandedSet.current.add(asn)

      // Re-layout gently
      cy.layout({ name: 'cose', animate: true, nodeRepulsion: () => 6000, idealEdgeLength: () => 100, padding: 20, randomize: false }).run()
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
    } finally { setExpanding(false) }
  }

  /* ---- initial search ---- */
  async function onSearch() {
    setLoading(true); setError(''); setGraph(null); setSelected(null)
    try {
      let data
      if (mode === 'asn') data = await getKgAsn(input, { ...filters, include_org: false })
      else if (mode === 'path') data = await getKgPath(input)
      else if (mode === 'org') data = await getKgOrg(input, filters.limit)
      else data = await getKgPattern(input)
      setGraph(data); renderGraph(data, layoutKey)
    } catch (e) { setError(e.response?.data?.detail || e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => () => { if (cyRef.current) cyRef.current.destroy() }, [])

  const summary = graph?.meta?.summary || graph?.meta || {}

  /* ---- export ---- */
  async function onExport(fmt) {
    if (!graph) return
    try {
      const data = await exportKg(graph, fmt)
      const content = fmt === 'graphml' ? data.graphml : fmt === 'cypher' ? data.cypher : JSON.stringify(data, null, 2)
      const ext = { json: 'json', cytoscape: 'json', graphml: 'xml', cypher: 'cypher' }[fmt] || 'txt'
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([typeof content === 'string' ? content : JSON.stringify(content, null, 2)], { type: 'text/plain' }))
      a.download = `aspathlens-kg.${ext}`; a.click()
    } catch (e) { setError(e.message) }
  }

  const canExpand = selected?.kind === 'node' && selected.type === 'ASN' && !expandedSet.current.has(selected.data?.asn)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-white">Knowledge Graph</h1>

      {/* Mode tabs */}
      <div className="flex flex-wrap gap-2">
        {MODES.map(m => (
          <button key={m} onClick={() => { setMode(m); setGraph(null); setSelected(null) }}
            className={`rounded-lg px-3 py-1.5 text-sm transition ${mode === m ? 'bg-sky-500 text-white' : 'bg-[#0b1121] text-slate-400 hover:text-sky-300'}`}>
            {MODE_LABELS[m][lang]}</button>
        ))}
      </div>

      {/* Input bar */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="text-xs font-semibold uppercase tracking-widest text-sky-400/70">
            {mode === 'asn' ? 'ASN' : mode === 'path' ? 'AS Path' : mode === 'org' ? tr('asn.orgName') : tr('pattern.pattern')}</label>
          <input className="dk-input mt-1 w-64 font-mono" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onSearch()}
            placeholder={mode === 'asn' ? '4134' : mode === 'path' ? '3356 4134 4837 9808' : mode === 'org' ? 'China Telecom' : 'p2p -> c2p'} />
        </div>
        {mode === 'asn' && (<>
          <div><label className="text-xs text-slate-500">Depth</label>
            <select className="dk-input mt-1 block" value={filters.depth} onChange={e => setFilters({ ...filters, depth: +e.target.value })}>
              <option value={1}>1-hop</option><option value={2}>2-hop</option></select></div>
          <div><label className="text-xs text-slate-500">Limit</label>
            <select className="dk-input mt-1 block" value={filters.limit} onChange={e => setFilters({ ...filters, limit: +e.target.value })}>
              <option value={20}>20</option><option value={50}>50</option><option value={100}>100</option></select></div>
          <div><label className="text-xs text-slate-500">Filter</label>
            <select className="dk-input mt-1 block" value={filters.relationship} onChange={e => setFilters({ ...filters, relationship: e.target.value })}>
              {REL_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}</select></div>
        </>
        )}
        {/* Layout selector */}
        <div>
          <label className="text-xs text-slate-500">{lang === 'zh' ? '布局' : 'Layout'}</label>
          <select className="dk-input mt-1 block" value={layoutKey} onChange={e => setLayoutKey(e.target.value)}>
            {LAYOUTS.map(l => <option key={l.key} value={l.key}>{l.label[lang]}</option>)}
          </select>
        </div>
        <button onClick={onSearch} disabled={loading} className="dk-btn-primary disabled:opacity-50">
          {loading ? (lang === 'zh' ? '加载中…' : 'Loading…') : (lang === 'zh' ? '构建图谱' : 'Build Graph')}</button>
      </div>

      {error && <p className="text-sm text-rose-400">{error}</p>}
      {graph?.meta?.warning && (
        <div className="dk-card border-amber-500/30 p-3 text-sm text-amber-300/80">⚠ {graph.meta.warning}</div>
      )}

      {/* Graph + Side panel */}
      <div className="flex gap-4" style={{ minHeight: '520px' }}>
        <div className="dk-card flex-1 overflow-hidden" ref={containerRef} style={{ minHeight: '520px' }} />

        <div className="w-72 space-y-3">
          {/* Summary */}
          {summary && Object.keys(summary).length > 0 && (
            <div className="dk-card p-4 text-sm">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{lang === 'zh' ? '摘要' : 'Summary'}</h3>
              {[
                [tr('asn.providers'), summary.provider_count],
                [tr('asn.peers'), summary.peer_count],
                [tr('asn.customers'), summary.customer_count],
                [tr('asn.sameOrg'), summary.same_org_asn_count],
                [lang === 'zh' ? '总邻居' : 'Total neighbors', summary.total_neighbors],
                [lang === 'zh' ? '已展示' : 'Shown', summary.shown_neighbors],
                [tr('risk.title'), summary.risk_score],
                [lang === 'zh' ? '候选泄露者' : 'Candidate', summary.candidate_leaker ? `AS${summary.candidate_leaker}` : undefined],
                ['Valley-free', summary.is_valley_free !== undefined ? (summary.is_valley_free ? '✓ valid' : '✗ violated') : undefined],
                [lang === 'zh' ? '成员 ASN' : 'Members', summary.member_count],
              ].filter(([, v]) => v !== undefined).map(([k, v]) => (
                <div key={k} className="flex justify-between border-t border-sky-500/10 py-1">
                  <span className="text-slate-500">{k}</span>
                  <span className="font-medium text-slate-200">{v}</span>
                </div>
              ))}
            </div>
          )}

          {/* Selected detail */}
          {selected && (
            <div className="dk-card p-4 text-sm">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{lang === 'zh' ? '详情' : 'Details'}</h3>
              <p className="text-xs text-slate-500">
                {selected.kind === 'node' ? (lang === 'zh' ? '节点' : 'Node') : (lang === 'zh' ? '边' : 'Edge')}:{' '}
                <span className="font-semibold text-sky-300">{selected.type}</span>
              </p>
              {selected.data?.asn && (
                <p className="mt-1 text-xs text-slate-400">
                  {selected.data.org_name && <span>{selected.data.org_name} · </span>}
                  {selected.data.country && <span>{selected.data.country}</span>}
                </p>
              )}
              <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-[#0b1121] p-2 text-xs text-slate-400">
                {JSON.stringify(selected.data, null, 2)}
              </pre>

              {/* Expand button */}
              {canExpand && (
                <button onClick={() => expandNode(selected.data.asn)} disabled={expanding}
                  className="dk-btn-outline mt-3 w-full text-xs disabled:opacity-50">
                  {expanding
                    ? (lang === 'zh' ? '扩展中…' : 'Expanding…')
                    : (lang === 'zh' ? `展开 AS${selected.data.asn} 的邻居` : `Expand AS${selected.data.asn} neighbors`)}
                </button>
              )}
              {selected.kind === 'node' && selected.type === 'ASN' && expandedSet.current.has(selected.data?.asn) && (
                <p className="mt-2 text-xs text-emerald-400">✓ {lang === 'zh' ? '已扩展' : 'Expanded'}</p>
              )}
            </div>
          )}

          {/* Export */}
          {graph && (
            <div className="dk-card p-4">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-sky-400/70">{lang === 'zh' ? '导出' : 'Export'}</h3>
              <div className="flex flex-wrap gap-2">
                {['json', 'cytoscape', 'graphml', 'cypher'].map(f => (
                  <button key={f} onClick={() => onExport(f)} className="dk-btn-ghost text-xs">{f}</button>
                ))}
              </div>
            </div>
          )}

          {/* Help */}
          <div className="dk-card p-3 text-xs text-slate-600">
            {lang === 'zh'
              ? '点击任意 ASN 节点，然后点击"展开邻居"按钮可向外扩展该节点的连接。'
              : 'Click any ASN node, then click "Expand neighbors" to grow the graph from that node.'}
          </div>
        </div>
      </div>
    </div>
  )
}