from __future__ import annotations

import json
from pathlib import Path

from pipeline.ingest.ingest_pipeline import MasterIngestionAgent


def main() -> None:
    agent = MasterIngestionAgent(
        raw_root=Path("data/raw"),
        processed_root=Path("data/processed"),
        parquet_root=Path("data/parquet"),
        log_path=Path("pipeline/ingest/ingestion.log"),
    )
    unified, results, checks, quality = agent.run()

    summary = {
        "rows_written": int(len(unified)),
        "files_total": len(results),
        "files_processed": sum(1 for r in results if r.status == "processed"),
        "files_failed": sum(1 for r in results if r.status == "failed"),
        "verification": checks,
        "quality": quality,
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
