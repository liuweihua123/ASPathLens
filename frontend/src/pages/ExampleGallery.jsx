import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getExamples } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'

export default function ExampleGallery() {
  const { tr, lang } = useLang()
  const [examples, setExamples] = useState([])
  const nav = useNavigate()

  useEffect(() => { getExamples().then(d => setExamples(d.examples || [])) }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">{tr('eg.title')}</h1>
      <p className="text-sm text-slate-400">{tr('eg.desc')}</p>
      <div className="grid gap-4 md:grid-cols-2">
        {examples.map(ex => (
          <div key={ex.id} className="dk-card-hover p-5">
            <h3 className="font-semibold text-white">{ex.name_en}</h3>
            <p className="text-xs text-slate-500">{ex.name_zh}</p>
            {ex.type === 'diff' ? (
              <p className="mt-2 font-mono text-xs text-sky-300/80">Before: {ex.before_path}<br />After: {ex.after_path}</p>
            ) : (
              <p className="mt-2 font-mono text-sm text-sky-300/80">{ex.as_path}</p>
            )}
            <p className="mt-2 text-xs text-slate-400">{ex.expected}</p>
            <button onClick={() => ex.type === 'diff' ? nav('/diff', { state: { before: ex.before_path, after: ex.after_path } }) : nav('/analyzer', { state: { path: ex.as_path } })}
              className="mt-3 text-sm text-sky-400 hover:text-sky-300">
              {ex.type === 'diff' ? tr('eg.loadDiff') : tr('eg.loadAnalyzer')}</button>
          </div>
        ))}
      </div>
    </div>
  )
}