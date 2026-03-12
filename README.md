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

From the `ttc_delay_analytics` folder:

```bash
streamlit run dashboard/app.py
```

Then open the local URL shown by Streamlit (usually `http://localhost:8501`).

## How to use your two CSV files

1. Put both files here:
   - `TTC-PULSE/ttc_delay_analytics/data/ttc_bus_delay_2023.csv`
   - `TTC-PULSE/ttc_delay_analytics/data/ttc_bus_delay_2024.csv`
2. Start the app with `streamlit run dashboard/app.py`.
3. In the sidebar, choose one of these dataset modes:
   - **Default 2023 + 2024 files** (reads the two files above)
   - **Upload CSV file(s)** (lets you upload one or more files manually)

## CSV compatibility improvements

The loader now accepts more header variations automatically, including:

- Route columns like `Route`, `Route Name`, `Route_No`, `Line`
- Time/date patterns like `Date`, `Report Date`, `Incident Date`, `Time Of Day`
- Incident/location patterns like `Incident Description`, `Intersection`, `Location Name`
- Delay/gap patterns like `Min Delay`, `Delay Minutes`, `Min Gap`, `Gap Minutes`

It also handles:

- Hidden BOM/zero-width characters in headers
- Delimiters including comma, tab, semicolon, and pipe (`|`)
- Files with a combined datetime where time must be derived
- Missing `min_gap` by using `min_delay` as a fallback

## Troubleshooting

If you still see `Missing required columns`:

1. Confirm both files exist in `ttc_delay_analytics/data/` with exact names.
2. Open CSV headers and verify they include equivalents of:
   - `date`, `time`, `route`, `location`, `incident`, `min_delay`, `min_gap`
3. If your file uses uncommon names, use **Upload CSV file(s)** and share the exact header row so aliases can be added.
4. Make sure you launched Streamlit from `ttc_delay_analytics` (not a different directory).

