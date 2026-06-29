"""Application state: loaded datasets."""

from __future__ import annotations

from pathlib import Path

from app.config import ASORG_RAW_DIR, ASREL_RAW_DIR, get_settings
from app.services.as2org_loader import As2OrgStore, load_as2org_from_path
from app.services.asrel_loader import AsRelStore, load_asrel_from_path
from app.services.dataset_status import _find_latest_file
from app.services.path_analyzer import AnalyzerContext, PathAnalyzerService


class DataStore:
    asrel: AsRelStore | None = None
    as2org: As2OrgStore | None = None

    def reload_from_disk(self) -> None:
        asrel_path = _find_latest_file(ASREL_RAW_DIR, "*.as-rel2.txt*")
        asorg_path = _find_latest_file(ASORG_RAW_DIR, "*.as-org2info.txt*")
        self.asrel = load_asrel_from_path(asrel_path) if asrel_path else None
        self.as2org = load_as2org_from_path(asorg_path) if asorg_path else None

    def analyzer(self) -> PathAnalyzerService:
        ctx = AnalyzerContext(
            asrel=self.asrel,
            as2org=self.as2org,
            asrel_label=self.asrel.stats.file_name if self.asrel else "not loaded",
            as2org_label=self.as2org.stats.file_name if self.as2org else "not loaded",
        )
        return PathAnalyzerService(ctx)


data_store = DataStore()