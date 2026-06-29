import { useLang } from '../i18n/context.jsx'

const endpoints = [
  { method: 'POST', path: '/api/path/analyze', desc: { en: 'Analyze a single AS path', zh: '分析单条 AS 路径' },
    curl: `curl -X POST http://127.0.0.1:8000/api/path/analyze \\\n  -H "Content-Type: application/json" \\\n  -d '{"as_path":"3356 4134 4837 9808","use_normalized":true}'`,
    python: `import requests\nr = requests.post("http://127.0.0.1:8000/api/path/analyze",\n    json={"as_path": "3356 4134 4837 9808", "use_normalized": True})\nprint(r.json())` },
  { method: 'POST', path: '/api/path/normalize', desc: { en: 'Normalize AS path', zh: '规范化 AS 路径' },
    curl: `curl -X POST http://127.0.0.1:8000/api/path/normalize \\\n  -H "Content-Type: application/json" \\\n  -d '{"as_path":"3356 4134 4134 4837"}'`,
    python: `import requests\nr = requests.post("http://127.0.0.1:8000/api/path/normalize",\n    json={"as_path": "3356 4134 4134 4837"})\nprint(r.json())` },
  { method: 'POST', path: '/api/path/diff', desc: { en: 'Compare two paths', zh: '对比两条路径' },
    curl: `curl -X POST http://127.0.0.1:8000/api/path/diff \\\n  -H "Content-Type: application/json" \\\n  -d '{"before_path":"3356 4134","after_path":"3356 1299"}'`,
    python: `import requests\nr = requests.post("http://127.0.0.1:8000/api/path/diff",\n    json={"before_path": "3356 4134", "after_path": "3356 1299"})\nprint(r.json())` },
  { method: 'POST', path: '/api/batch/analyze/json', desc: { en: 'Batch analyze (JSON)', zh: 'JSON 批量分析' },
    curl: `curl -X POST http://127.0.0.1:8000/api/batch/analyze/json \\\n  -H "Content-Type: application/json" \\\n  -d '{"paths":["3356 4134 4837","174 2914 3356"]}'`,
    python: `import requests\nr = requests.post("http://127.0.0.1:8000/api/batch/analyze/json",\n    json={"paths": ["3356 4134 4837", "174 2914 3356"]})\nprint(r.json())` },
  { method: 'GET', path: '/api/asn/{asn}', desc: { en: 'ASN explorer', zh: 'ASN 探索' },
    curl: 'curl http://127.0.0.1:8000/api/asn/4134',
    python: 'import requests\nr = requests.get("http://127.0.0.1:8000/api/asn/4134")\nprint(r.json())' },
  { method: 'GET', path: '/api/kg/asn/{asn}', desc: { en: 'ASN neighborhood graph', zh: 'ASN 邻域图谱' },
    curl: 'curl http://127.0.0.1:8000/api/kg/asn/4134?limit=20',
    python: 'import requests\nr = requests.get("http://127.0.0.1:8000/api/kg/asn/4134",\n    params={"limit": 20})\nprint(len(r.json()["nodes"]), "nodes")' },
  { method: 'GET', path: '/api/dataset/status', desc: { en: 'Dataset status', zh: '数据状态' },
    curl: 'curl http://127.0.0.1:8000/api/dataset/status',
    python: 'import requests\nr = requests.get("http://127.0.0.1:8000/api/dataset/status")\nprint(r.json())' },
  { method: 'GET', path: '/api/dataset/diff', desc: { en: 'Dataset version diff', zh: '数据版本对比' },
    curl: 'curl "http://127.0.0.1:8000/api/dataset/diff?dataset=as_relationship&old_version=20260501&new_version=20260601"',
    python: `import requests\nr = requests.get("http://127.0.0.1:8000/api/dataset/diff",\n    params={"dataset": "as_relationship", "old_version": "20260501", "new_version": "20260601"})\nprint(r.json())` },
]

export default function APIPlayground() {
  const { tr, lang } = useLang()
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('api.title')}</h1>
      <p className="text-sm text-slate-400">{tr('api.desc')} <a href="/docs" className="text-sky-400 underline">{tr('api.swagger')}</a></p>
      <div className="space-y-4">
        {endpoints.map(ep => (
          <div key={ep.path + ep.method} className="dk-card p-5">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded px-2 py-0.5 text-xs font-bold ${ep.method === 'GET' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-sky-500/15 text-sky-400'}`}>{ep.method}</span>
              <code className="font-mono text-sm text-sky-300">{ep.path}</code>
            </div>
            <p className="mt-2 text-sm text-slate-400">{ep.desc[lang] || ep.desc.en}</p>
            <details className="mt-3">
              <summary className="cursor-pointer text-sm font-medium text-sky-400">{tr('api.showExamples')}</summary>
              <div className="mt-2 grid gap-3 md:grid-cols-2">
                <div><p className="text-xs font-medium text-slate-500">curl</p>
                  <pre className="mt-1 overflow-x-auto rounded-lg bg-[#0b1121] p-3 text-xs text-slate-300">{ep.curl}</pre></div>
                <div><p className="text-xs font-medium text-slate-500">Python</p>
                  <pre className="mt-1 overflow-x-auto rounded-lg bg-[#0b1121] p-3 text-xs text-slate-300">{ep.python}</pre></div>
              </div>
            </details>
          </div>
        ))}
      </div>
    </div>
  )
}