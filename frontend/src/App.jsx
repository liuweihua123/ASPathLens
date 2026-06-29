import { Link, Route, Routes, useLocation } from 'react-router-dom'
import { useLang } from './i18n/context.jsx'
import Home from './pages/Home.jsx'
import PathAnalyzer from './pages/PathAnalyzer.jsx'
import PathDiff from './pages/PathDiff.jsx'
import ASNExplorer from './pages/ASNExplorer.jsx'
import DatasetStatus from './pages/DatasetStatus.jsx'
import DatasetDiff from './pages/DatasetDiff.jsx'
import BatchAnalyzer from './pages/BatchAnalyzer.jsx'
import PatternSearch from './pages/PatternSearch.jsx'
import ExampleGallery from './pages/ExampleGallery.jsx'
import APIPlayground from './pages/APIPlayground.jsx'
import KnowledgeGraph from './pages/KnowledgeGraph.jsx'

export default function App() {
  const { lang, toggle, tr } = useLang()
  const { pathname } = useLocation()
  const isHome = pathname === '/'

  const nav = [
    { to: '/analyzer', key: 'nav.analyzer' },
    { to: '/diff', key: 'nav.diff' },
    { to: '/asn', key: 'nav.asn' },
    { to: '/kg', key: 'nav.kg' },
    { to: '/batch', key: 'nav.batch' },
    { to: '/pattern', key: 'nav.pattern' },
    { to: '/dataset', key: 'nav.dataset' },
    { to: '/dataset-diff', key: 'nav.datasetDiff' },
    { to: '/examples', key: 'nav.examples' },
    { to: '/api-docs', key: 'nav.api' },
  ]

  return (
    <div className="min-h-screen bg-[#060a14] text-slate-200">
      {/* ---- Header (always dark) ---- */}
      <header className={isHome
        ? 'fixed inset-x-0 top-0 z-50 border-b border-sky-500/10 bg-[#060a14]/80 backdrop-blur-lg'
        : 'sticky top-0 z-50 border-b border-sky-500/10 bg-[#060a14]/90 backdrop-blur-lg'}>
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-4 py-3">
          <Link to="/" className="text-xl font-bold tracking-tight text-white">
            AS<span className="text-sky-400">Path</span>Lens
          </Link>
          <nav className="flex flex-wrap gap-0.5 text-[13px] text-slate-400">
            {nav.map((item) => (
              <Link key={item.to} to={item.to}
                className="rounded px-2 py-1 transition hover:bg-white/5 hover:text-sky-300">
                {tr(item.key)}
              </Link>
            ))}
          </nav>
          <button type="button" onClick={toggle}
            className="ml-auto rounded-full border border-sky-500/30 px-3 py-1 text-xs font-medium text-sky-400 transition hover:bg-sky-500/10"
            title={lang === 'en' ? '切换中文' : 'Switch to English'}>
            {lang === 'en' ? '中文' : 'EN'}
          </button>
        </div>
      </header>

      {/* ---- Main ---- */}
      {isHome ? (
        <main className="pt-14"><Home /></main>
      ) : (
        <main className="mx-auto max-w-7xl px-4 py-8">
          <Routes>
            <Route path="/analyzer" element={<PathAnalyzer />} />
            <Route path="/diff" element={<PathDiff />} />
            <Route path="/asn" element={<ASNExplorer />} />
            <Route path="/batch" element={<BatchAnalyzer />} />
            <Route path="/pattern" element={<PatternSearch />} />
            <Route path="/dataset" element={<DatasetStatus />} />
            <Route path="/dataset-diff" element={<DatasetDiff />} />
            <Route path="/examples" element={<ExampleGallery />} />
            <Route path="/kg" element={<KnowledgeGraph />} />
            <Route path="/api-docs" element={<APIPlayground />} />
          </Routes>
        </main>
      )}

      {/* ---- Footer ---- */}
      {!isHome && (
        <footer className="border-t border-sky-500/10 bg-[#060a14] py-6 text-center text-xs text-slate-600">
          {tr('footer.disclaimer')}
        </footer>
      )}
    </div>
  )
}