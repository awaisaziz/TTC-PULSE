# TTC Bus Delay Analytics Dashboard

This project provides a Streamlit dashboard for exploring TTC bus delay data interactively.

## Project structure

```text
ttc_delay_analytics/
    data/
        ttc_bus_delay_2023.csv
        ttc_bus_delay_2024.csv
    src/
        data_fetcher.py
        data_loader.py
        preprocessing.py
        eda_analysis.py
        visualization.py
    dashboard/
        app.py
    requirements.txt
```

## Setup

```bash
cd ttc_delay_analytics
python -m venv .venv
```

Activate the virtual environment:

- macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Prepare data

You can use either approach:

1. **Use default local files** in `ttc_delay_analytics/data/` named:
   - `ttc_bus_delay_2023.csv`
   - `ttc_bus_delay_2024.csv`
2. **Download files automatically**:

```bash
python src/data_fetcher.py
```

## Run the dashboard

```bash
streamlit run dashboard/app.py
```

## What is fixed and improved

- Fixed robust column handling so common TTC schema variations are automatically mapped (for example `Incident_Date`, `Incident_Time`, `Min Delay`, `Min Gap`, etc.).
- Added fallback logic so if `min_gap` is missing it is derived from `min_delay`.
- Added dataset source selection in the sidebar:
  - **Default 2023 + 2024 files**
  - **Upload CSV file(s)**
- Added a **Combined dashboard** page where you can select multiple analyses and see them update in real time for the selected dataset and filters.

## Interactive features

- Sidebar filters for year, route, incident type, and delay severity.
- Individual analysis pages:
  - Overview
  - Temporal analysis
  - Route reliability
  - Incident causes
  - Location hotspots
- Combined dashboard with multi-select analysis panels.

## Notes

- If the dashboard reports missing columns, check the uploaded CSV has equivalents for date/time/route/location/incident/min_delay.
- Supported delimiters and encodings are auto-detected with multiple fallbacks.
