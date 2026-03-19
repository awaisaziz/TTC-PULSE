-- Initialize DuckDB analytical layer for TTC delay analytics.
-- Run with: duckdb data/ttc.duckdb < sql/duckdb/01_initialize.sql

-- Keep scans parallel and deterministic for local verification.
PRAGMA threads=4;
PRAGMA enable_progress_bar=false;

DROP VIEW IF EXISTS delays;
DROP TABLE IF EXISTS delays;

-- Build canonical delays table directly in DuckDB to avoid runtime dependency
-- on external parquet file paths.
CREATE OR REPLACE TABLE delays AS
SELECT
    service_date,
    service_time,
    route_id,
    vehicle_type,
    min_delay,
    vehicle_id,
    EXTRACT('year' FROM service_date)::INTEGER AS year,
    EXTRACT('month' FROM service_date)::INTEGER AS month
FROM (
    SELECT
        CAST(Date AS DATE) AS service_date,
        CAST(Time AS TIME) AS service_time,
        CAST(Route AS VARCHAR) AS route_id,
        CAST('bus' AS VARCHAR) AS vehicle_type,
        TRY_CAST("Min Delay" AS INTEGER) AS min_delay,
        TRY_CAST(Vehicle AS VARCHAR) AS vehicle_id
    FROM read_csv_auto('data/raw/bus/*.csv', header=true, union_by_name=true)
    WHERE TRY_CAST("Min Delay" AS INTEGER) IS NOT NULL
    UNION ALL
    SELECT
        CAST(Date AS DATE) AS service_date,
        CAST(Time AS TIME) AS service_time,
        CAST(Line AS VARCHAR) AS route_id,
        CAST('subway' AS VARCHAR) AS vehicle_type,
        TRY_CAST("Min Delay" AS INTEGER) AS min_delay,
        TRY_CAST(Vehicle AS VARCHAR) AS vehicle_id
    FROM read_csv_auto('data/raw/subway/*.csv', header=true, union_by_name=true)
    WHERE TRY_CAST("Min Delay" AS INTEGER) IS NOT NULL
) t;

-- Optional parquet export artifact for pipeline verification and downstream use.
COPY delays
TO 'data/parquet/delays'
(
    FORMAT PARQUET,
    COMPRESSION ZSTD,
    PARTITION_BY (vehicle_type, year, month),
    OVERWRITE_OR_IGNORE true
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

CREATE OR REPLACE TABLE trips AS
SELECT
    route_id,
    service_id,
    trip_id,
    trip_headsign,
    direction_id,
    shape_id
FROM read_csv_auto('data/raw/gtfs/trips.csv', header=true);

CREATE OR REPLACE TABLE stop_times AS
SELECT
    trip_id,
    arrival_time,
    departure_time,
    stop_id,
    stop_sequence,
    shape_dist_traveled
FROM read_csv_auto('data/raw/gtfs/stop_times.csv', header=true);

CREATE OR REPLACE TABLE calendar AS
SELECT * FROM read_csv_auto('data/raw/gtfs/calendar.csv', header=true);

CREATE OR REPLACE TABLE calendar_dates AS
SELECT * FROM read_csv_auto('data/raw/gtfs/calendar_dates.csv', header=true);

CREATE OR REPLACE TABLE shapes AS
SELECT * FROM read_csv_auto('data/raw/gtfs/shapes.csv', header=true);
