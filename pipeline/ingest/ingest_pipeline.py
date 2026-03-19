from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


CANONICAL_SCHEMA = [
    "timestamp",
    "route_id",
    "vehicle_type",
    "location",
    "incident_code",
    "incident_desc",
    "min_delay",
    "min_gap",
    "source_file",
]

COLUMN_ALIASES = {
    "date": "date",
    "report date": "date",
    "time": "time",
    "route": "route_id",
    "line": "route_id",
    "route_id": "route_id",
    "station": "location",
    "location": "location",
    "code": "incident_code",
    "incident": "incident_code",
    "incident id": "incident_code",
    "min delay": "min_delay",
    " delay": "min_delay",
    "delay": "min_delay",
    " min delay": "min_delay",
    "min gap": "min_gap",
    "gap": "min_gap",
    "vehicle": "vehicle",
    "route_type": "route_type",
    "date_col": "date",
}


@dataclass
class IngestionResult:
    file_path: Path
    dataset_type: str
    rows_in: int
    rows_out: int
    status: str
    message: str = ""


class FileScannerAgent:
    def __init__(self, raw_root: Path) -> None:
        self.raw_root = raw_root

    def scan_csv_files(self) -> list[Path]:
        return sorted(path for path in self.raw_root.rglob("*.csv") if path.is_file())


class DatasetClassifierAgent:
    def classify(self, file_path: Path, columns: list[str]) -> str:
        lowered = [c.strip().lower() for c in columns]
        path_str = str(file_path).lower()
        if "subway" in path_str or "station" in lowered or "code" in lowered:
            return "subway"
        if "bus" in path_str or "route" in lowered:
            return "bus"
        if "gtfs" in path_str or any(col in lowered for col in ["trip_id", "stop_id", "shape_id", "service_id"]):
            return "gtfs"
        return "unknown"


class SubwayLookupAgent:
    def __init__(self, raw_root: Path, logger: logging.Logger) -> None:
        self.raw_root = raw_root
        self.logger = logger
        self.lookup: dict[str, str] = {}

    def load(self) -> dict[str, str]:
        candidates = [
            p
            for p in self.raw_root.rglob("*.csv")
            if "code" in p.name.lower() and "subway" in str(p).lower()
        ]
        if not candidates:
            self.logger.warning("No subway lookup CSV found.")
            self.lookup = {}
            return self.lookup

        chosen = sorted(candidates)[0]
        df = pd.read_csv(chosen, dtype=str, encoding="utf-8-sig")
        df.columns = [c.strip().lower() for c in df.columns]

        code_col = "code" if "code" in df.columns else df.columns[0]
        desc_col = "description" if "description" in df.columns else ("desc" if "desc" in df.columns else df.columns[-1])

        lookup = (
            df[[code_col, desc_col]]
            .dropna(how="any")
            .assign(**{code_col: lambda d: d[code_col].astype(str).str.strip()})
            .drop_duplicates(subset=[code_col])
            .set_index(code_col)[desc_col]
            .to_dict()
        )
        self.lookup = lookup
        self.logger.info("Loaded %s subway code mappings from %s", len(lookup), chosen)
        return lookup


class TransformerAgent:
    def __init__(self, subway_lookup: dict[str, str]) -> None:
        self.subway_lookup = subway_lookup

    @staticmethod
    def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        rename_map: dict[str, str] = {}
        for col in df.columns:
            key = col.strip().lower()
            canonical = COLUMN_ALIASES.get(key)
            if canonical:
                rename_map[col] = canonical
        out = df.rename(columns=rename_map).copy()
        out.columns = [c.strip() for c in out.columns]
        return out

    @staticmethod
    def _build_timestamp(df: pd.DataFrame) -> pd.Series:
        if "date" not in df.columns and "time" not in df.columns:
            return pd.Series([pd.NaT] * len(df), index=df.index)
        date_part = df.get("date", pd.Series([None] * len(df), index=df.index)).astype(str).str.strip()
        time_part = df.get("time", pd.Series(["00:00:00"] * len(df), index=df.index)).astype(str).str.strip()
        raw = (date_part + " " + time_part).str.strip()
        ts = pd.to_datetime(raw, errors="coerce", infer_datetime_format=True)
        return ts

    @staticmethod
    def _safe_numeric(series: pd.Series | None, index: pd.Index) -> pd.Series:
        if series is None:
            return pd.Series([pd.NA] * len(index), index=index, dtype="Float64")
        return pd.to_numeric(series, errors="coerce").astype("Float64")

    @staticmethod
    def _vehicle_type(dataset_type: str, df: pd.DataFrame) -> pd.Series:
        if dataset_type in {"bus", "subway"}:
            return pd.Series([dataset_type] * len(df), index=df.index)
        if "route_type" in df.columns:
            mapped = df["route_type"].astype(str).map({"1": "subway", "3": "bus"}).fillna("unknown")
            return mapped
        return pd.Series(["unknown"] * len(df), index=df.index)

    def transform(self, df: pd.DataFrame, dataset_type: str, source_file: str) -> pd.DataFrame:
        ndf = self._normalize_columns(df)

        out = pd.DataFrame(index=ndf.index)
        out["timestamp"] = self._build_timestamp(ndf)
        out["route_id"] = ndf.get("route_id", pd.Series([pd.NA] * len(ndf), index=ndf.index)).astype("string")
        out["vehicle_type"] = self._vehicle_type(dataset_type, ndf).astype("string")

        location_series = ndf.get("location", pd.Series([pd.NA] * len(ndf), index=ndf.index)).astype("string")
        location_series = location_series.fillna("unknown").replace({"": "unknown", "nan": "unknown", "None": "unknown"})
        out["location"] = location_series

        code_series = ndf.get("incident_code", pd.Series([pd.NA] * len(ndf), index=ndf.index)).astype("string")
        out["incident_code"] = code_series

        if dataset_type == "subway":
            out["incident_desc"] = code_series.astype(str).str.strip().map(self.subway_lookup).astype("string")
        else:
            out["incident_desc"] = pd.Series([pd.NA] * len(ndf), index=ndf.index, dtype="string")

        out["min_delay"] = self._safe_numeric(ndf.get("min_delay"), ndf.index)
        out["min_gap"] = self._safe_numeric(ndf.get("min_gap"), ndf.index)
        out["source_file"] = source_file

        for col in CANONICAL_SCHEMA:
            if col not in out.columns:
                out[col] = pd.NA

        return out[CANONICAL_SCHEMA]


class VerificationAgent:
    def verify(self, file_count: int, processed_count: int, failed_count: int, parquet_root: Path) -> list[str]:
        checks: list[str] = []
        checks.append(f"files_discovered={file_count}")
        checks.append(f"files_processed={processed_count}")
        checks.append(f"files_failed={failed_count}")

        parquet_parts = list(parquet_root.rglob("*.parquet"))
        checks.append(f"parquet_files={len(parquet_parts)}")

        return checks


class DataQualityAgent:
    def summarize(self, df: pd.DataFrame) -> dict[str, Any]:
        subway = df[df["vehicle_type"] == "subway"]
        mapped = subway["incident_desc"].notna().sum() if not subway.empty else 0
        return {
            "rows": int(len(df)),
            "unknown_locations": int((df["location"] == "unknown").sum()),
            "subway_rows": int(len(subway)),
            "subway_codes_mapped": int(mapped),
        }


class MasterIngestionAgent:
    def __init__(
        self,
        raw_root: Path = Path("data/raw"),
        processed_root: Path = Path("data/processed"),
        parquet_root: Path = Path("data/parquet"),
        log_path: Path = Path("pipeline/ingest/ingestion.log"),
    ) -> None:
        self.raw_root = raw_root
        self.processed_root = processed_root
        self.parquet_root = parquet_root
        self.log_path = log_path

        self.processed_root.mkdir(parents=True, exist_ok=True)
        self.parquet_root.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
            handlers=[logging.FileHandler(self.log_path), logging.StreamHandler()],
        )
        self.logger = logging.getLogger("master_ingestion_agent")

        self.scanner = FileScannerAgent(raw_root)
        self.classifier = DatasetClassifierAgent()
        self.lookup_agent = SubwayLookupAgent(raw_root, self.logger)
        self.verifier = VerificationAgent()
        self.quality_agent = DataQualityAgent()

    def run(self) -> tuple[pd.DataFrame, list[IngestionResult], list[str], dict[str, Any]]:
        files = self.scanner.scan_csv_files()
        self.logger.info("Discovered %s CSV files under %s", len(files), self.raw_root)

        subway_lookup = self.lookup_agent.load()
        transformer = TransformerAgent(subway_lookup)

        all_frames: list[pd.DataFrame] = []
        results: list[IngestionResult] = []

        for file_path in files:
            rel = str(file_path.relative_to(self.raw_root))
            try:
                df = pd.read_csv(file_path, dtype=str, encoding="utf-8-sig", on_bad_lines="skip")
                dataset_type = self.classifier.classify(file_path, list(df.columns))

                if df.empty or dataset_type == "unknown":
                    results.append(IngestionResult(file_path, dataset_type, len(df), 0, "skipped", "unknown or empty dataset"))
                    self.logger.warning("Skipped %s (%s)", rel, dataset_type)
                    continue

                cleaned = transformer.transform(df, dataset_type, rel)
                output_path = self.processed_root / (file_path.stem + "_cleaned.csv")
                cleaned.to_csv(output_path, index=False)

                all_frames.append(cleaned)
                results.append(IngestionResult(file_path, dataset_type, len(df), len(cleaned), "processed"))
                self.logger.info("Processed %s as %s rows=%s", rel, dataset_type, len(cleaned))
            except Exception as exc:
                results.append(IngestionResult(file_path, "unknown", 0, 0, "failed", str(exc)))
                self.logger.exception("Failed processing %s", rel)

        unified = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame(columns=CANONICAL_SCHEMA)

        unified["year"] = unified["timestamp"].dt.year.astype("Int64")
        unified["year"] = unified["year"].fillna(-1).astype(int)

        unified.to_csv(self.processed_root / "all_data_cleaned.csv", index=False)
        unified.to_parquet(self.parquet_root, index=False, partition_cols=["year", "vehicle_type"])

        checks = self.verifier.verify(
            file_count=len(files),
            processed_count=sum(1 for r in results if r.status == "processed"),
            failed_count=sum(1 for r in results if r.status == "failed"),
            parquet_root=self.parquet_root,
        )

        quality = self.quality_agent.summarize(unified)

        self.logger.info("Verification: %s", checks)
        self.logger.info("Data quality summary: %s", quality)

        return unified, results, checks, quality
