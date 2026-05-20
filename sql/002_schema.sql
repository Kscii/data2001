CREATE TABLE IF NOT EXISTS {schema}.poi_clean (
    objectid BIGINT PRIMARY KEY,
    topoid BIGINT,
    poigroup_code SMALLINT,
    poigroup_name TEXT,
    poitype TEXT,
    poiname TEXT,
    poilabel TEXT,
    poilabeltype TEXT,
    poialtlabel TEXT,
    poisourcefeatureoid BIGINT,
    accesscontrol INTEGER,
    startdate TIMESTAMPTZ,
    enddate TIMESTAMPTZ,
    lastupdate TIMESTAMPTZ,
    msoid BIGINT,
    centroidid BIGINT,
    shapeuuid UUID,
    changetype TEXT,
    processstate TEXT,
    urbanity TEXT,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.sa4 (
    sa4_code TEXT PRIMARY KEY,
    sa4_name TEXT NOT NULL,
    gccsa_code TEXT,
    gccsa_name TEXT,
    state_code TEXT,
    state_name TEXT,
    area_albers_sqkm DOUBLE PRECISION,
    asgs_loci_uri TEXT,
    bbox_minx DOUBLE PRECISION,
    bbox_miny DOUBLE PRECISION,
    bbox_maxx DOUBLE PRECISION,
    bbox_maxy DOUBLE PRECISION,
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.sa2 (
    sa2_code TEXT PRIMARY KEY, -- 设定sa2_code为主键, 按照sa2_code进行去重, 保证每个sa2_code只有一条记录
    sa2_name TEXT NOT NULL,
    sa3_code TEXT,
    sa3_name TEXT,
    sa4_code TEXT REFERENCES {schema}.sa4(sa4_code),
    sa4_name TEXT,
    gccsa_code TEXT,
    gccsa_name TEXT,
    state_code TEXT,
    state_name TEXT,
    area_albers_sqkm DOUBLE PRECISION,
    asgs_loci_uri TEXT,
    population INTEGER,
    population_density DOUBLE PRECISION,
    bbox_minx DOUBLE PRECISION,
    bbox_miny DOUBLE PRECISION,
    bbox_maxx DOUBLE PRECISION,
    bbox_maxy DOUBLE PRECISION,
    geometry GEOMETRY(MultiPolygon, 4326) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.sa2_poi (
    sa2_code TEXT NOT NULL REFERENCES {schema}.sa2(sa2_code) ON DELETE CASCADE,
    poi_objectid BIGINT NOT NULL REFERENCES {schema}.poi_clean(objectid) ON DELETE CASCADE,
    assign_method TEXT NOT NULL DEFAULT 'postgis_covers',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (sa2_code, poi_objectid)
);

CREATE TABLE IF NOT EXISTS {schema}.sa2_score (
    score_version TEXT NOT NULL,
    score_universe TEXT NOT NULL,
    sa2_code TEXT NOT NULL REFERENCES {schema}.sa2(sa2_code) ON DELETE CASCADE,
    poi_count INTEGER NOT NULL,
    mean_poi_count DOUBLE PRECISION NOT NULL,
    std_poi_count DOUBLE PRECISION NOT NULL,
    z_poi DOUBLE PRECISION NOT NULL,
    score_raw DOUBLE PRECISION NOT NULL,
    score_100 DOUBLE PRECISION NOT NULL,
    population INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (sa2_code, score_version, score_universe)
);

CREATE TABLE IF NOT EXISTS {schema}.sa2_income (
    sa2_code TEXT PRIMARY KEY REFERENCES {schema}.sa2(sa2_code) ON DELETE CASCADE,
    sa2_name TEXT NOT NULL,
    income_earners_2022_23 INTEGER,
    income_earners_2021_22 INTEGER,
    income_earners_change INTEGER,
    income_earners_change_pct DOUBLE PRECISION,
    median_income_2022_23 INTEGER,
    source_year TEXT NOT NULL,
    source_name TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.score_income_correlation (
    id BIGSERIAL PRIMARY KEY,
    score_version TEXT NOT NULL,
    score_universe TEXT NOT NULL,
    method TEXT NOT NULL,
    statistic DOUBLE PRECISION NOT NULL,
    p_value DOUBLE PRECISION NOT NULL,
    n INTEGER NOT NULL,
    alpha DOUBLE PRECISION NOT NULL,
    is_significant BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
