# Run TTC Pulse (Toronto Transit Reliability Observatory)

This quick guide is for running the TTC Pulse project focused on TTC transit in Toronto.

## 1) Create a Python virtual environment

From the project root, create a local environment folder named `.venv`:

```bash
python -m venv .venv
```

This `.venv` folder stores the project's installed Python packages (including everything from `requirements.txt`) in an isolated environment.

## 2) Activate the virtual environment

### Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
```

### Windows (cmd)

```cmd
.\.venv\Scripts\activate.bat
```

### macOS/Linux

```bash
source .venv/bin/activate
```

## 3) Install project dependencies into the virtual environment

```bash
pip install -r requirements.txt
```

## 4) Verify data backend

Ensure the DuckDB file exists:
- `data/ttc_pulse.duckdb`

## 5) Run Streamlit dashboard

From project root:

```bash
streamlit run app/streamlit_app.py
```

## 6) Optional GTFS-RT live alert chain

```bash
python src/ttc_pulse/alerts/poll_service_alerts.py --url "<GTFSRT_ALERTS_URL>"
python src/ttc_pulse/ingestion/register_gtfsrt_snapshots.py
python src/ttc_pulse/alerts/parse_service_alerts.py
python src/ttc_pulse/normalization/normalize_gtfsrt_entities.py
python src/ttc_pulse/facts/build_fact_gtfsrt_alerts_norm.py
python src/ttc_pulse/marts/build_gold_alert_validation.py
```

## 7) Airflow side-car

DAG file:
- `airflow/dags/poll_gtfsrt_alerts.py`

Schedule:
- every 30 minutes
