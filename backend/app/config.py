"""Application configuration and CAIDA data source URLs."""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project paths
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
ASREL_RAW_DIR = RAW_DIR / "as_relationship"
ASORG_RAW_DIR = RAW_DIR / "as_org"
TMP_DIR = DATA_DIR / "tmp"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "aspathlens.db"

# CAIDA URLs (serial-2 ASRelationship, AS2Org, ASRank)
ASREL_SERIAL2_DIR = "https://data.caida.org/datasets/as-relationships/serial-2/"
ASREL_LATEST_EXAMPLE = (
    "https://data.caida.org/datasets/as-relationships/serial-2/20260601.as-rel2.txt.bz2"
)
AS2ORG_DIR = "https://data.caida.org/datasets/as-organizations/"
AS2ORG_LATEST_URL = (
    "https://data.caida.org/datasets/as-organizations/latest.as-org2info.txt.gz"
)
AS2ORG_LATEST_EXAMPLE = (
    "https://data.caida.org/datasets/as-organizations/20260601.as-org2info.txt.gz"
)
ASRANK_GRAPHQL_URL = "https://api.asrank.caida.org/v2/graphql"
ASRANK_GRAPHIQL_URL = "https://api.asrank.caida.org/v2/graphiql"
ASRANK_RESTFUL_URL = "https://api.asrank.caida.org/v2/restful/"
ASRANK_DOCS_URL = "https://api.asrank.caida.org/v2/docs"
ASRANK_CACHE_TTL_DAYS = 7
ASRANK_REQUEST_TIMEOUT_SEC = 15

# Private / reserved ASN ranges (RFC 6996, etc.)
PRIVATE_ASN_16BIT = range(64512, 65535)
PRIVATE_ASN_32BIT = range(4200000000, 4294967295)
MAX_ASN = 4294967295


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ASPathLens"
    debug: bool = False
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_token: str = ""  # optional for POST /api/dataset/update
    active_asrel_version: str = ""
    active_as2org_version: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()