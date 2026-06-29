"""FastAPI application entry."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis_api, asn_api, batch_api, dataset_api, dataset_diff_api, kg_api, path_api
from app.config import get_settings
from app.db.database import init_db
from app.state import data_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    data_store.reload_from_disk()
    print(
        f"[ASPathLens] asrel edges: {data_store.asrel.stats.edge_count if data_store.asrel else 0}, "
        f"as2org ASNs: {data_store.as2org.stats.asn_count if data_store.as2org else 0}"
    )
    yield


app = FastAPI(
    title="ASPathLens",
    description="Relationship-aware AS path analyzer for BGP policy research.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(path_api.router)
app.include_router(batch_api.router)
app.include_router(analysis_api.router)
app.include_router(dataset_diff_api.router)
app.include_router(dataset_api.router)
app.include_router(kg_api.router)
app.include_router(asn_api.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ASPathLens"}