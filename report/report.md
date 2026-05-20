# Greater Sydney Resource Distribution Analysis

## Project Overview

This project investigates how urban resources are distributed across different areas of Greater Sydney using POI data, census information, and spatial analysis methods. The main focus of the project is to compare how well different SA2 regions are resourced and whether there are noticeable differences between highly urbanised and more suburban areas.

The project began with cleaning and preparing the raw datasets. Several preprocessing steps were applied, including standardising column names, handling missing values, reshaping the data structure, and preparing geographic boundary information for later analysis and mapping. These steps were necessary to make the datasets easier to work with and more consistent across different tasks.

After the cleaning stage, POI data from categories such as recreation, transport, education, and community facilities were analysed. A scoring workflow was then used to calculate a well-resourced score for each SA2 region based mainly on the concentration of POIs and related indicators.

Different visualisations were produced during the analysis process, including score maps, POI distribution maps, ranking charts, and comparisons between well-resourced scores and median income levels. These visualisations helped show how accessibility and resource concentration varied between different parts of Sydney.

## Data Sources and Study Scope

Detailed endpoint contracts and field mappings are documented in `api_reference.md`, Section: Dictionary.

- NSW Region Summary CSV
  - Endpoint / path: `data/raw/task1/raw_data.csv`
  - Role in analysis: raw Task 1 input for cleaning and member-derived statistics.
  - Evidence: `full_workflow.ipynb`, Section 2; `task1_statistics.ipynb`, Section: Individual Derived Statistics.
- NSW Points of Interest API
  - Endpoint / path: `https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_POI/MapServer/0/query`
  - Role in analysis: provides POI point records used to count resources within SA2 areas.
  - Evidence: `full_workflow.ipynb`, Section 5.
- ABS SA2 Boundaries
  - Endpoint / path: `https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA2/FeatureServer/0/query`
  - Role in analysis: provides SA2 polygons, SA2 bounding boxes, and map geometry.
  - Evidence: `full_workflow.ipynb`, Sections 4-6.
- ABS SA4 Boundaries
  - Endpoint / path: `https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SA4/MapServer/0/query`
  - Role in analysis: defines selected member SA4 scopes and SA4-level comparison groups.
  - Evidence: `full_workflow.ipynb`, Section 1.1.
- ABS SA2 Population
  - Endpoint / path: `https://geo.abs.gov.au/arcgis/rest/services/Hosted/ABS_Population_and_people_by_2021_SA2_Nov_2023/FeatureServer/1/query`
  - Role in analysis: adds SA2 population and population density for score filtering and context.
  - Evidence: `full_workflow.ipynb`, Section 5.
- ABS Personal Income in Australia
  - Endpoint / path: `https://geo.abs.gov.au/arcgis/rest/services/Hosted/Personal_Income_in_Australia_2022_23_SA2_2021/FeatureServer/0/query`
  - Role in analysis: provides median income fields for score-income correlation analysis.
  - Evidence: `full_workflow.ipynb`, Section 9.

The selected SA4 scope is configured in `configs/local.yaml`. SA2 counts are read back from the final PostGIS `sa2` table after the Task 2 import.

| Member name | Unikey | Selected SA4 | SA2 count |
| --- | --- | --- | --- |
| Xuejian Fang | xfan0282 | Sydney - City and Inner South | 27 |
| Daniel Kaiqi Bi | dabi0142 | Sydney - Parramatta | 34 |
| Jinyu Zhou | jzho0172 | Sydney - North Sydney and Hornsby | 26 |
| Xuanhao Yu | xuyu8020 | Sydney - Northern Beaches | 19 |

All selected SA4 areas are within Greater Sydney. The current configuration uses `task2_import.crawl_scope: selected_sa4` and `task3_score.score_universe: selected_sa4`, so the score distribution is calculated over the selected member SA4 set rather than every SA2 in Greater Sydney.

## Task 1: NSW Statistics Cleaning and Key Findings

The Task 1 cleaning workflow is shown in `full_workflow.ipynb`, Section 2: Task 1 CSV Loading, Cleaning, and Derived Statistics. The raw CSV is cleaned once and then reused as the common input for each member's derived statistics.

The implemented cleaning steps standardise column names, standardise text columns, extract unit information, handle missing values and duplicate rows, convert year columns into numeric values, detect outliers, reshape the dataset into long format, and remove rows with missing observations.

Each member's complete five derived statistics are provided in `task1_statistics.ipynb`, Section: Individual Derived Statistics. The report highlights selected functions that support the group-level analysis.

| Statistic function(s) | Selected derived statistic | Result summary | Why it matters |
| --- | --- | --- | --- |
| `xfan0282_2()`, `xfan0282_3()`, `xfan0282_5()` | Work-from-home growth, public transport commute decline, and housing stress | Work-from-home share grew 6.42x from 4.82% to 30.98%; public transport commute share dropped by 11.98 percentage points from 15.98% to 4.00%; rent stress was 2.05x mortgage stress in 2021. | These findings show major changes in commuting behaviour and housing pressure, providing context for interpreting transport resources, local POI demand, and accessibility. |
| `dabi0142_1()` to `dabi0142_5()` | Population growth rate, working-age population percentage, unemployment rate change, most volatile indicator, and longest increase streak | NSW population growth result was negative in the output, working-age population was around 64.7%, unemployment had a largest yearly change of -2.3 percentage points, and one indicator showed a 5-year increase streak. | These statistics help show long-term demographic and labour market patterns in NSW, while also highlighting possible data quality or indicator selection issues. |
| `jzho0172_1()`, `jzho0172_2()`, `jzho0172_3()` | Population growth and demographic structure | Estimated resident population grew by 5.38% from 2019 to 2024. Population density increased by 0.60 persons/km², and females made up 50.26% of the 2024 population. | These findings show recent population growth and demographic balance in NSW, which provides useful context for interpreting demand for services and POI-based resource scores. |
| `xuyu8020_1()` to `xuyu8020_5()` | Population structure, gender balance, income growth, income distribution, and business dynamics | NSW had an age dependency ratio of 54.44 dependents per 100 working-age persons in 2024. The sex ratio was 98.98 males per 100 females. Median total income increased by 15.16% from 2018 to 2022, while mean total income was 37.03% higher than median income in 2022. The business net entry rate was 2.95% of total businesses in 2024. | These statistics provide demographic and economic context for later resource analysis. Population structure may affect service demand, income statistics help describe economic conditions, and business entry-exit patterns indicate local economic activity. |

Overall, the Task 1 findings provide useful context for the later POI-based resource analysis. The commuting statistics show changes in work and transport behaviour, while the demographic and income statistics show that resource scores should be interpreted alongside population structure, affordability, business activity, and changing mobility patterns rather than as simple POI counts alone.

## Database Schema and Indexing

Detailed table definitions, indexes, geometry types, and the full ERD reference are documented in `database_reference.md`, Section: Dictionary.

![Database schema diagram](figures/schema.png)

In this ERD, blue key icons mark primary key columns, and yellow key icons mark foreign key columns.

The ERD summarises four main relationships used by the project:

- `sa4 -> sa2`
- `sa2 -> sa2_poi -> poi_clean`
- `sa2 -> sa2_score`
- `sa2 -> sa2_income`

The `sa4` and `sa2` tables define the geographic scope of the analysis. Each SA2 belongs to one SA4, and the SA2 geometry is used as the spatial unit for assigning POI records and calculating scores. The `sa2_poi` table is a bridge table between SA2 boundaries and cleaned POI points, so the raw POI records can remain separate from the spatial assignment result. The score and income tables are stored separately from the boundary tables because they are derived analytical outputs rather than boundary source data.

| Table | Role | Key relationship |
| --- | --- | --- |
| `sa4` | SA4 boundary and parent geography. | `sa4 -> sa2` |
| `sa2` | Main spatial unit with population, bbox, and polygon geometry. | joined to POI assignment, score, and income records |
| `poi_clean` | Cleaned NSW POI point records. | assigned to SA2 through `sa2_poi` |
| `sa2_poi` | Spatial assignment bridge table. | `sa2 <-> poi_clean` |
| `sa2_score` | Derived well-resourced score for each SA2. | references `sa2` |
| `sa2_income` | Median income and income-earner data by SA2. | joins with `sa2_score` for correlation |
| `score_income_correlation` | Pearson and Spearman test outputs. | derived from `sa2_score` and `sa2_income` |

Spatial fields are stored in SRID 4326. `poi_clean.geometry` is a `Point`, while `sa2.geometry` and `sa4.geometry` are `MultiPolygon` geometries.

The database includes GiST spatial indexes on POI, SA2, and SA4 geometries to support PostGIS joins and map queries. It also includes filter and ranking indexes such as `sa2.sa4_code`, `sa2.population`, `sa2_score(score_version, score_universe)`, `sa2_score.score_100`, and income indexes for score ranking and correlation queries.

## API Extraction and Spatial Join

Detailed API extraction parameters, metadata checks, and persisted raw file paths are documented in `api_reference.md`, Section: Design Notes.

Task 2 first reads the selected SA4 scope from the configuration, fetches the SA2 polygons within that scope, and builds one bbox request for each SA2. The NSW POI API is then queried with those bbox envelopes. Raw responses and raw features are persisted for reproducibility, cleaned POI records are written to `poi_clean`, and final POI-to-SA2 assignment is performed in PostGIS.

Bbox extraction only returns candidate POIs because a rectangular bbox can include points outside the actual SA2 polygon. Final assignment uses `ST_Covers(sa2.geometry, poi_clean.geometry)` and writes the result to `sa2_poi`. If one POI matches multiple SA2 polygons on a boundary, the deterministic rule keeps the first `sa2_code` in ascending order. Therefore, raw bbox features are not used directly for the score; `sa2_poi` is the final polygon-assigned geographic dataset.

The selected SA2 areas were also validated against their parent SA4 polygons in PostGIS. The evidence query checks `ST_Covers(sa4.geometry, ST_PointOnSurface(sa2.geometry))` and requires an SA2-to-SA4 area coverage ratio of at least `0.999`. All 106 imported SA2 polygons passed this validation, with zero point failures and zero missing parent SA4 records.

| Evidence item | Value |
| --- |-------|
| Response files | 106   |
| Raw feature rows | 16468 |
| Clean POI rows | 9634 |
| Assigned POI rows | 7894 |
| Unassigned POI rows | 1740 |
| Boundary duplicate candidates | 0 |

## Score Calculation Method

The score is calculated from the number of POIs assigned to each SA2:

```text
z_poi = (poi_count - mean_poi_count) / std_poi_count
score_raw = sigmoid(z_poi)
score_100 = score_raw * 100
```

`poi_count` is aggregated from `sa2_poi` by SA2. The current configuration uses `score_universe: selected_sa4`, so `mean_poi_count` and `std_poi_count` are calculated across the selected member SA4 areas.

SA2 areas are scored only when `population >= 100`, using `task3_score.min_population`. SA2 areas with population below `100` or missing population are excluded from `sa2_score`. In the current selected-SA4 run, 101 of 106 imported SA2 areas were scored; the five excluded SA2 areas had population below the threshold.

The z-score standardises POI counts relative to the selected score universe. The sigmoid transformation maps the standardised values onto a 0-1 range, and multiplying by 100 gives an interpretable 0-100 score while reducing the visual impact of extreme POI counts.

The score is a quantity-based resource indicator. It does not measure service quality, service capacity, opening hours, accessibility, or resident demand.

As an extension and sensitivity analysis, the report also compares the baseline score with a population-adjusted POI density view:

```text
poi_per_1000 = (poi_count / population) * 1000
```

This extension does not replace the required baseline formula. Instead, it checks whether areas with high raw POI counts still appear well-resourced after considering resident population size.

## Results Analysis and Visualisations

The figures below provide the report-level interpretation of the score results. Detailed member-level visual analysis is available in `task2_task3_analysis.ipynb`, Section: Individual Visual Analysis.

### Score Distribution

![Score distribution histogram](figures/score_histogram.png)

The score histogram shows that most SA2 regions fall within the lower-to-middle score range, especially around 30 to 55. Across the 101 scored SA2s, scores range from 19.93 to 99.46, with a median of 45.91 and an interquartile range from 35.48 to 57.63. The distribution is right-skewed, with fewer SA2s receiving very high scores above 80. This suggests that highly resourced SA2s are relatively uncommon within the selected SA4 scope. Most areas have moderate POI availability, while a small number of areas contain much denser POI concentrations and therefore receive much higher scores.

### Spatial Pattern of Scores

![SA2 score choropleth map](figures/sa2_score_choropleth.png)

The score map shows that high-scoring SA2s are not evenly distributed across the selected regions. Several higher-score areas appear around more urbanised or activity-centre locations, while lower-score areas are more common in less dense or more residential parts of the selected SA4s. The Northern Beaches and North Sydney and Hornsby areas contain several high-scoring SA2s, while parts of Parramatta and City and Inner South show more mixed results. This indicates that POI concentration is strongly spatial rather than randomly distributed.

![Population-adjusted POI density map](figures/poi_density_choropleth.png)

The population-adjusted POI density map is used as an extension and sensitivity analysis for the baseline score. Some SA2s with high raw POI counts may not appear as strong after adjusting by population, because their larger resident base reduces POI density per person. In contrast, some lower-population areas can appear relatively high on the density map even if their raw POI count is not among the highest. This comparison helps identify where the baseline score may be influenced by population size, land use, or unusually dense POI clusters.

![POI point scatter map](figures/poi_point_scatter.png)

The POI point map shows clear clustering rather than an even spread of facilities. POIs are concentrated around urban centres, coastal activity areas, transport corridors, and commercial or community hubs. This clustering helps explain why nearby SA2s can receive very different scores: the score depends not only on the size of the SA2, but also on whether major POI clusters fall inside its boundary. It also confirms why the final polygon spatial join is necessary after bbox extraction.

### Highest and Lowest Scoring SA2s

![Top scoring SA2s](figures/top_sa2_score.png)

![Bottom scoring SA2s](figures/bottom_sa2_score.png)

The highest-scoring SA2s include areas such as Sydenham - Tempe - St Peters, Sydney (North) - Millers Point, Newport - Bilgola, Bayview - Elanora Heights, Avalon - Palm Beach, and Manly - Fairlight. These areas are likely to contain dense clusters of recreation, community, transport, or activity-centre POIs. Northern Beaches and North Sydney and Hornsby appear frequently among the top-scoring SA2s, suggesting strong internal POI concentration in these SA4s.

The lowest-scoring SA2s include areas such as Dee Why (South) - North Curl Curl, South Wentworthville, Berala, Auburn - North, Parramatta - South, and Banksmeadow. These lower scores may reflect fewer recorded POIs inside the SA2 boundary, more residential land use, or POIs being concentrated in neighbouring SA2s instead. The comparison between top and bottom SA2s shows that resource scores are highly sensitive to local land use and POI clustering.

### SA4-Level Comparison

![SA4 score boxplot](figures/sa4_score_boxplot.png)

The SA4 boxplot shows clear differences between the selected SA4 regions. Sydney - North Sydney and Hornsby has the highest mean score (55.21) and median score (53.21), followed closely by Sydney - Northern Beaches with a mean of 54.39 and median of 51.56. Sydney - Parramatta has a lower median of 45.44, while Sydney - City and Inner South has the lowest median of 36.79 but contains the highest individual SA2 score, Sydenham - Tempe - St Peters at 99.46. This means variation occurs both between SA4s and within each SA4: City and Inner South is especially uneven, while North Sydney and Hornsby is more consistently high.

### POI Group Composition

![POI group distribution](figures/poi_group_distribution.png)

The POI group distribution is dominated by Recreation, followed by Community and Transport. Education and Place also contribute a noticeable number of POIs, while Landform, Hydrography, Utility, and Industry appear much less frequently. This composition matters because the baseline score treats all POIs equally. As a result, SA2s with many recreation or community POIs may receive higher scores even if they do not necessarily have stronger access to essential services such as health, education, or transport.

## Correlation with Median Income

![Score and median income correlation](figures/score_income_correlation.png)

| Method | Statistic | p-value | n | Significant? | Interpretation |
| --- | --- | --- | --- | --- | --- |
| Pearson | 0.171 | 0.089 | 100 | No | Weak positive linear relationship, not statistically significant at alpha = 0.05. |
| Spearman | 0.202 | 0.044 | 100 | Yes | Weak positive rank relationship, statistically significant but small in effect size. |

The income relationship is weak overall. Pearson correlation is not statistically significant, while Spearman correlation is significant at alpha = 0.05 but still small. This suggests that higher-income SA2s may tend to rank slightly higher in resource score, but income alone does not explain the score pattern. The weak relationship is plausible because POI locations are also shaped by land use, transport corridors, commercial centres, coastal recreation areas, data reference years, and SA2 aggregation. The result should not be interpreted as causal.

## Conclusion

The scores vary substantially across the selected SA2 regions. Scores range from 19.93 to 99.46, with an interquartile range from 35.48 to 57.63, so the variation is meaningful rather than minor. Variation also appears across SA4s: North Sydney and Hornsby and Northern Beaches have higher median scores, Parramatta is more moderate, and City and Inner South has a lower median but several strong high-score outliers.

The variation is mainly explained by spatial clustering and land use. High-scoring SA2s tend to contain activity centres, coastal or recreation clusters, transport-related POIs, and dense community or commercial facilities, while low-scoring SA2s are often more residential or sit outside major POI clusters. The scoring method is appropriate as the required baseline because it follows `sigmoid(z_poi)` and produces an interpretable 0-100 score, but it remains a quantity-based indicator. It does not measure service quality, capacity, travel time, or actual accessibility, so the population-adjusted POI density map is used as a sensitivity check.

## Limitations and Further Work

- POI count does not distinguish service quality, size, capacity, opening hours, or actual resident accessibility.
- SA2 aggregation can hide variation within each SA2, especially in dense urban areas.
- Bbox extraction returns candidate POIs only, so polygon spatial join is required. Boundary points still require deterministic handling.
- Data sources may not all represent the same reference year, which can affect comparisons between POIs, population, and income.
- The relationship between median income and resource score is correlational and should not be interpreted as causal.
- The current baseline score is mainly based on raw POI count. The population-adjusted POI density map partially tests population demand sensitivity, but the score itself still does not include travel time, public transport frequency, service weighting, or service quality.

Further work could add category-specific POI weights, network travel distance, and sensitivity analysis for different score universes or population filters.

## Appendix: Evidence, Reproducibility and Contributions

### Evidence Map

| Rubric area | Primary evidence | Report coverage |
| --- | --- | --- |
| Data Import | `full_workflow.ipynb`, Section 3: Data Source Summary; Section 5: Task 2 API Extraction and Crawl Plan | Dataset summary and API extraction evidence. |
| Dataset Description | `full_workflow.ipynb`, Section 3: Data Source Summary; `api_reference.md`, Section: Dictionary | Concise dataset source, role, and field-mapping summary. |
| API Extraction | `full_workflow.ipynb`, Section 5: Task 2 API Extraction and Crawl Plan; `api_reference.md`, Section: Design Notes | API workflow summary, selected-SA4 crawl scope, bbox request process, and extraction result table. |
| Database Schema | `full_workflow.ipynb`, Section 4: Database Schema and Indexes; `database_reference.md`, Section: Dictionary | ERD, table roles, key relationships, geometry types, and SRID summary. |
| Database Indexing | `full_workflow.ipynb`, Section 4: Database Schema and Indexes; `database_reference.md`, Section: Dictionary | Spatial GiST indexes and filter/ranking indexes used for joins, maps, scoring, and correlation queries. |
| Spatial Join | `full_workflow.ipynb`, Section 6: Spatial Join Evidence; `task2_task3_analysis.ipynb`, Section: Task 2 Evidence | `ST_Covers` explanation, bbox-candidate limitation, deterministic boundary handling, SA2-to-SA4 validation, and POI assignment summary. |
| Score Calculation | `full_workflow.ipynb`, Section 7: Task 3 Score Calculation | `z_poi`, sigmoid score formula, score universe, population filter, 0-100 score scaling, and method limitations. |
| Results Analysis | `full_workflow.ipynb`, Section 8: Results Analysis; `task2_task3_analysis.ipynb`, Section: Individual Visual Analysis | Interpretation of score distribution, spatial score pattern, POI density, POI clusters, top/bottom SA2s, SA4 comparison, and POI group composition. |
| Correlation Analysis | `full_workflow.ipynb`, Section 9: Correlation Analysis | Pearson/Spearman result table, significance test, interpretation, and non-causal limitation. |
| Data Visualisations | `full_workflow.ipynb`, Section 10: Report Figures | Report figures including score histogram, choropleth maps, POI point map, ranking charts, SA4 boxplot, POI group chart, and score-income scatter plot. |
| Report Quality | `report.md`, Section: Full report | Structured report with evidence links, technical summaries, visual interpretation, limitations, conclusion, reproducibility notes, and contribution appendix. |

Supporting technical references:

- `api_reference.md`, Section: Dictionary
- `architecture_design.md`, Section: Design Notes
- `database_reference.md`, Section: Dictionary

Final submission structure:

```text
submission.zip
  report/
    final_report.pdf
  notebooks/
    full_workflow.ipynb
    xfan0282/
      task1_statistics.ipynb
      task2_task3_analysis.ipynb
    dabi0142/
      task1_statistics.ipynb
      task2_task3_analysis.ipynb
    jzho0172/
      task1_statistics.ipynb
      task2_task3_analysis.ipynb
    xuyu8020/
      task1_statistics.ipynb
      task2_task3_analysis.ipynb
```

Reproducibility commands:

```bash
uv sync
uv run data2001 init-db
uv run data2001 check-db
uv run data2001 run-workflow
uv run data2001 generate-figures
```

### Contributions

The table below summarises the main contributions by member. Commit hashes are provided as supporting evidence; a contribution may be supported by multiple commits where implementation, fixes, notebook evidence, and report integration were completed separately.

| Member | Contribution area | Contribution details | Supporting commit hashes |
| --- | --- | --- | --- |
| Xuejian Fang (`xfan0282`) | Task 1 cleaning | Implemented `extract_unit_column()` to separate measurement units from raw description text into a `unit` column and integrate the step into the Task 1 cleaning workflow. | `9d830fb`, `677474a`, `f9a5488`, `6522ef5` |
| Xuejian Fang (`xfan0282`) | Task 1 statistics | Implemented and refined `xfan0282_1()` to `xfan0282_5()`, covering apartment share increase, work-from-home growth, public transport commute decline, occupation commute distance gap, and rent stress relative to mortgage stress. | `70a9ccf`, `463ca42` |
| Xuejian Fang (`xfan0282`) | Core pipeline and database | Built the project configuration, PostgreSQL/PostGIS schema, database indexes, workflow runner, Task 2 POI ingestion, Task 3 scoring, and correlation pipeline. | `b62b1cf`, `dbf4542`, `080fe59`, `d861094`, `2121936`, `afd0c09` |
| Xuejian Fang (`xfan0282`) | Task 4 visualisation and report integration | Implemented report visualisations, map outputs, dashboard/export support, member evidence notebooks, generated figures, and final report draft integration. | `32ec4d9`, `d7dcb3e`, `399e42f`, `f776326`, `fec66a4`, `f98d6af` |
| Daniel Kaiqi Bi (`dabi0142`) | Task 1 cleaning | Implemented and updated `clean_column_names()`, `clean_missing_values()`, `convert_numeric_columns()`, `reshape_wide_to_long()`, and `validate_and_flag_outliers()` for the early Task 1 cleaning pipeline. | `72eb43c`, `1968fb0`, `8767754`, `b64ec6d`, `90162d4`, `a370b3d` |
| Daniel Kaiqi Bi (`dabi0142`) | Task 1 statistics | Implemented and updated `dabi0142_1()` to `dabi0142_5()`, covering population growth rate, working-age population percentage, largest unemployment rate change, most volatile indicator, and longest increase streak. | `02169a2`, `bb809ab`, `4119216` |
| Daniel Kaiqi Bi (`dabi0142`) | Task 2/3 analysis and workflow support | Contributed Parramatta-focused analysis material and updated the shared workflow notebook used for end-to-end Task 2/3 evidence and report interpretation. | `bb809ab`, `4119216`, `b90603b`, `8fa7b44` |
| Daniel Kaiqi Bi (`dabi0142`) | Notebook and report support | Added project overview and analysis material, updated notebook analysis, and contributed to the shared full workflow notebook and report context. | `bb809ab`, `4119216`, `b90603b` |
| Jinyu Zhou (`jzho0172`) | Task 1 cleaning | Implemented `standardise_text_columns()` to trim text fields, convert empty strings to missing values, and connect the step to the Task 1 cleaning workflow. | `9382387` |
| Jinyu Zhou (`jzho0172`) | Task 1 statistics | Implemented `jzho0172_1()` to `jzho0172_5()`, covering estimated resident population growth, population density change, female population share, female-male population gap, and median male age change; also added Task 1 visualisation support. | `4bd37ac`, `37b626e` |
| Jinyu Zhou (`jzho0172`) | Task 2/3 workflow evidence support | Helped maintain and integrate the shared full workflow notebook, including notebook conflict resolution and group evidence material used alongside the Task 2/3 workflow outputs. | `4bd37ac`, `ec15663`, `5a0a739` |
| Jinyu Zhou (`jzho0172`) | Notebook and report support | Added notebook/report notes explaining the `jzho0172` cleaning step, statistics, and Task 1 findings; filled the final SA2 count for the member scope; also resolved notebook/report integration conflicts. | `5a0a739`, `606d9d1`, `d7f86df`, `ec15663`, `405cd14`, `4456a10` |
| Xuanhao Yu (`xuyu8020`) | Task 1 cleaning | Implemented `drop_missing_observations()` to remove missing long-format value rows after reshaping and fixed an index-handling issue in that step. | `97016f1`, `bb5fe5e` |
| Xuanhao Yu (`xuyu8020`) | Task 1 statistics | Implemented `xuyu8020_1()` to `xuyu8020_5()`, covering age dependency ratio, sex ratio, median total income growth, mean-to-median total income gap, and business net entry rate. | `4ac76d4` |
| Xuanhao Yu (`xuyu8020`) | Task 2/3 selected-SA4 analysis | Worked on the Sydney - Northern Beaches Task 2/3 analysis by updating the member notebook, adding key findings, adjusting report evidence values, and configuring the member SA4 scope. | `97be051`, `620c748`, `a7826b0`, `0fa1be3` |
| Xuanhao Yu (`xuyu8020`) | Notebook and report support | Added `xuyu8020` Task 1 notebook evidence, worked on the Sydney - Northern Beaches Task 2/3 analysis, filled pending report sections, adjusted evidence values, merged main into the report branch, and added key findings. | `97be051`, `620c748`, `a7826b0`, `0fa1be3`, `f55fae4`, `541587c` |

All members contributed to the shared report and group notebook evidence, while each member also maintained their own Task 1 cleaning function, Task 1 statistics module, and member-level notebook analysis.
