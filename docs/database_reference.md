# Database Reference

## Source of Truth

| Type | Location | Notes |
| --- | --- | --- |
| Extensions | `sql/001_extensions.sql` | PostGIS extension. |
| Schema | `sql/002_schema.sql` | Business table definitions. |
| Indexes | `sql/003_indexes.sql` | Spatial indexes and query indexes. |
| Admin repository | `src/data2001/db/repositories/admin.py` | init/check/clear/reset. |
| Write repository | `src/data2001/db/repositories/write.py` | Upserts, spatial assignment, score writes, and correlation writes. |
| Read repository | `src/data2001/db/repositories/read.py` | Score and correlation input queries. |
| ERD | `report/figures/schema.png` | Database relationship diagram. |

## Dictionary

### ERD

![Database schema diagram](../report/figures/schema.png)

Core relationships:

```text
sa4 -> sa2
sa2 -> sa2_poi -> poi_clean
sa2 -> sa2_score
sa2 -> sa2_income
sa2_score + sa2_income -> score_income_correlation
```

### Default Database Connection

| Setting | Default |
| --- | --- |
| driver | `postgresql+psycopg` |
| host | `localhost` |
| port | `5432` |
| database | `data2001` |
| user | `data2001` |
| password | `data2001` |
| schema | `data2001` |
| spatial SRID | `4326` |

### Table: `poi_clean`

Purpose: stores cleaned NSW POI point data. Original API fields are normalised, and a PostGIS point geometry is added.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `objectid` | `BIGINT` | primary key | NSW POI object id. |
| `topoid` | `BIGINT` | nullable | API source field. |
| `poigroup_code` | `SMALLINT` | nullable | POI group code. |
| `poigroup_name` | `TEXT` | nullable | Group name mapped from code. |
| `poitype` | `TEXT` | nullable | POI type. |
| `poiname` | `TEXT` | nullable | POI name. |
| `poilabel` | `TEXT` | nullable | POI label. |
| `poilabeltype` | `TEXT` | nullable | Label type. |
| `poialtlabel` | `TEXT` | nullable | Alternative label. |
| `poisourcefeatureoid` | `BIGINT` | nullable | Source feature id. |
| `accesscontrol` | `INTEGER` | nullable | Access control. |
| `startdate` | `TIMESTAMPTZ` | nullable | API date. |
| `enddate` | `TIMESTAMPTZ` | nullable | API date. |
| `lastupdate` | `TIMESTAMPTZ` | nullable | API update time. |
| `msoid` | `BIGINT` | nullable | API source field. |
| `centroidid` | `BIGINT` | nullable | API source field. |
| `shapeuuid` | `UUID` | nullable | Geometry/source UUID. |
| `changetype` | `TEXT` | nullable | API source field. |
| `processstate` | `TEXT` | nullable | API source field. |
| `urbanity` | `TEXT` | nullable | API source field. |
| `longitude` | `DOUBLE PRECISION` | not null | From `geometry.x`. |
| `latitude` | `DOUBLE PRECISION` | not null | From `geometry.y`. |
| `geometry` | `GEOMETRY(Point, 4326)` | not null | `ST_MakePoint(longitude, latitude)`. |
| `created_at` | `TIMESTAMPTZ` | not null default now | Load timestamp. |

### Table: `sa4`

Purpose: stores SA4 boundaries and acts as the parent geography for SA2 records.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `sa4_code` | `TEXT` | primary key | SA4 code. |
| `sa4_name` | `TEXT` | not null | SA4 name. |
| `gccsa_code` | `TEXT` | nullable | GCCSA code. |
| `gccsa_name` | `TEXT` | nullable | Default focus is `Greater Sydney`. |
| `state_code` | `TEXT` | nullable | State code. |
| `state_name` | `TEXT` | nullable | State name. |
| `area_albers_sqkm` | `DOUBLE PRECISION` | nullable | ABS area. |
| `asgs_loci_uri` | `TEXT` | nullable | ABS ASGS URI. |
| `bbox_minx` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `bbox_miny` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `bbox_maxx` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `bbox_maxy` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `geometry` | `GEOMETRY(MultiPolygon, 4326)` | not null | SA4 polygon. |
| `loaded_at` | `TIMESTAMPTZ` | not null default now | Load timestamp. |

### Table: `sa2`

Purpose: stores SA2 boundaries, SA4 membership, population, and bbox fields. SA2 is the main analytical unit for score, maps, and spatial join.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `sa2_code` | `TEXT` | primary key | SA2 code. |
| `sa2_name` | `TEXT` | not null | SA2 name. |
| `sa3_code` | `TEXT` | nullable | SA3 code. |
| `sa3_name` | `TEXT` | nullable | SA3 name. |
| `sa4_code` | `TEXT` | FK -> `sa4.sa4_code` | SA4 parent. |
| `sa4_name` | `TEXT` | nullable | SA4 name. |
| `gccsa_code` | `TEXT` | nullable | GCCSA code. |
| `gccsa_name` | `TEXT` | nullable | GCCSA name. |
| `state_code` | `TEXT` | nullable | State code. |
| `state_name` | `TEXT` | nullable | State name. |
| `area_albers_sqkm` | `DOUBLE PRECISION` | nullable | ABS area. |
| `asgs_loci_uri` | `TEXT` | nullable | ABS ASGS URI. |
| `population` | `INTEGER` | nullable | Updated from the population layer. |
| `population_density` | `DOUBLE PRECISION` | nullable | Updated from the population layer. |
| `bbox_minx` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `bbox_miny` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `bbox_maxx` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `bbox_maxy` | `DOUBLE PRECISION` | nullable | Computed bbox. |
| `geometry` | `GEOMETRY(MultiPolygon, 4326)` | not null | SA2 polygon. |
| `loaded_at` | `TIMESTAMPTZ` | not null default now | Load timestamp. |

### Table: `sa2_poi`

Purpose: stores final spatial assignment from POI points to SA2 polygons. It is a bridge table and does not duplicate POI detail fields.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `sa2_code` | `TEXT` | PK, FK -> `sa2.sa2_code`, cascade delete | Assigned SA2. |
| `poi_objectid` | `BIGINT` | PK, FK -> `poi_clean.objectid`, cascade delete | Assigned POI. |
| `assign_method` | `TEXT` | not null default `postgis_covers` | Current configured value is `covers_deterministic_first`. |
| `created_at` | `TIMESTAMPTZ` | not null default now | Assignment timestamp. |

### Table: `sa2_score`

Purpose: stores Task 3 well-resourced scores. The primary key includes score version and universe so later algorithm variants can be stored.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `score_version` | `TEXT` | primary key part | Default `baseline`. |
| `score_universe` | `TEXT` | primary key part | `greater_sydney` or `selected_sa4`. |
| `sa2_code` | `TEXT` | primary key part, FK -> `sa2.sa2_code`, cascade delete | Scored SA2. |
| `poi_count` | `INTEGER` | not null | Aggregated from `sa2_poi`. |
| `mean_poi_count` | `DOUBLE PRECISION` | not null | Mean inside the score universe. |
| `std_poi_count` | `DOUBLE PRECISION` | not null | Standard deviation inside the score universe. |
| `z_poi` | `DOUBLE PRECISION` | not null | `(poi_count - mean) / std`. |
| `score_raw` | `DOUBLE PRECISION` | not null | `sigmoid(z_poi)`. |
| `score_100` | `DOUBLE PRECISION` | not null | `score_raw * output_scale`. |
| `population` | `INTEGER` | nullable | Copied for context/filtering. |
| `created_at` | `TIMESTAMPTZ` | not null default now | Score timestamp. |

### Table: `sa2_income`

Purpose: stores ABS Personal Income in Australia median income fields at SA2 level for correlation analysis.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `sa2_code` | `TEXT` | primary key, FK -> `sa2.sa2_code`, cascade delete | Income SA2. |
| `sa2_name` | `TEXT` | not null | SA2 name. |
| `income_earners_2022_23` | `INTEGER` | nullable | Current income earners. |
| `income_earners_2021_22` | `INTEGER` | nullable | Previous income earners. |
| `income_earners_change` | `INTEGER` | nullable | Absolute change. |
| `income_earners_change_pct` | `DOUBLE PRECISION` | nullable | Percentage change. |
| `median_income_2022_23` | `INTEGER` | nullable | Median income. |
| `source_year` | `TEXT` | not null | Default `2022-23`. |
| `source_name` | `TEXT` | not null | Default `ABS Personal Income in Australia`. |
| `loaded_at` | `TIMESTAMPTZ` | not null default now | Load timestamp. |

### Table: `score_income_correlation`

Purpose: stores statistical test outputs for score versus median income. The current workflow writes Pearson and Spearman results.

| Column | Type | Constraint | Note |
| --- | --- | --- | --- |
| `id` | `BIGSERIAL` | primary key | Result id. |
| `score_version` | `TEXT` | not null | Score version. |
| `score_universe` | `TEXT` | not null | Score universe. |
| `method` | `TEXT` | not null | `pearson` or `spearman`. |
| `statistic` | `DOUBLE PRECISION` | not null | Correlation coefficient. |
| `p_value` | `DOUBLE PRECISION` | not null | Test p-value. |
| `n` | `INTEGER` | not null | Sample size. |
| `alpha` | `DOUBLE PRECISION` | not null | Significance threshold. |
| `is_significant` | `BOOLEAN` | not null | `p_value < alpha`. |
| `created_at` | `TIMESTAMPTZ` | not null default now | Result timestamp. |

### Indexes

| Index | Table / columns | Type | Purpose |
| --- | --- | --- | --- |
| `idx_poi_clean_topoid` | `poi_clean(topoid)` | btree | POI source id lookup. |
| `idx_poi_clean_poigroup` | `poi_clean(poigroup_code)` | btree | POI group filtering and group distribution. |
| `idx_poi_clean_geometry_gist` | `poi_clean(geometry)` | GiST | Spatial join point lookup. |
| `idx_sa4_geometry_gist` | `sa4(geometry)` | GiST | SA4 map/spatial query. |
| `idx_sa2_sa4_code` | `sa2(sa4_code)` | btree | SA4 scope filtering. |
| `idx_sa2_population` | `sa2(population)` | btree | Population filtering. |
| `idx_sa2_geometry_gist` | `sa2(geometry)` | GiST | Spatial join polygon lookup. |
| `idx_sa2_poi_poi_objectid` | `sa2_poi(poi_objectid)` | btree | Reverse POI assignment lookup. |
| `idx_sa2_score_version_universe` | `sa2_score(score_version, score_universe)` | btree | Current score version/universe queries. |
| `idx_sa2_score_score` | `sa2_score(score_100)` | btree | Ranking and score filtering. |
| `idx_sa2_income_median_income` | `sa2_income(median_income_2022_23)` | btree | Income scatter/correlation. |
| `idx_sa2_income_earners` | `sa2_income(income_earners_2022_23)` | btree | Income sample filtering. |

## Design Notes

### Spatial Fields

| Table | Geometry | SRID | Source |
| --- | --- | --- | --- |
| `poi_clean` | `Point` | `4326` | NSW POI `geometry.x/y`. |
| `sa2` | `MultiPolygon` | `4326` | ABS SA2 rings, loaded with `ST_Multi`. |
| `sa4` | `MultiPolygon` | `4326` | ABS SA4 rings, loaded with `ST_Multi`. |

The metadata expected SRID may differ from 4326, but requests use `outSR=4326`, and the database stores geometry in 4326.

### Spatial Assignment

```sql
ST_Covers(sa2.geometry, poi_clean.geometry)
```

`ST_Covers` keeps POI points that lie on SA2 boundaries. If one POI matches multiple SA2 polygons, the SQL uses `ROW_NUMBER() OVER (PARTITION BY p.objectid ORDER BY s.sa2_code ASC)` and keeps the first `sa2_code`.

### Database Lifecycle

| Behaviour | Design |
| --- | --- |
| init | Creates PostGIS extension, schema, tables, and indexes. |
| check | Checks connection, PostGIS, business table count, and geometry SRID. |
| clear | Clears business table rows but keeps schema/table/index definitions. |
| reset | Drops the business schema and reinitialises it. |

### Score Formula Storage

```text
z_poi = (poi_count - mean_poi_count) / std_poi_count
score_raw = sigmoid(z_poi)
score_100 = score_raw * output_scale
```

`sa2_score` stores both aggregated inputs and calculated outputs so the report, notebooks, and dashboard can inspect the source of each SA2 score.

## Cross References

| Document | Contents |
| --- | --- |
| `docs/api_reference.md` | Endpoints, API fields, and persisted files. |
| `docs/architecture_design.md` | Workflow, module boundaries, and call chain. |
| `docs/database_container_setup.md` | Local PostGIS container. |
| `report/report.md` | ERD and figures used by the report. |
