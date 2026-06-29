import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLang } from '../i18n/context.jsx'

/* =========================================================
   ASPathLens Landing Page
   ========================================================= */

export default function Home() {
  const { tr, lang } = useLang()
  const nav = useNavigate()
  const [demoPath, setDemoPath] = useState('')

  const examples = [
    { label: lang === 'zh' ? '合法路径' : 'Valid path', path: '174 2914 3356', badge: 'valid', badgeColor: 'bg-emerald-500/20 text-emerald-400' },
    { label: lang === 'zh' ? '可疑模式' : 'Suspicious', path: '3356 1299 4837 9808', badge: 'suspicious', badgeColor: 'bg-amber-500/20 text-amber-400' },
    { label: lang === 'zh' ? '同组织路径' : 'Same-org', path: '4134 4809 58453', badge: 'same-org', badgeColor: 'bg-sky-500/20 text-sky-400' },
    { label: lang === 'zh' ? 'Prepending' : 'Prepending', path: '3356 4134 4134 4137 9808', badge: 'prepended', badgeColor: 'bg-slate-500/20 text-slate-400' },
  ]

  const features = [
    { icon: '🔍', key: 'f1', en: 'AS Path Analysis', zh: 'AS 路径分析', descEn: 'Label AS relationships hop by hop and explain path policy plausibility.', descZh: '逐跳标注 AS 商业关系，解释路径策略是否合理。' },
    { icon: '⛰️', key: 'f2', en: 'Valley-free Check', zh: 'Valley-free 检测', descEn: 'Detect valley-free violations and locate suspicious relationship transitions.', descZh: '检测 valley-free 违规，并定位可疑关系跳转。' },
    { icon: '🏢', key: 'f3', en: 'Same-org Reasoning', zh: '同组织推理', descEn: 'Use AS2Org to reduce false positives from organization-internal routing.', descZh: '利用 AS2Org 识别同组织 AS，降低组织内部调度造成的误判。' },
    { icon: '🕸️', key: 'f4', en: 'Knowledge Graph', zh: '知识图谱', descEn: 'Explore ASNs, organizations, relationships, path segments, and violation patterns as a graph.', descZh: '以知识图谱形式探索 ASN、组织、关系边、路径片段和可疑模式。' },
    { icon: '📡', key: 'f5', en: 'ASN Neighborhood', zh: 'ASN 邻域', descEn: 'Inspect providers, peers, customers, same-org ASNs, and ASRank topology.', descZh: '查看 providers、peers、customers、同组织 AS 和 ASRank 拓扑画像。' },
    { icon: '📊', key: 'f6', en: 'Dataset-aware', zh: '数据版本感知', descEn: 'Track dataset versions, relationship coverage, and changes over time.', descZh: '跟踪数据版本、关系覆盖率和 ASRelationship 变化。' },
  ]

  const steps = [
    { n: '01', en: 'AS Path Input', zh: 'AS Path 输入', icon: '📝' },
    { n: '02', en: 'Normalize Path', zh: '路径规范化', icon: '⚙️' },
    { n: '03', en: 'Map ASN → Org', zh: 'ASN → 组织映射', icon: '🏢' },
    { n: '04', en: 'Label Relationships', zh: '标注商业关系', icon: '🔗' },
    { n: '05', en: 'Valley-free Check', zh: 'Valley-free 检测', icon: '⛰️' },
    { n: '06', en: 'Build Graph', zh: '构建知识图谱', icon: '🕸️' },
    { n: '07', en: 'Export Report', zh: '导出报告', icon: '📄' },
  ]

  const dataSources = [
    { name: 'CAIDA ASRelationship', desc: lang === 'zh' ? '用于 AS 商业关系推断：p2c、c2p、p2p。' : 'Used for AS commercial relationship inference: p2c, c2p, p2p.', tag: 'Core' },
    { name: 'CAIDA AS2Org', desc: lang === 'zh' ? '用于 ASN 到组织映射和同组织推理。' : 'Used for ASN-to-organization mapping and same-org reasoning.', tag: 'Core' },
    { name: 'CAIDA ASRank', desc: lang === 'zh' ? '用于 ASN rank、degree、customer cone 和拓扑画像增强。' : 'Used for ASN rank, degree, customer cone, and topology enhancement.', tag: 'Enhancement' },
  ]

  return (
    <div className="-mx-4 -mt-8 min-h-screen bg-[#060a14]">
      {/* ========= HERO ========= */}
      <section className="bg-grid relative overflow-hidden">
        {/* Gradient blobs */}
        <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-sky-500/10 blur-3xl" />
        <div className="pointer-events-none absolute -right-32 top-1/3 h-80 w-80 rounded-full bg-indigo-500/10 blur-3xl" />

        <div className="mx-auto max-w-7xl px-4 pb-16 pt-20 md:pb-24 md:pt-28">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            {/* Left: text */}
            <div className="fade-up">
              <span className="mb-4 inline-block rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-400">
                Open-source BGP research tool
              </span>
              <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-white md:text-5xl">
                AS<span className="text-sky-400">Path</span>Lens
              </h1>
              <p className="mt-4 max-w-xl text-lg text-slate-300">
                {lang === 'zh'
                  ? '面向 BGP 路由策略研究的 AS 路径分析器和轻量级 AS 知识图谱工具。'
                  : 'Relationship-aware AS path analysis and lightweight AS knowledge graph for BGP policy research.'}
              </p>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-slate-400">
                {lang === 'zh'
                  ? '输入一条 AS Path，自动解释 AS 组织归属、商业关系、valley-free 策略、潜在 route leak 模式和知识图谱上下文。'
                  : 'Paste an AS path. ASPathLens explains AS ownership, relationships, valley-free policy, potential route-leak patterns, and knowledge graph context.'}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a href="/analyzer" className="rounded-lg bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-sky-500/25 transition hover:bg-sky-400 hover:shadow-sky-500/40">
                  {lang === 'zh' ? '分析 AS Path' : 'Analyze an AS Path'}
                </a>
                <a href="/kg" className="rounded-lg border border-sky-500/40 px-5 py-2.5 text-sm font-semibold text-sky-300 transition hover:bg-sky-500/10">
                  {lang === 'zh' ? '探索知识图谱' : 'Explore Knowledge Graph'}
                </a>
                <a href="/examples" className="rounded-lg border border-slate-600 px-5 py-2.5 text-sm font-medium text-slate-400 transition hover:border-slate-500 hover:text-slate-300">
                  {lang === 'zh' ? '查看示例' : 'View Examples'}
                </a>
              </div>
            </div>

            {/* Right: preview card */}
            <div className="fade-up fade-up-d2">
              <PreviewCard lang={lang} />
            </div>
          </div>
        </div>
      </section>

      {/* ========= QUICK DEMO ========= */}
      <section className="border-t border-sky-500/10 bg-[#080e1e]">
        <div className="mx-auto max-w-3xl px-4 py-14">
          <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-sky-400/70">
            {lang === 'zh' ? '快速体验' : 'Quick Demo'}
          </h2>
          <div className="mt-6 flex gap-2">
            <input
              value={demoPath}
              onChange={(e) => setDemoPath(e.target.value)}
              placeholder="3356 4134 4837 9808"
              className="flex-1 rounded-lg border border-sky-500/20 bg-[#0b1121] px-4 py-3 font-mono text-sm text-white placeholder:text-slate-600 focus:border-sky-500/50 focus:outline-none focus:ring-1 focus:ring-sky-500/30"
            />
            <button
              onClick={() => { if (demoPath.trim()) nav('/analyzer', { state: { path: demoPath.trim() } }) }}
              className="rounded-lg bg-sky-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-sky-400"
            >
              {lang === 'zh' ? '分析' : 'Analyze'}
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {examples.map((ex) => (
              <button key={ex.path} onClick={() => setDemoPath(ex.path)}
                className="group flex items-center gap-1.5 rounded-md border border-slate-700/60 bg-[#0b1121] px-3 py-1.5 text-xs transition hover:border-sky-500/30 hover:bg-[#111c32]">
                <span className={`inline-block h-1.5 w-1.5 rounded-full ${ex.badgeColor.split(' ')[0].replace('text-', 'bg-')}`} />
                <span className="text-slate-400 group-hover:text-slate-300">{ex.label}</span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ========= CAPABILITIES ========= */}
      <section className="border-t border-sky-500/10 bg-[#060a14]">
        <div className="mx-auto max-w-7xl px-4 py-20">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl">
            {lang === 'zh' ? '核心能力' : 'Core Capabilities'}
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-sm text-slate-400">
            {lang === 'zh'
              ? '从路径分析到知识图谱，覆盖 BGP 策略研究的主要工作流。'
              : 'From path analysis to knowledge graph — covering the core BGP policy research workflow.'}
          </p>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <div key={f.key}
                className={`glass glow-border group rounded-xl p-5 transition-all duration-300 hover:-translate-y-1 fade-up fade-up-d${i + 1}`}>
                <div className="mb-3 text-2xl">{f.icon}</div>
                <h3 className="font-semibold text-white">{lang === 'zh' ? f.zh : f.en}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">
                  {lang === 'zh' ? f.descZh : f.descEn}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========= HOW IT WORKS ========= */}
      <section className="border-t border-sky-500/10 bg-[#080e1e]">
        <div className="mx-auto max-w-7xl px-4 py-20">
          <h2 className="text-center text-2xl font-bold text-white md:text-3xl">
            {lang === 'zh' ? '工作流程' : 'How It Works'}
          </h2>
          <div className="mt-12 flex items-center justify-center gap-2 overflow-x-auto px-2">
            {steps.map((s, i) => (
              <div key={s.n} className="flex shrink-0 items-center gap-2">
                <div className="glass glow-border flex h-[6.5rem] w-[7rem] flex-col items-center justify-center rounded-lg px-1.5 py-2 text-center transition hover:-translate-y-0.5">
                  <span className="text-lg">{s.icon}</span>
                  <span className="mt-0.5 text-[10px] font-bold text-sky-400/60">{s.n}</span>
                  <span className="mt-0.5 text-[11px] font-medium leading-tight text-slate-300">{lang === 'zh' ? s.zh : s.en}</span>
                </div>
                {i < steps.length - 1 && <span className="shrink-0 text-slate-600 select-none">→</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========= KNOWLEDGE GRAPH PREVIEW ========= */}
      <section className="border-t border-sky-500/10 bg-[#060a14]">
        <div className="mx-auto max-w-7xl px-4 py-20">
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <div>
              <h2 className="text-2xl font-bold text-white md:text-3xl">
                {lang === 'zh' ? '知识图谱' : 'Knowledge Graph'}
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-slate-400">
                {lang === 'zh'
                  ? 'ASPathLens 不只是路径表格，而是将 AS 关系、组织归属、路径片段和可疑模式组织成可探索的知识图谱。'
                  : 'Not just a path table. ASPathLens turns AS relationships, organizations, path segments, and suspicious patterns into an explorable knowledge graph.'}
              </p>
              <div className="mt-6 space-y-3">
                {[
                  { color: 'bg-sky-400', label: 'ASN nodes', zhLabel: 'ASN 节点' },
                  { color: 'bg-violet-400', label: 'Organization nodes', zhLabel: '组织节点' },
                  { color: 'bg-rose-400', label: 'Violation patterns', zhLabel: '违规模式' },
                  { color: 'bg-emerald-400', label: 'Relationship edges', zhLabel: '关系边' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2 text-sm text-slate-400">
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${item.color}`} />
                    {lang === 'zh' ? item.zhLabel : item.label}
                  </div>
                ))}
              </div>
              <a href="/kg" className="mt-8 inline-block rounded-lg border border-sky-500/40 px-5 py-2.5 text-sm font-semibold text-sky-300 transition hover:bg-sky-500/10">
                {lang === 'zh' ? '打开知识图谱' : 'Open Knowledge Graph'} →
              </a>
            </div>
            <KgPreview />
          </div>
        </div>
      </section>

      {/* ========= DATA SOURCES ========= */}
      <section className="border-t border-sky-500/10 bg-[#080e1e]">
        <div className="mx-auto max-w-5xl px-4 py-20">
          <h2 className="text-center text-2xl font-bold text-white">
            {lang === 'zh' ? '数据来源' : 'Data Sources'}
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-sm text-slate-500">
            {lang === 'zh'
              ? 'ASPathLens 进行的是基于 AS 关系的路径策略分析，不是实时 BGP 事件确认系统。'
              : 'ASPathLens performs relationship-aware policy analysis, not real-time BGP incident confirmation.'}
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-3">
            {dataSources.map((ds) => (
              <div key={ds.name} className="glass glow-border rounded-xl p-5 transition hover:-translate-y-0.5">
                <div className="flex items-center justify-between">
                  <h3 className="font-mono text-sm font-semibold text-sky-300">{ds.name}</h3>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                    ds.tag === 'Core' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400'
                  }`}>{ds.tag}</span>
                </div>
                <p className="mt-3 text-sm text-slate-400">{ds.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========= EXAMPLES ========= */}
      <section className="border-t border-sky-500/10 bg-[#060a14]">
        <div className="mx-auto max-w-5xl px-4 py-20">
          <h2 className="text-center text-2xl font-bold text-white">
            {lang === 'zh' ? '示例' : 'Examples'}
          </h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { name: lang === 'zh' ? '合法路径' : 'Valid path', path: '174 2914 3356', level: 'normal', levelColor: 'text-emerald-400' },
              { name: lang === 'zh' ? '可疑模式' : 'Suspicious', path: '3356 1299 4837 9808', level: 'highly suspicious', levelColor: 'text-rose-400' },
              { name: lang === 'zh' ? 'Prepending' : 'Prepending', path: '3356 4134 4134 4837', level: 'normalized', levelColor: 'text-sky-400' },
              { name: lang === 'zh' ? '私有 ASN' : 'Private ASN', path: '3356 64512 4134', level: 'warning', levelColor: 'text-amber-400' },
            ].map((ex) => (
              <button key={ex.path} onClick={() => nav('/analyzer', { state: { path: ex.path } })}
                className="glass glow-border group rounded-xl p-5 text-left transition-all hover:-translate-y-1">
                <h3 className="text-sm font-semibold text-white">{ex.name}</h3>
                <p className="mt-1 font-mono text-xs text-sky-300/80">{ex.path}</p>
                <div className="mt-3 flex items-center justify-between">
                  <span className={`text-xs font-medium ${ex.levelColor}`}>{ex.level}</span>
                  <span className="text-xs text-slate-600 transition group-hover:text-sky-400">Try it →</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ========= CAPABILITY BOUNDARY ========= */}
      <section className="border-t border-sky-500/10 bg-[#080e1e]">
        <div className="mx-auto max-w-3xl px-4 py-12 text-center">
          <div className="glass inline-block rounded-xl border border-amber-500/20 px-6 py-4">
            <p className="text-sm text-amber-200/90">
              ⚠️{' '}
              {lang === 'zh'
                ? '该工具不能单独确认 BGP 劫持或真实路由泄露，只能解释基于 AS 商业关系和组织归属的路径策略可疑性。'
                : 'ASPathLens does not confirm BGP hijacks or route leaks. It explains AS relationship policy suspiciousness using CAIDA ASRelationship, AS2Org, and ASRank.'}
            </p>
          </div>
        </div>
      </section>

      {/* ========= FOOTER ========= */}
      <footer className="border-t border-sky-500/10 bg-[#060a14]">
        <div className="mx-auto max-w-7xl px-4 py-10">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="text-lg font-bold text-white">AS<span className="text-sky-400">Path</span>Lens</span>
              <p className="mt-1 text-xs text-slate-500">
                {lang === 'zh'
                  ? '面向 BGP 策略研究的 AS 路径分析器和知识图谱工具。'
                  : 'Relationship-aware AS path analysis for BGP policy research.'}
              </p>
            </div>
            <div className="flex gap-4 text-xs text-slate-500">
              <a href="https://github.com" className="hover:text-sky-400">GitHub</a>
              <span>·</span>
              <a href="/docs" className="hover:text-sky-400">API Docs</a>
              <span>·</span>
              <span>MIT License</span>
            </div>
          </div>
          <p className="mt-6 text-center text-[11px] text-slate-600">
            Built for BGP policy research. Powered by CAIDA ASRelationship, AS2Org, and ASRank.
          </p>
        </div>
      </footer>
    </div>
  )
}

/* =========================================================
   Sub-components
   ========================================================= */

function PreviewCard({ lang }) {
  return (
    <div className="glass glow-border rounded-2xl p-0 shadow-2xl shadow-sky-500/5">
      {/* Tab bar */}
      <div className="flex items-center gap-2 border-b border-sky-500/10 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-rose-500/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber-500/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
        <span className="ml-3 text-[11px] font-mono text-slate-500">aspathlens — path analysis</span>
      </div>
      <div className="p-5 font-mono text-xs leading-6">
        <div className="text-slate-500">
          <span className="text-sky-400">$</span> aspathlens analyze <span className="text-emerald-400">"3356 4134 4837 9808"</span>
        </div>
        <div className="mt-4 space-y-1.5">
          <Row label={lang === 'zh' ? '路径' : 'Path'} value="AS3356 → AS4134 → AS4837 → AS9808" />
          <Row label="Org" value="Lumen → China Telecom → China Unicom → China Mobile" />
          <Row label="Sequence">
            <span className="rel-p2c">p2c</span>
            {' → '}
            <span className="rel-p2p">p2p</span>
            {' → '}
            <span className="rel-p2c">p2c</span>
          </Row>
          <Row label="Valley-free" value={lang === 'zh' ? '合法 ✓' : 'Valid ✓'} valueClass="text-emerald-400" />
          <Row label={lang === 'zh' ? '风险评分' : 'Risk'} value="72 / 100 — suspicious" valueClass="text-amber-400" />
        </div>
        <div className="mt-4 rounded-lg bg-rose-500/10 px-3 py-2 text-[11px] text-rose-300/80">
          ⚠ {lang === 'zh' ? '候选 route leak 模式：AS4837 (p2p → p2c)' : 'Candidate route leak pattern: AS4837 (p2p → p2c)'}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, valueClass, children }) {
  return (
    <div className="flex gap-2">
      <span className="w-20 shrink-0 text-slate-500">{label}</span>
      <span className={valueClass || 'text-slate-300'}>{value || children}</span>
    </div>
  )
}

/* =========================================================
   Static Knowledge Graph Preview (Pure SVG)
   ========================================================= */

function KgPreview() {
  const W = 560, H = 300

  // Node positions (center coords)
  const nodes = [
    { id: '3356', x: 70,  y: 65, label: 'AS3356', type: 'asn' },
    { id: '4134', x: 210, y: 65, label: 'AS4134', type: 'asn' },
    { id: '4837', x: 350, y: 65, label: 'AS4837', type: 'asn' },
    { id: '9808', x: 490, y: 65, label: 'AS9808', type: 'asn' },
    { id: 'lumen', x: 70,  y: 160, label: 'Lumen', type: 'org' },
    { id: 'ct',    x: 210, y: 160, label: 'China Telecom', type: 'org' },
    { id: 'cu',    x: 350, y: 160, label: 'China Unicom', type: 'org' },
    { id: 'cm',    x: 490, y: 160, label: 'China Mobile', type: 'org' },
    { id: 'pat',   x: 350, y: 252, label: 'p2p→c2p', type: 'pattern' },
  ]

  const edges = [
    { from: '3356', to: '4134', type: 'p2c', label: 'p2c' },
    { from: '4134', to: '4837', type: 'p2p', label: 'p2p' },
    { from: '4837', to: '9808', type: 'p2c', label: 'p2c' },
    { from: '3356', to: 'lumen', type: 'belongs', label: '' },
    { from: '4134', to: 'ct',    type: 'belongs', label: '' },
    { from: '4837', to: 'cu',    type: 'belongs', label: '' },
    { from: '9808', to: 'cm',    type: 'belongs', label: '' },
    { from: '4837', to: 'pat',   type: 'violation', label: '' },
  ]

  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]))

  const edgeColor = { p2c: '#60a5fa', p2p: '#34d399', belongs: '#334155', violation: '#f43f5e' }
  const nodeFill   = { asn: '#0ea5e922', org: '#8b5cf622', pattern: '#f43f5e22' }
  const nodeStroke = { asn: '#0ea5e988', org: '#8b5cf688', pattern: '#f43f5e88' }
  const nodeTextColor = { asn: '#0ea5e9', org: '#8b5cf6', pattern: '#f43f5e' }

  // Radii for hit-testing
  const nodeRx = { asn: 20, org: 36, pattern: 18 }
  const nodeRy = { asn: 20, org: 16, pattern: 18 }

  return (
    <div className="glass glow-border relative w-full overflow-hidden rounded-2xl">
      <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full">
        {/* Edges */}
        {edges.map(e => {
          const s = nodeMap[e.from], t = nodeMap[e.to]
          if (!s || !t) return null
          // Shorten line to not overlap node border
          const dx = t.x - s.x, dy = t.y - s.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const sr = nodeRx[s.type] || 20, tr2 = nodeRx[t.type] || 20
          const x1 = s.x + (dx / dist) * (sr + 4)
          const y1 = s.y + (dy / dist) * (nodeRy[s.type] + 4)
          const x2 = t.x - (dx / dist) * (tr2 + 4)
          const y2 = t.y - (dy / dist) * (nodeRy[t.type] + 4)
          const mx = (x1 + x2) / 2, my = (y1 + y2) / 2
          return (
            <g key={`${e.from}-${e.to}`}>
              <line x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={edgeColor[e.type] || '#334155'}
                strokeWidth={e.type === 'violation' ? 2.5 : 1.5}
                strokeDasharray={e.type === 'violation' ? '6 3' : e.type === 'belongs' ? '3 3' : undefined}
                opacity={e.type === 'belongs' ? 0.35 : 0.75}
                markerEnd={e.type !== 'belongs' ? undefined : undefined} />
              {e.label && (
                <text x={mx} y={my - 6} textAnchor="middle" fill={edgeColor[e.type]}
                  fontSize="9" fontFamily="monospace" fontWeight="bold"
                  stroke="#0b1121" strokeWidth="2.5" paintOrder="stroke">
                  {e.label}
                </text>
              )}
            </g>
          )
        })}

        {/* Nodes */}
        {nodes.map((n, i) => {
          const rx = nodeRx[n.type], ry = nodeRy[n.type]
          return (
            <g key={n.id}>
              {n.type === 'asn' ? (
                <circle cx={n.x} cy={n.y} r={rx} fill={nodeFill[n.type]} stroke={nodeStroke[n.type]} strokeWidth="1.5" />
              ) : n.type === 'org' ? (
                <rect x={n.x - rx} y={n.y - ry} width={rx * 2} height={ry * 2} rx="6" fill={nodeFill[n.type]} stroke={nodeStroke[n.type]} strokeWidth="1.5" />
              ) : (
                <rect x={n.x - rx} y={n.y - ry} width={rx * 2} height={ry * 2} rx="4" fill={nodeFill[n.type]} stroke={nodeStroke[n.type]} strokeWidth="1.5"
                  transform={`rotate(45 ${n.x} ${n.y})`} />
              )}
              <text x={n.x} y={n.y + (n.type === 'pattern' ? 0 : n.type === 'org' ? 1 : 1)}
                textAnchor="middle" dominantBaseline="central"
                fill={nodeTextColor[n.type]} fontSize={n.type === 'pattern' ? '8' : '9'} fontWeight="600" fontFamily="monospace">
                {n.type === 'pattern' ? '⚠' : n.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}