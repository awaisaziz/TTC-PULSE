from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
EXCLUDED_TOKENS = ('readme', 'code description', 'code-descriptions')
DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTH_ORDER = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

COLUMN_ALIASES = {
    'date': 'date',
    'report_date': 'date',
    'incident_date': 'date',
    'time': 'time',
    'report_time': 'time',
    'incident_time': 'time',
    'time_of_day': 'time',
    'route': 'route',
    'route_number': 'route',
    'route_name': 'route',
    'route_no': 'route',
    'route_num': 'route',
    'line': 'route',
    'station': 'location',
    'location': 'location',
    'location_name': 'location',
    'intersection': 'location',
    'incident': 'incident',
    'incident_type': 'incident',
    'incident_description': 'incident',
    'delay_reason': 'incident',
    'code': 'incident_code',
    'min_delay': 'min_delay',
    'min delay': 'min_delay',
    'delay_minutes': 'min_delay',
    'delay': 'min_delay',
    'min_gap': 'min_gap',
    'min gap': 'min_gap',
    'gap_minutes': 'min_gap',
    'gap': 'min_gap',
    'day': 'day',
    'direction': 'direction',
    'bound': 'direction',
    'vehicle': 'vehicle',
}

REQUIRED_COLUMNS = ['date', 'route', 'location', 'min_delay', 'min_gap']


def normalize_col(col: str) -> str:
    col = str(col).strip().strip('"').replace('﻿', '').replace('​', '')
    col = col.replace('/', '_').replace('-', '_').lower()
    col = re.sub(r'[^a-z0-9_]+', '_', col)
    col = re.sub(r'_+', '_', col).strip('_')
    return COLUMN_ALIASES.get(col, col)


def read_any_table(file_path: Path) -> pd.DataFrame:
    payload = file_path.read_bytes()
    is_excel_payload = payload[:2] == b'PK'

    if file_path.suffix.lower() in {'.xlsx', '.xls'} or is_excel_payload:
        return pd.read_excel(file_path)

    encodings = ('utf-8', 'utf-8-sig', 'utf-16', 'cp1252', 'latin1')
    separators = (None, ',', '\t', ';', '|')

    for encoding in encodings:
        for separator in separators:
            try:
                return pd.read_csv(file_path, encoding=encoding, sep=separator, engine='python', on_bad_lines='skip')
            except Exception:
                pass

    raise ValueError(f'Unable to parse file: {file_path}')


def categorize_incident(text: str) -> str:
    value = str(text).strip().lower()
    if not value or value == 'nan':
        return 'Unknown'

    keyword_map = {
        'Mechanical': ['mechanical', 'engine', 'brake', 'vehicle', 'equipment'],
        'Traffic': ['traffic', 'congestion', 'slow traffic'],
        'Security': ['security', 'police', 'investigation'],
        'Diversion': ['diversion', 'detour', 'road closure'],
        'Collision': ['collision', 'accident', 'crash'],
        'Medical': ['medical', 'sick customer', 'injury'],
        'Weather': ['weather', 'snow', 'storm', 'rain'],
        'Passenger': ['passenger', 'customer', 'wheelchair'],
        'Operations': ['operator', 'crew', 'dispatch', 'late leaving', 'general delay'],
        'Construction': ['construction', 'work zone'],
    }

    for label, keywords in keyword_map.items():
        if any(keyword in value for keyword in keywords):
            return label

    if re.fullmatch(r'[A-Z]{3,6}', str(text).strip()):
        return f'Code-{str(text).strip()[:2]}'

    return str(text).strip().title()


def extract_route_id(route_value: str) -> str:
    route_text = str(route_value).strip()
    match = re.match(r'^(\d+[A-Z]?)', route_text)
    if match:
        return match.group(1)
    return route_text or 'Unknown'


def standardize_dataset(df: pd.DataFrame, file_path: Path, mode: str) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_col(column) for column in df.columns]

    for target, patterns in {
        'date': ('date',),
        'route': ('route', 'line'),
        'location': ('location', 'station', 'intersection', 'stop'),
        'incident': ('incident',),
        'incident_code': ('code',),
        'min_delay': ('delay',),
        'min_gap': ('gap',),
    }.items():
        if target in df.columns:
            continue
        match = next((col for col in df.columns if any(pattern in col for pattern in patterns)), None)
        if match is not None:
            df[target] = df[match]

    if 'min_gap' not in df.columns and 'min_delay' in df.columns:
        df['min_gap'] = df['min_delay']

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f'{file_path.name} is missing required columns: {missing}')

    if 'incident' not in df.columns and 'incident_code' in df.columns:
        df['incident'] = df['incident_code']

    if 'incident_code' not in df.columns:
        df['incident_code'] = pd.NA

    standardized = pd.DataFrame()
    standardized['date'] = pd.to_datetime(df['date'], errors='coerce')
    standardized['route'] = df['route'].astype(str).str.strip()
    standardized['route_id'] = standardized['route'].apply(extract_route_id)
    standardized['location'] = df['location'].astype(str).str.strip()
    standardized['incident'] = df['incident'].astype(str).str.strip()
    standardized['incident_code'] = df['incident_code'].astype(str).str.strip()
    standardized['incident_category'] = standardized['incident'].apply(categorize_incident)
    standardized['min_delay'] = pd.to_numeric(df['min_delay'], errors='coerce').fillna(0)
    standardized['min_gap'] = pd.to_numeric(df['min_gap'], errors='coerce').fillna(0)
    standardized['mode'] = mode
    standardized['source_file'] = file_path.name

    standardized = standardized.dropna(subset=['date'])
    standardized['year'] = standardized['date'].dt.year
    standardized['month'] = standardized['date'].dt.month
    standardized['month_name'] = standardized['date'].dt.strftime('%b')
    standardized['weekday'] = standardized['date'].dt.day_name()

    return standardized


@st.cache_data(show_spinner=False)
def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    mode_dirs = [path for path in DATA_DIR.iterdir() if path.is_dir()]

    frames = []
    failures = []
    for mode_dir in mode_dirs:
        mode = mode_dir.name.lower()
        files = sorted(
            path for path in mode_dir.glob('*.csv')
            if not any(token in path.name.lower() for token in EXCLUDED_TOKENS)
        )
        for file_path in files:
            try:
                raw = read_any_table(file_path)
                frames.append(standardize_dataset(raw, file_path, mode))
            except Exception as exc:
                failures.append({'mode': mode, 'file_name': file_path.name, 'error': str(exc)})

    if not frames:
        raise ValueError('No usable data files were loaded from the data directory.')

    combined = pd.concat(frames, ignore_index=True)
    failure_df = pd.DataFrame(failures)
    return combined, failure_df


def build_route_summary(df: pd.DataFrame) -> pd.DataFrame:
    route_names = (
        df.groupby(['route_id', 'route'], as_index=False)
        .size()
        .sort_values(['route_id', 'size'], ascending=[True, False])
        .drop_duplicates('route_id')
        .rename(columns={'route': 'route_label'})[['route_id', 'route_label']]
    )

    summary = (
        df.groupby('route_id', as_index=False)
        .agg(
            incidents=('route_id', 'size'),
            total_delay=('min_delay', 'sum'),
            total_gap=('min_gap', 'sum'),
            avg_delay=('min_delay', 'mean'),
            avg_gap=('min_gap', 'mean'),
            first_year=('year', 'min'),
            last_year=('year', 'max'),
        )
    )
    return summary.merge(route_names, on='route_id', how='left')


def make_top10_chart(route_summary: pd.DataFrame, metric: str, title: str, color_scale: str) -> px.bar:
    if route_summary.empty:
        return px.bar(title=title)

    top10 = route_summary.nlargest(10, metric).sort_values(metric)
    top10['display_label'] = top10['route_id'] + ' - ' + top10['route_label'].fillna(top10['route_id'])

    fig = px.bar(
        top10,
        x=metric,
        y='display_label',
        orientation='h',
        text_auto=True,
        color=metric,
        color_continuous_scale=color_scale,
        labels={metric: title, 'display_label': 'Route'},
        title=title,
    )
    fig.update_layout(height=450, coloraxis_showscale=False, margin=dict(l=0, r=0, t=45, b=0))
    return fig


def make_yearly_chart(route_df: pd.DataFrame) -> px.bar:
    yearly = (
        route_df.groupby(['year', 'route_id'], as_index=False)
        .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
        .sort_values('year')
    )
    long_df = yearly.melt(
        id_vars=['year', 'route_id'],
        value_vars=['incidents', 'total_delay', 'total_gap'],
        var_name='metric',
        value_name='value',
    )
    return px.bar(long_df, x='year', y='value', color='route_id', facet_row='metric', barmode='group', title='Yearly Statistics by Selected Routes')


def make_monthly_chart(route_df: pd.DataFrame) -> px.line:
    monthly = (
        route_df.groupby(['year', 'month', 'month_name', 'route_id'], as_index=False)
        .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
        .sort_values(['year', 'month'])
    )
    monthly['month_label'] = monthly['month_name'] + ' ' + monthly['year'].astype(str)
    long_df = monthly.melt(
        id_vars=['month_label', 'route_id'],
        value_vars=['incidents', 'total_delay', 'total_gap'],
        var_name='metric',
        value_name='value',
    )
    return px.line(long_df, x='month_label', y='value', color='route_id', facet_row='metric', markers=True, title='Monthly Statistics by Selected Routes')


def make_weekday_chart(route_df: pd.DataFrame) -> px.bar:
    weekday = (
        route_df.groupby(['weekday', 'route_id'], as_index=False)
        .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
    )
    weekday['weekday'] = pd.Categorical(weekday['weekday'], categories=DAY_ORDER, ordered=True)
    weekday = weekday.sort_values('weekday')
    long_df = weekday.melt(
        id_vars=['weekday', 'route_id'],
        value_vars=['incidents', 'total_delay', 'total_gap'],
        var_name='metric',
        value_name='value',
    )
    return px.bar(long_df, x='weekday', y='value', color='route_id', facet_row='metric', barmode='group', title='Day-of-Week Statistics by Selected Routes')


def make_incident_chart(route_df: pd.DataFrame) -> px.bar:
    incident_df = (
        route_df.groupby(['incident_category', 'route_id'], as_index=False)
        .agg(incidents=('incident_category', 'size'), total_delay=('min_delay', 'sum'))
        .sort_values('incidents', ascending=False)
    )
    top_categories = incident_df.groupby('incident_category', as_index=False)['incidents'].sum().nlargest(12, 'incidents')
    filtered = incident_df[incident_df['incident_category'].isin(top_categories['incident_category'])]
    return px.bar(filtered, x='incidents', y='incident_category', color='route_id', barmode='group', title='Top Incident Categories for Selected Routes')


def main() -> None:
    st.set_page_config(page_title='TTC Transit Route Insights', layout='wide')
    st.title('TTC Route Insights Dashboard')
    st.caption('Compare bus, subway, and streetcar delays with route/year/month/day filters.')

    df, failures = load_all_data()

    modes = sorted(df['mode'].dropna().unique().tolist())
    selected_modes = st.sidebar.multiselect('Mode', modes, default=modes)
    filtered_df = df[df['mode'].isin(selected_modes)].copy()

    years = sorted(filtered_df['year'].dropna().astype(int).unique().tolist())
    selected_years = st.sidebar.multiselect('Year', years, default=years)
    filtered_df = filtered_df[filtered_df['year'].isin(selected_years)]

    months = [month for month in MONTH_ORDER if month in filtered_df['month_name'].unique()]
    selected_months = st.sidebar.multiselect('Month', months, default=months)
    filtered_df = filtered_df[filtered_df['month_name'].isin(selected_months)]

    weekdays = [day for day in DAY_ORDER if day in filtered_df['weekday'].unique()]
    selected_weekdays = st.sidebar.multiselect('Day of Week', weekdays, default=weekdays)
    filtered_df = filtered_df[filtered_df['weekday'].isin(selected_weekdays)]

    if filtered_df.empty:
        st.warning('No records match the selected mode/year/month/day filters.')
        return

    route_summary = build_route_summary(filtered_df)
    route_ids = route_summary.sort_values('route_id')['route_id'].tolist()
    default_routes = route_summary.nlargest(3, 'incidents')['route_id'].tolist()

    selected_routes = st.sidebar.multiselect(
        'Routes (multi-select)',
        options=route_ids,
        default=default_routes,
        format_func=lambda route_id: f"{route_id} - {route_summary.loc[route_summary['route_id'] == route_id, 'route_label'].iloc[0]}",
    )

    selected_route_df = filtered_df[filtered_df['route_id'].isin(selected_routes)].copy()

    top_a, top_b, top_c = st.columns(3)
    with top_a:
        st.plotly_chart(
            make_top10_chart(route_summary, 'incidents', 'Top 10 Routes by Incidents', 'Viridis'),
            use_container_width=True,
        )
    with top_b:
        st.plotly_chart(
            make_top10_chart(route_summary, 'total_delay', 'Top 10 Routes by Total Min Delay', 'Cividis'),
            use_container_width=True,
        )
    with top_c:
        st.plotly_chart(
            make_top10_chart(route_summary, 'total_gap', 'Top 10 Routes by Total Min Gap', 'Sunset'),
            use_container_width=True,
        )

    if selected_route_df.empty:
        st.warning('Select at least one route to view detailed statistics.')
        return

    k1, k2, k3, k4 = st.columns(4)
    k1.metric('Selected Routes', f"{len(selected_routes):,}")
    k2.metric('Incidents', f"{len(selected_route_df):,}")
    k3.metric('Total Min Delay', f"{selected_route_df['min_delay'].sum():,.0f}")
    k4.metric('Total Min Gap', f"{selected_route_df['min_gap'].sum():,.0f}")

    tabs = st.tabs(['Yearly', 'Monthly', 'Day of Week', 'Incidents', 'Tables'])

    with tabs[0]:
        st.plotly_chart(make_yearly_chart(selected_route_df), use_container_width=True)

    with tabs[1]:
        st.plotly_chart(make_monthly_chart(selected_route_df), use_container_width=True)

    with tabs[2]:
        st.plotly_chart(make_weekday_chart(selected_route_df), use_container_width=True)

    with tabs[3]:
        st.plotly_chart(make_incident_chart(selected_route_df), use_container_width=True)

    with tabs[4]:
        route_table = (
            selected_route_df.groupby(['mode', 'route_id'], as_index=False)
            .agg(
                incidents=('route_id', 'size'),
                total_delay=('min_delay', 'sum'),
                total_gap=('min_gap', 'sum'),
                avg_delay=('min_delay', 'mean'),
                avg_gap=('min_gap', 'mean'),
            )
            .sort_values(['mode', 'incidents'], ascending=[True, False])
        )
        st.dataframe(route_table, use_container_width=True, hide_index=True)

        incident_table = (
            selected_route_df.groupby(['mode', 'route_id', 'incident_category', 'incident'], as_index=False)
            .agg(
                incidents=('incident', 'size'),
                total_delay=('min_delay', 'sum'),
                total_gap=('min_gap', 'sum'),
            )
            .sort_values(['incidents', 'total_delay'], ascending=[False, False])
            .head(100)
        )
        st.dataframe(incident_table, use_container_width=True, hide_index=True)

    if not failures.empty:
        with st.expander('Skipped files'):
            st.dataframe(failures, use_container_width=True, hide_index=True)


if __name__ == '__main__':
    main()
