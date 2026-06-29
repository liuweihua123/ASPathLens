# ASPathLens

A relationship-aware AS path analyzer and lightweight AS knowledge graph for BGP policy research.

Paste an AS path or ASN. ASPathLens explains AS ownership, AS relationships, valley-free policy, potential route-leak patterns, and AS neighborhood topology using CAIDA ASRelationship, AS2Org, and ASRank.

Use it as a **Web UI**, **REST API**, **CLI tool**, or **Python library**.

**中文：** ASPathLens 是一个面向 BGP 路由研究的 AS 路径分析器和轻量级 AS 知识图谱工具。它基于 CAIDA AS Relationship、AS2Org 和 ASRank，对输入的 AS Path 进行商业关系标注、组织归属分析、valley-free 检测、same-org 豁免、潜在 route leak 模式识别、可解释风险评分和 AS 邻域知识图谱可视化。

> **ASPathLens does not confirm BGP hijacks or route leaks.**
> It only explains AS path **policy suspiciousness** using AS relationships and organization mappings.
> 该工具只能判断 AS 商业关系角度下的路径策略可疑性，不能单独证明 BGP 劫持、真实路由泄露事件或攻击者身份。

---

## Quick start

### 1. Install backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Download CAIDA data (required)

```bash
python scripts/download_asrel.py    # ~30 MB, AS Relationship serial-2
python scripts/download_as2org.py   # ~4 MB, AS2Org
python scripts/parse_asrel.py       # → SQLite
python scripts/parse_as2org.py      # → SQLite

# or all at once:
python scripts/update_all.py
```

### 3. Start backend

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Start frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker compose up --build
```

Data mount: `./backend/data:/app/data`

---

## Features

| Page | Description | Phase |
|------|-------------|-------|
| **Path Analyzer** | Single path analysis: org, relationships, valley-free, leak candidate, risk score | ✅ MVP |
| **Path Diff** | Compare before/after paths: ASN changes, risk delta, relationship diff | ✅ |
| **ASN Explorer** | Per-ASN profile: org, local counts, same-org ASNs, ASRank enhancement | ✅ |
| **Batch Analyzer** | CSV/TXT/JSON batch analysis: stats, top patterns/suspicious ASNs, per-row results, CSV/JSON export | ✅ |
| **Pattern Search** | Search for relationship patterns (e.g. `p2p → c2p`) across paths | ✅ |
| **Dataset Status** | Loaded data counts, ASRank health, data readiness | ✅ |
| **Dataset Diff** | Compare two ASRelationship/AS2Org versions | ✅ |
| **Example Gallery** | One-click example loading (valid, suspicious, prepending, diff, etc.) | ✅ |
| **API Playground** | Full REST API reference with curl/Python examples | ✅ |
| **Knowledge Graph** | ASN neighborhood / Path subgraph / Org graph / Pattern graph with Cytoscape.js | ✅ |
| **Org Explorer** | Org member list and neighbor stats (backend ready) | API only |

---

## REST API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/path/normalize` | Normalize AS path |
| POST | `/api/path/analyze` | Full path analysis |
| POST | `/api/path/diff` | Compare two paths |
| POST | `/api/path/repair-hint` | Repair hint for violations |
| POST | `/api/batch/analyze` | Batch via file upload |
| POST | `/api/batch/analyze/json` | Batch via JSON body |
| POST | `/api/pattern/search` | Pattern search |
| POST | `/api/report/export` | Export report (JSON/CSV/Markdown) |
| GET | `/api/asn/{asn}` | ASN explorer |
| GET | `/api/dataset/status` | Dataset status |
| GET | `/api/dataset/diff` | Dataset version diff |
| GET | `/api/dataset/changes/{asn}` | ASN changes between versions |
| GET | `/api/dataset/versions` | List available versions |
| GET | `/api/examples` | Example gallery |
| GET | `/api/report/{report_id}` | Retrieve saved report |
| GET | `/api/health` | Health check |
| GET | `/api/kg/asn/{asn}` | ASN neighborhood knowledge graph |
| POST | `/api/kg/path-subgraph` | Path subgraph (nodes + edges from analysis) |
| GET | `/api/kg/org/{org_id}` | Organization knowledge graph |
| GET | `/api/kg/pattern/{pattern}` | Violation pattern graph |
| POST | `/api/kg/export` | Export graph (JSON/Cytoscape/GraphML/Cypher) |

```bash
curl -X POST http://127.0.0.1:8000/api/path/analyze \
  -H "Content-Type: application/json" \
  -d '{"as_path":"3356 4134 4837 9808","use_normalized":true}'
```

---

## CLI

```bash
cd backend
pip install -e .

aspathlens analyze "3356 4134 4837 9808"
aspathlens analyze "3356 4134 4837 9808" --format json
aspathlens diff "3356 4134 4837 9808" "3356 1299 4837 9808"
aspathlens batch paths.csv --output result.csv
aspathlens asn 4134
aspathlens dataset status
aspathlens dataset diff --old 20260501 --new 20260601
```

---

## Python SDK

```python
from app.sdk import ASPathAnalyzer

analyzer = ASPathAnalyzer.from_files(
    asrel_path="data/raw/as_relationship/20260601.as-rel2.txt.bz2",
    as2org_path="data/raw/as_org/20260601.as-org2info.txt.gz",
)

result = analyzer.analyze("3356 4134 4837 9808")
print(result["risk_score"]["score"], result["valley_free"]["is_valid"])

diff = analyzer.diff("3356 4134 4837 9808", "3356 1299 4837 9808")
print(diff["diff"]["risk_delta"])

results = analyzer.batch_analyze(["3356 4134 4837 9808", "174 2914 3356"])
```

---

## Data sources

| Source | URL | Usage |
|--------|-----|-------|
| CAIDA AS Relationship (serial-2) | https://data.caida.org/datasets/as-relationships/serial-2/ | Core: per-hop relationship labels |
| CAIDA AS2Org | https://data.caida.org/datasets/as-organizations/ | Core: ASN → org mapping, same-org detection |
| CAIDA ASRank API | https://api.asrank.caida.org/v2/graphql | Enhancement only (ASN Explorer, Org Explorer) |

Only these three sources are used. No RouteViews, RIPE RIS, BGPStream, RPKI, IRR, PeeringDB, or threat intelligence data.

---

## Auto-update

Suggested schedule: AS Relationship monthly; AS2Org monthly/quarterly.

**Cron:**
```bash
0 3 2 * * /usr/bin/python3 /path/to/backend/scripts/update_all.py >> logs/update.log 2>&1
```

**GitHub Actions:** `.github/workflows/update-data.yml`

---

## Knowledge Graph

ASPathLens provides a lightweight AS knowledge graph for BGP policy research.

It connects ASNs, organizations, countries, AS relationships, AS paths, path segments, and violation patterns into a navigable property graph.

**Modes:**
- **ASN Neighborhood** — explore providers, peers, customers, same-org ASes, organization node, country node
- **Path Subgraph** — visualize an AS path as a knowledge graph with violation highlights
- **Organization Graph** — explore org members, internal connections, external neighbors
- **Pattern Graph** — visualize which ASNs are frequently involved in specific violation patterns

The graph is built on-demand from loaded CAIDA ASRelationship + AS2Org data. No Neo4j required.

Export formats: JSON, Cytoscape.js JSON, GraphML, Cypher (optional Neo4j import).

---

## Tests

```bash
cd backend
pytest -q   # 33 tests
```

---

## Screenshots

- Path Analyzer: paste `3356 4134 4837 9808` → see org names, relationships, valley-free, risk score
- Path Diff: compare `3356 4134 4837 9808` vs `3356 1299 4837 9808` → risk delta +90
- Dataset Status: real-time edge/ASN counts from parsed CAIDA data
- Knowledge Graph: ASN neighborhood with providers/peers/highlighted violations via Cytoscape.js

---

## Important notices

- ASPathLens does **not** confirm BGP hijacks or route leaks.
- It only measures **AS path policy suspiciousness** using relationship and organization data.
- ASRelationship is inferred data — version changes can affect analysis results.
- `unknown` edges reduce confidence but are not violations.
- Same-org edges are weaker evidence for violations.

---

## Citation

Please cite CAIDA datasets:

- [CAIDA AS Relationships Dataset](https://www.caida.org/catalog/datasets/as-relationships/)
- [CAIDA AS Organizations Dataset](https://www.caida.org/catalog/datasets/as-organizations/)
- [CAIDA ASRank](https://asrank.caida.org/)

---

## License

MIT — see [LICENSE](LICENSE).

---

## GitHub

Suggested repo name: `as-path-lens`
Description: *Explain AS paths with CAIDA AS Relationship, AS2Org, and ASRank. Includes AS knowledge graph.*
Topics: `bgp`, `routing`, `as-path`, `internet-measurement`, `caida`, `as-relationship`, `asrank`, `network-security`, `route-leak`, `valley-free`, `internet-topology`, `knowledge-graph`, `graph-visualization`, `cytoscape`, `property-graph`, `as-graph`