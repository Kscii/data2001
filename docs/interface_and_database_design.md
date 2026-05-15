# 接口字段和数据库交接文档

## 1. 配置入口

本地配置文件：

```text
configs/local.yaml
```

示例配置文件：

```text
configs/example.yaml
```

主要配置：

```text
database      PostgreSQL/PostGIS 连接
task2         API 抓取范围、SA4 选择、POI clean batch size
api.layers    ArcGIS endpoint、字段列表、metadata 检查
spatial       POI 到 SA2 的空间归属方式和数据库 SRID
scoring       score universe、population filter、输出 scale
income        income 字段映射和最小 income earners 阈值
correlation   Pearson/Spearman 和显著性阈值
outputs       raw data、processed data、figure 输出路径
figures       report PNG 导出参数
dashboard     Dash 本地启动参数
```

常用命令：

```bash
uv run data2001 init-db
uv run data2001 check-db
uv run data2001 plan-import
uv run data2001 run-workflow
uv run data2001 export-charts
uv run data2001 serve-dashboard
```

## 2. ArcGIS 接口

### 2.1 NSW POI

Endpoint：

```text
https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_POI/MapServer/0/query
```

常用请求参数：

```text
f=json
where=1=1
outFields=objectid,topoid,poigroup,...
returnGeometry=true
geometry=minx,miny,maxx,maxy
geometryType=esriGeometryEnvelope
inSR=4326
outSR=4326
spatialRel=esriSpatialRelIntersects
resultRecordCount=1000
resultOffset=0,1000,2000,...
```

使用字段：

```text
objectid
topoid
poigroup
poitype
poiname
poilabel
poilabeltype
poialtlabel
poisourcefeatureoid
accesscontrol
startdate
enddate
lastupdate
msoid
centroidid
shapeuuid
changetype
processstate
urbanity
geometry.x -> longitude
geometry.y -> latitude
```

`poigroup` 映射：

```text
1 Community
2 Education
3 Recreation
4 Transport
5 Utility
6 Hydrography
7 Landform
8 Place
9 Industry
```

### 2.2 SA2 / SA4 Boundary

SA2 endpoint：

```text
https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/FeatureServer/0/query
```

SA4 endpoint：

```text
https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA4/MapServer/0/query
```

默认区域：

```sql
gccsa_name_2021 = 'Greater Sydney'
```

SA2 字段：

```text
sa2_code_2021
sa2_name_2021
sa3_code_2021
sa3_name_2021
sa4_code_2021
sa4_name_2021
gccsa_code_2021
gccsa_name_2021
state_code_2021
state_name_2021
area_albers_sqkm
asgs_loci_uri_2021
geometry
```

SA4 字段：

```text
sa4_code_2021
sa4_name_2021
gccsa_code_2021
gccsa_name_2021
state_code_2021
state_name_2021
area_albers_sqkm
asgs_loci_uri_2021
geometry
```

### 2.3 Population

Endpoint：

```text
https://geo.abs.gov.au/arcgis/rest/services/Hosted/ABS_Population_and_people_by_2021_SA2_Nov_2023/FeatureServer/1/query
```

字段：

```text
sa2_code_2021
sa2_name_2021
erp_p_202022      -> population
erp_212022        -> population_density
area_albers_sqkm
```

### 2.4 Median Income

Endpoint：

```text
https://geo.abs.gov.au/arcgis/rest/services/Hosted/Personal_Income_in_Australia_2022_23_SA2_2021/FeatureServer/0/query
```

API 字段：

```text
sa2_code_2021
sa2_name_2021
income_earners_23
income_earners_22
change_from_prev_year_23_22
change_from_prev_year_pct_23_22
median_income_23
```

数据库字段：

```text
income_earners_2022_23
income_earners_2021_22
income_earners_change
income_earners_change_pct
median_income_2022_23
```

## 3. 抓取范围

`task2.crawl_scope` 控制抓取范围：

```text
greater_sydney       Greater Sydney 下所有 SA2 bbox
selected_sa4         selected_sa4_by_member 中 SA4 下的所有 SA2 bbox
explicit_sa4_codes   sa4_codes 中 SA4 下的所有 SA2 bbox
```

组员和 SA4 的对应关系写在：

```yaml
task2:
  selected_sa4_by_member:
    abcd1234: Sydney - Parramatta
    efgh5678: Sydney - Northern Beaches
```

小范围测试可以临时使用：

```yaml
task2:
  crawl_scope: explicit_sa4_codes
  sa4_codes:
    - "126"
```

POI 抓取按 SA2 bbox 请求候选点，最终归属使用数据库空间关系：

```sql
ST_Covers(sa2.geometry, poi_clean.geometry)
```

边界点规则：

```text
assign_method = covers_deterministic_first
如果一个 POI 同时匹配多个 SA2，保留 sa2_code 升序第一条。
```

## 4. 数据库表

SQL 文件：

```text
sql/001_extensions.sql
sql/002_schema.sql
sql/003_indexes.sql
```

核心表：

```text
poi_clean                 清洗后的 POI 点
sa4                       SA4 boundary
sa2                       SA2 boundary + population
sa2_poi                   POI 到 SA2 的空间归属
sa2_score                 score 结果
sa2_income                SA2 median income
score_income_correlation  score-income correlation 检验结果
```

主要主键和关联：

```text
poi_clean.objectid                         primary key
sa4.sa4_code                               primary key
sa2.sa2_code                               primary key
sa2.sa4_code                               references sa4.sa4_code
sa2_poi(sa2_code, poi_objectid)            primary key
sa2_poi.sa2_code                           references sa2.sa2_code
sa2_poi.poi_objectid                       references poi_clean.objectid
sa2_score(sa2_code, score_version, score_universe)
sa2_income.sa2_code                        references sa2.sa2_code
```

`sa2_score` 字段：

```text
score_version
score_universe
sa2_code
poi_count
mean_poi_count
std_poi_count
z_poi
score_raw
score_100
population
created_at
```

Score 公式：

```text
score_raw = sigmoid(z_poi)
score_100 = score_raw * output_scale
```

## 5. 常用索引

空间索引：

```text
poi_clean.geometry GiST
sa2.geometry GiST
sa4.geometry GiST
```

过滤和 join 索引：

```text
poi_clean.topoid
poi_clean.poigroup_code
sa2.sa4_code
sa2.population
sa2_poi.poi_objectid
sa2_score(score_version, score_universe)
sa2_score.score_100
sa2_income.median_income_2022_23
sa2_income.income_earners_2022_23
```

## 6. 文件输出

Task 2 raw files：

```text
data/raw/poi_api/responses/response_*.json
data/raw/poi_api/features.jsonl
```

Task 1 processed CSV：

```text
data/processed/cleaned_data.csv
```

Task 4 figures：

```text
report/figures/score_histogram.png
report/figures/top_sa2_score.png
report/figures/bottom_sa2_score.png
report/figures/poi_group_distribution.png
report/figures/score_income_correlation.png
report/figures/sa2_score_choropleth.png
```