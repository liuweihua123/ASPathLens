"""Python SDK facade."""

from __future__ import annotations

from pathlib import Path

from app.services.as2org_loader import load_as2org_from_path
from app.services.asrel_loader import load_asrel_from_path
from app.services.path_analyzer import AnalyzerContext, PathAnalyzerService
from app.services.path_diff import diff_paths


class ASPathAnalyzer:
    def __init__(self, service: PathAnalyzerService):
        self._service = service

    @classmethod
    def from_files(cls, asrel_path: str | Path, as2org_path: str | Path) -> "ASPathAnalyzer":
        return cls(
            PathAnalyzerService(
                AnalyzerContext(
                    asrel=load_asrel_from_path(asrel_path),
                    as2org=load_as2org_from_path(as2org_path),
                )
            )
        )

    def analyze(self, as_path: str, use_normalized: bool = True) -> dict:
        return self._service.analyze(as_path, use_normalized)

    def batch_analyze(self, paths: list[str]) -> list[dict]:
        return [self.analyze(p) for p in paths]

    def diff(self, before: str, after: str) -> dict:
        return diff_paths(self._service, before, after)