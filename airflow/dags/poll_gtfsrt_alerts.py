from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

REPO_ROOT = Path(os.getenv("TTC_PULSE_HOME", str(Path(__file__).resolve().parents[2])))
PYTHON_BIN = os.getenv("TTC_PULSE_PYTHON", "python")
GTFSRT_URL = os.getenv("GTFSRT_ALERTS_URL", "")


def _run_script(script_relative_path: str, extra_args: str = "") -> str:
    script_path = REPO_ROOT / script_relative_path
    suffix = f" {extra_args}" if extra_args else ""
    return f'"{PYTHON_BIN}" "{script_path}"{suffix}'


default_args = {
    "owner": "ttc_pulse",
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="poll_gtfsrt_alerts",
    description="30-min side-car pipeline for GTFS-RT service alerts to gold_alert_validation",
    default_args=default_args,
    schedule="*/30 * * * *",
    start_date=datetime(2026, 3, 17),
    catchup=False,
    max_active_runs=1,
    tags=["ttc-pulse", "gtfsrt", "alerts", "sidecar"],
) as dag:
    poll_cmd = _run_script("src/ttc_pulse/alerts/poll_service_alerts.py", f'--url "{GTFSRT_URL}"') if GTFSRT_URL else _run_script("src/ttc_pulse/alerts/poll_service_alerts.py")

    poll_task = BashOperator(
        task_id="poll_service_alerts",
        bash_command=poll_cmd,
    )

    register_raw = BashOperator(
        task_id="register_raw_gtfsrt_snapshots",
        bash_command=_run_script("src/ttc_pulse/ingestion/register_gtfsrt_snapshots.py"),
    )

    parse_alerts = BashOperator(
        task_id="parse_gtfsrt_alerts_to_bronze",
        bash_command=_run_script("src/ttc_pulse/alerts/parse_service_alerts.py"),
    )

    normalize_alerts = BashOperator(
        task_id="normalize_gtfsrt_entities",
        bash_command=_run_script("src/ttc_pulse/normalization/normalize_gtfsrt_entities.py"),
    )

    build_alert_fact = BashOperator(
        task_id="build_fact_gtfsrt_alerts_norm",
        bash_command=_run_script("src/ttc_pulse/facts/build_fact_gtfsrt_alerts_norm.py"),
    )

    build_alert_gold = BashOperator(
        task_id="build_gold_alert_validation",
        bash_command=_run_script("src/ttc_pulse/marts/build_gold_alert_validation.py"),
    )

    poll_task >> register_raw >> parse_alerts >> normalize_alerts >> build_alert_fact >> build_alert_gold
