from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
EXCLUDED_TOKENS = ('readme',)
DAY_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

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

REQUIRED_COLUMNS = ['date', 'time', 'route', 'location', 'min_delay', 'min_gap']


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

    if re.fullmatch(r'[A-Z]{4,6}', str(text).strip()):
        return f'Code-{str(text).strip()[:2]}'

    return str(text).strip().title()


def extract_route_id(route_value: str) -> str:
    route_text = str(route_value).strip()
    match = re.match(r'^(\d+[A-Z]?)', route_text)
    if match:
        return match.group(1)
    return route_text or 'Unknown'


def standardize_dataset(df: pd.DataFrame, file_path: Path) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_col(column) for column in df.columns]

    for target, patterns in {
        'date': ('date',),
        'time': ('time',),
        'route': ('route', 'line'),
        'location': ('location', 'station', 'intersection', 'stop'),
        'incident': ('incident',),
        'incident_code': ('code',),
        'min_delay': ('delay',),
        'min_gap': ('gap',),
        'direction': ('direction', 'bound'),
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
    standardized['source_file'] = file_path.name

    standardized = standardized.dropna(subset=['date'])
    standardized['year'] = standardized['date'].dt.year
    standardized['month'] = standardized['date'].dt.month
    standardized['month_name'] = standardized['date'].dt.strftime('%b')
    standardized['weekday'] = standardized['date'].dt.day_name()
    standardized['weekday'] = pd.Categorical(standardized['weekday'], categories=DAY_ORDER, ordered=True)

    return standardized


@st.cache_data(show_spinner=False)
def load_all_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    files = sorted(path for path in DATA_DIR.glob('*.csv') if not any(token in path.name.lower() for token in EXCLUDED_TOKENS))

    frames = []
    failures = []
    for file_path in files:
        try:
            raw = read_any_table(file_path)
            frames.append(standardize_dataset(raw, file_path))
        except Exception as exc:
            failures.append({'file_name': file_path.name, 'error': str(exc)})

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


def make_top10_chart(route_summary: pd.DataFrame, metric: str) -> px.bar:
    labels = {
        'incidents': 'Incidents',
        'total_delay': 'Total Delay Minutes',
        'total_gap': 'Total Gap Minutes',
    }
    top10 = route_summary.nlargest(10, metric).sort_values(metric)
    top10['display_label'] = top10['route_id'] + ' - ' + top10['route_label'].fillna(top10['route_id'])

    fig = px.bar(
        top10,
        x=metric,
        y='display_label',
        orientation='h',
        text_auto=True,
        color=metric,
        color_continuous_scale='Tealgrn',
        labels={metric: labels[metric], 'display_label': 'Route'},
        title=f'Top 10 Routes by {labels[metric]}',
    )
    fig.update_layout(height=500, coloraxis_showscale=False)
    return fig


def make_yearly_chart(route_df: pd.DataFrame) -> px.bar:
    yearly = (
        route_df.groupby('year', as_index=False)
        .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
        .sort_values('year')
    )
    long_df = yearly.melt(id_vars='year', value_vars=['incidents', 'total_delay', 'total_gap'], var_name='metric', value_name='value')
    return px.bar(long_df, x='year', y='value', color='metric', barmode='group', title='Yearly Route Performance')


def make_monthly_chart(route_df: pd.DataFrame) -> px.line:
    monthly = (
        route_df.groupby(['year', 'month', 'month_name'], as_index=False)
        .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
        .sort_values(['year', 'month'])
    )
    monthly['month_label'] = monthly['month_name'] + ' ' + monthly['year'].astype(str)
    fig = px.line(monthly, x='month_label', y=['incidents', 'total_delay', 'total_gap'], markers=True, title='Monthly Route Trend')
    fig.update_layout(xaxis_title='Month', yaxis_title='Value')
    return fig


def make_weekday_chart(route_df: pd.DataFrame) -> px.bar:
    weekday = (
        route_df.groupby('weekday', as_index=False)
        .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
        .sort_values('weekday')
    )
    long_df = weekday.melt(id_vars='weekday', value_vars=['incidents', 'total_delay', 'total_gap'], var_name='metric', value_name='value')
    return px.bar(long_df, x='weekday', y='value', color='metric', barmode='group', title='Day-of-Week Pattern')


def make_incident_chart(route_df: pd.DataFrame) -> px.bar:
    category = (
        route_df.groupby('incident_category', as_index=False)
        .agg(incidents=('incident_category', 'size'), total_delay=('min_delay', 'sum'))
        .sort_values('incidents', ascending=False)
        .head(12)
    )
    return px.bar(category, x='incidents', y='incident_category', orientation='h', color='total_delay', title='Top Incident Categories for Selected Route')


def main() -> None:
    st.set_page_config(page_title='TTC Route Insights', layout='wide')
    st.title('TTC Bus Route Insights Dashboard')
    st.caption('Interactive route ranking and route-level drilldown across years, months, and weekdays.')

    df, failures = load_all_data()
    route_summary = build_route_summary(df)

    metric = st.sidebar.radio(
        'Rank top 10 routes by',
        options=['incidents', 'total_delay', 'total_gap'],
        format_func=lambda value: {
            'incidents': 'Number of incidents',
            'total_delay': 'Total min delay',
            'total_gap': 'Total min gap',
        }[value],
    )

    top10 = route_summary.nlargest(10, metric)
    default_route = top10.iloc[0]['route_id'] if not top10.empty else route_summary.iloc[0]['route_id']
    route_ids = route_summary.sort_values('route_id')['route_id'].tolist()

    selected_route = st.sidebar.selectbox(
        'Select route',
        options=route_ids,
        index=route_ids.index(default_route),
        format_func=lambda route_id: f"{route_id} - {route_summary.loc[route_summary['route_id'] == route_id, 'route_label'].iloc[0]}",
    )

    selected_route_df = df[df['route_id'] == selected_route].copy()
    route_meta = route_summary.loc[route_summary['route_id'] == selected_route].iloc[0]

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.plotly_chart(make_top10_chart(route_summary, metric), use_container_width=True)
    with col2:
        st.subheader(f"Route {route_meta['route_id']}")
        st.write(route_meta['route_label'])
        m1, m2, m3 = st.columns(3)
        m1.metric('Incidents', f"{int(route_meta['incidents']):,}")
        m2.metric('Total Min Delay', f"{route_meta['total_delay']:,.0f}")
        m3.metric('Total Min Gap', f"{route_meta['total_gap']:,.0f}")
        m4, m5, m6 = st.columns(3)
        m4.metric('Avg Delay', f"{route_meta['avg_delay']:.2f}")
        m5.metric('Avg Gap', f"{route_meta['avg_gap']:.2f}")
        m6.metric('Year Span', f"{int(route_meta['first_year'])}-{int(route_meta['last_year'])}")

        if not failures.empty:
            with st.expander('Skipped files'):
                st.dataframe(failures, use_container_width=True, hide_index=True)

    tab1, tab2, tab3, tab4 = st.tabs(['Yearly', 'Monthly', 'Weekday', 'Incidents'])

    with tab1:
        st.plotly_chart(make_yearly_chart(selected_route_df), use_container_width=True)
        yearly_table = (
            selected_route_df.groupby('year', as_index=False)
            .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'), avg_delay=('min_delay', 'mean'))
            .sort_values('year')
        )
        st.dataframe(yearly_table, use_container_width=True, hide_index=True)

    with tab2:
        st.plotly_chart(make_monthly_chart(selected_route_df), use_container_width=True)
        monthly_table = (
            selected_route_df.groupby(['year', 'month', 'month_name'], as_index=False)
            .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
            .sort_values(['year', 'month'])
        )
        st.dataframe(monthly_table, use_container_width=True, hide_index=True)

    with tab3:
        st.plotly_chart(make_weekday_chart(selected_route_df), use_container_width=True)
        weekday_table = (
            selected_route_df.groupby('weekday', as_index=False)
            .agg(incidents=('route_id', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'), avg_delay=('min_delay', 'mean'))
            .sort_values('weekday')
        )
        st.dataframe(weekday_table, use_container_width=True, hide_index=True)

    with tab4:
        st.plotly_chart(make_incident_chart(selected_route_df), use_container_width=True)
        incident_table = (
            selected_route_df.groupby(['incident_category', 'incident'], as_index=False)
            .agg(incidents=('incident', 'size'), total_delay=('min_delay', 'sum'), total_gap=('min_gap', 'sum'))
            .sort_values(['incidents', 'total_delay'], ascending=[False, False])
            .head(25)
        )
        st.dataframe(incident_table, use_container_width=True, hide_index=True)


if __name__ == '__main__':
    main()
