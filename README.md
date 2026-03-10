# TTC Bus Delay Analytics (2023 vs 2024)

This repository contains a modular Python data analytics pipeline and Streamlit dashboard for exploratory analysis of TTC bus delays.

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
source .venv/bin/activate
.venv\Scripts\activate
pip install -r requirements.txt
```

## Download dataset files

Use the CKAN downloader (based on Toronto Open Data API):

```bash
python src/data_fetcher.py
```

This creates:
- `ttc_delay_analytics/data/ttc_bus_delay_2023.csv`
- `ttc_delay_analytics/data/ttc_bus_delay_2024.csv`

## Run dashboard

```bash
streamlit run dashboard/app.py
```

## Features

- Data loading and column standardization.
- Cleaning and feature engineering (hour, day_of_week, month, delay_severity).
- EDA for temporal, route, incident, spatial, and year-over-year comparison analysis.
- Plotly visualizations:
  - delay distribution histogram
  - delays by hour heatmap
  - delay trends by month
  - top routes bar chart
  - incident type bar chart
  - delay vs gap scatter plot
- Streamlit dashboard pages:
  - Overview
  - Temporal analysis
  - Route reliability
  - Incident causes
  - Location hotspots
