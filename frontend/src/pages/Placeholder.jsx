export default function Placeholder({ title, phase }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-2 text-slate-600">Planned for Phase {phase}. API stubs and service modules are reserved in the backend.</p>
    </div>
  )
}