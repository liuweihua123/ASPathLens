"""Dataset and examples API — enriched for all phases."""

from fastapi import APIRouter

from app.services.dataset_status import get_dataset_status
from app.state import data_store

router = APIRouter(tags=["dataset"])


@router.get("/api/dataset/status")
def dataset_status():
    return get_dataset_status(asrel=data_store.asrel, as2org=data_store.as2org)


EXAMPLES = [
    {
        "id": "valid-valley-free",
        "name_en": "Valid valley-free path",
        "name_zh": "合法 valley-free 路径",
        "as_path": "174 2914 3356",
        "expected": "Valley-free valid; low risk.",
    },
    {
        "id": "p2c-c2p",
        "name_en": "p2c -> c2p suspicious path",
        "name_zh": "p2c -> c2p 可疑模式",
        "as_path": "4134 4837 3356",
        "expected": "Valley-free violation: down then uphill.",
    },
    {
        "id": "p2p-c2p",
        "name_en": "p2p -> c2p route-leak-like path",
        "name_zh": "p2p -> c2p 潜在泄露模式",
        "as_path": "3356 4134 4837 9808",
        "expected": "May show leak candidate depending on CAIDA data.",
    },
    {
        "id": "prepending",
        "name_en": "AS prepending path",
        "name_zh": "AS prepending 示例",
        "as_path": "3356 4134 4134 4134 4837 9808",
        "expected": "Normalizer collapses 3x prepending.",
    },
    {
        "id": "private-asn",
        "name_en": "Private ASN warning path",
        "name_zh": "私有 ASN 警告",
        "as_path": "3356 64512 4134",
        "expected": "Warning about private ASN 64512.",
    },
    {
        "id": "path-diff",
        "name_en": "Path diff example",
        "name_zh": "路径对比示例",
        "before_path": "3356 4134 4837 9808",
        "after_path": "3356 1299 4837 9808",
        "type": "diff",
        "expected": "ASN replacement, risk delta, relationship change.",
    },
]


@router.get("/api/examples")
def examples():
    return {"examples": EXAMPLES}