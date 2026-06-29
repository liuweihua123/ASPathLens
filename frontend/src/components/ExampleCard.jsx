import { useNavigate } from 'react-router-dom'

export default function ExampleCard({ example }) {
  const nav = useNavigate()
  return (
    <div className="rounded-xl border bg-white p-5">
      <h3 className="font-semibold">{example.name_en}</h3>
      <p className="text-sm text-slate-500">{example.name_zh}</p>
      <p className="mt-2 font-mono text-sm">{example.as_path}</p>
      <p className="mt-2 text-xs text-slate-600">{example.expected}</p>
      <button
        type="button"
        className="mt-3 text-sm text-accent"
        onClick={() => nav('/analyzer', { state: { path: example.as_path } })}
      >
        Load in analyzer
      </button>
    </div>
  )
}