import { useEffect, useState } from 'react'
import { getDatasetStatus } from '../api/client.js'
import { useLang } from '../i18n/context.jsx'
import DatasetStatusCard from '../components/DatasetStatusCard.jsx'

export default function DatasetStatus() {
  const { tr } = useLang()
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try { setData(await getDatasetStatus()) } catch (e) { setErr(e.message) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold text-white">{tr('ds.title')}</h1>
        <button onClick={load} disabled={loading} className="dk-btn-ghost">
          {loading ? tr('ds.refreshing') : tr('ds.refresh')}</button>
      </div>
      {err && <p className="text-sm text-rose-400">{err}</p>}
      {data ? <DatasetStatusCard data={data} /> : <p className="text-slate-500">{tr('asn.loading')}</p>}
    </div>
  )
}