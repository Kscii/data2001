CREATE INDEX IF NOT EXISTS idx_poi_clean_topoid
    ON {schema}.poi_clean (topoid);

CREATE INDEX IF NOT EXISTS idx_poi_clean_poigroup
    ON {schema}.poi_clean (poigroup_code);

CREATE INDEX IF NOT EXISTS idx_poi_clean_geometry_gist
    ON {schema}.poi_clean USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_sa4_geometry_gist
    ON {schema}.sa4 USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_sa2_sa4_code
    ON {schema}.sa2 (sa4_code);

CREATE INDEX IF NOT EXISTS idx_sa2_population
    ON {schema}.sa2 (population);

CREATE INDEX IF NOT EXISTS idx_sa2_geometry_gist
    ON {schema}.sa2 USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_sa2_poi_poi_objectid
    ON {schema}.sa2_poi (poi_objectid);

CREATE INDEX IF NOT EXISTS idx_sa2_score_version_universe
    ON {schema}.sa2_score (score_version, score_universe);

CREATE INDEX IF NOT EXISTS idx_sa2_score_score
    ON {schema}.sa2_score (score_100);

CREATE INDEX IF NOT EXISTS idx_sa2_income_median_income
    ON {schema}.sa2_income (median_income_2022_23);

CREATE INDEX IF NOT EXISTS idx_sa2_income_earners
    ON {schema}.sa2_income (income_earners_2022_23);
