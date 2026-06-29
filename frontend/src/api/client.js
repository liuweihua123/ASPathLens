import axios from 'axios'

const client = axios.create({ baseURL: '' })

// ---- Path ----
export async function normalizePath(asPath) {
  const { data } = await client.post('/api/path/normalize', { as_path: asPath })
  return data
}

export async function analyzePath(asPath, useNormalized = true) {
  const { data } = await client.post('/api/path/analyze', {
    as_path: asPath,
    use_normalized: useNormalized,
  })
  return data
}

export async function diffPaths(beforePath, afterPath) {
  const { data } = await client.post('/api/path/diff', {
    before_path: beforePath,
    after_path: afterPath,
    use_normalized: true,
  })
  return data
}

export async function getRepairHint(asPath) {
  const { data } = await client.post('/api/path/repair-hint', { as_path: asPath })
  return data
}

// ---- Batch ----
export async function batchAnalyzeFile(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/api/batch/analyze', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function batchAnalyzeJson(paths) {
  const { data } = await client.post('/api/batch/analyze/json', { paths })
  return data
}

// ---- Pattern ----
export async function searchPattern(pattern, paths) {
  const { data } = await client.post('/api/pattern/search', { pattern, paths })
  return data
}

// ---- ASN / Org ----
export async function getAsnProfile(asn) {
  const { data } = await client.get(`/api/asn/${asn}`)
  return data
}

// ---- Dataset ----
export async function getDatasetStatus() {
  const { data } = await client.get('/api/dataset/status')
  return data
}

export async function getDatasetVersions() {
  const { data } = await client.get('/api/dataset/versions')
  return data
}

export async function getDatasetDiff(dataset, oldVersion, newVersion) {
  const { data } = await client.get('/api/dataset/diff', {
    params: { dataset, old_version: oldVersion, new_version: newVersion },
  })
  return data
}

export async function getAsnChanges(asn, oldV, newV) {
  const { data } = await client.get(`/api/dataset/changes/${asn}`, {
    params: { version_old: oldV, version_new: newV },
  })
  return data
}

// ---- Report ----
export async function exportReport(result, format = 'markdown') {
  const { data } = await client.post('/api/report/export', { result, report_type: 'single', format })
  return data
}

// ---- Knowledge Graph ----
export async function getKgAsn(asn, opts = {}) {
  const params = { depth: 1, limit: 50, relationship: 'all', include_org: true, include_asrank: true, ...opts }
  const { data } = await client.get(`/api/kg/asn/${asn}`, { params })
  return data
}

export async function getKgPath(asPath) {
  const { data } = await client.post('/api/kg/path-subgraph', { as_path: asPath, use_normalized: true })
  return data
}

export async function getKgOrg(orgId, limit = 100) {
  const { data } = await client.get(`/api/kg/org/${encodeURIComponent(orgId)}`, { params: { limit } })
  return data
}

export async function getKgPattern(pattern) {
  const { data } = await client.get(`/api/kg/pattern/${encodeURIComponent(pattern)}`)
  return data
}

export async function exportKg(graph, format = 'json') {
  const { data } = await client.post('/api/kg/export', { graph, format })
  return data
}

// ---- Examples ----
export async function getExamples() {
  const { data } = await client.get('/api/examples')
  return data
}