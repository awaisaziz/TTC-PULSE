-- Initialize DuckDB analytical layer for TTC delay analytics.
-- Run with: duckdb data/ttc.duckdb < sql/duckdb/01_initialize.sql

INSTALL parquet;
LOAD parquet;

-- Keep scans parallel and deterministic for local verification.
PRAGMA threads=4;
PRAGMA enable_progress_bar=false;

-- Create a partitioned Parquet lake if it does not yet exist.
-- The partitioning by vehicle_type/year/month enables partition pruning for time-window and type filters.
COPY (
    WITH bus_raw AS (
        SELECT
            CAST(Date AS DATE) AS service_date,
            CAST(Time AS TIME) AS service_time,
            CAST(Route AS VARCHAR) AS route_id,
            CAST('bus' AS VARCHAR) AS vehicle_type,
            TRY_CAST("Min Delay" AS INTEGER) AS min_delay,
            TRY_CAST(Vehicle AS VARCHAR) AS vehicle_id
        FROM read_csv_auto('data/raw/bus/*.csv', header=true, union_by_name=true)
        WHERE TRY_CAST("Min Delay" AS INTEGER) IS NOT NULL
    ),
    subway_raw AS (
        SELECT
            CAST(Date AS DATE) AS service_date,
            CAST(Time AS TIME) AS service_time,
            CAST(Line AS VARCHAR) AS route_id,
            CAST('subway' AS VARCHAR) AS vehicle_type,
            TRY_CAST("Min Delay" AS INTEGER) AS min_delay,
            TRY_CAST(Vehicle AS VARCHAR) AS vehicle_id
        FROM read_csv_auto('data/raw/subway/*.csv', header=true, union_by_name=true)
        WHERE TRY_CAST("Min Delay" AS INTEGER) IS NOT NULL
    ),
    unified AS (
        SELECT
            service_date,
            EXTRACT('year' FROM service_date)::INTEGER AS year,
            EXTRACT('month' FROM service_date)::INTEGER AS month,
            service_time,
            route_id,
            vehicle_type,
            min_delay,
            vehicle_id
        FROM bus_raw
        UNION ALL
        SELECT
            service_date,
            EXTRACT('year' FROM service_date)::INTEGER AS year,
            EXTRACT('month' FROM service_date)::INTEGER AS month,
            service_time,
            route_id,
            vehicle_type,
            min_delay,
            vehicle_id
        FROM subway_raw
    )
    SELECT * FROM unified
)
TO 'data/parquet/delays'
(
    FORMAT PARQUET,
    COMPRESSION ZSTD,
    PARTITION_BY (vehicle_type, year, month),
    OVERWRITE_OR_IGNORE true
);

-- Canonical delay view over partitioned Parquet.
CREATE OR REPLACE VIEW delays AS
SELECT
    service_date,
    service_time,
    route_id,
    vehicle_type,
    min_delay,
    vehicle_id,
    year,
    month
FROM read_parquet(
    'data/parquet/delays/**/*.parquet',
    hive_partitioning=true,
    union_by_name=true
);

-- GTFS dimensions.
CREATE OR REPLACE TABLE routes AS
SELECT
    route_id,
    route_short_name,
    route_long_name,
    route_type,
    route_color,
    route_text_color
FROM read_csv_auto('data/raw/gtfs/routes.csv', header=true);

CREATE OR REPLACE TABLE stops AS
SELECT
    stop_id,
    stop_code,
    stop_name,
    stop_lat,
    stop_lon,
    location_type,
    parent_station,
    wheelchair_boarding
FROM read_csv_auto('data/raw/gtfs/stops.csv', header=true);
