# data2001 group assignment

![python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/uv-managed-green)
![postgresql](https://img.shields.io/badge/postgresql%20%2B%20postgis-enabled-blue)
![dashboard](https://img.shields.io/badge/visual-dashboard-purple)

## project links

- Dashboard: https://kscii.tech
- Repository: https://github.sydney.edu.au/xfan0282/data2001-group-assignment

## 项目依赖

使用本项目之前, 请确保电脑上有这些工具:

- git: 拉取代码和提交分支.
- python3.12: 项目运行的python版本.
- uv: python dependency manager和命令运行工具.
- podman: 本地启动postgresql/postgis容器.
- podman compose或docker compose: 用`compose.yml`启动数据库.
- jupyter支持: 用于打开`notebooks/full_workflow.ipynb`.
- chrome或kaleido管理的chrome: 用于导出report png figures.

## quick start

### 1. 安装uv和podman

macos安装uv:

```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 检查uv是否可用
uv --version
```

windows powershell安装uv:

```powershell
# 安装uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 检查uv是否可用
uv --version
```

macos安装podman:

```bash
# 安装podman
brew install podman

# 初始化并启动podman virtual machine
podman machine init
podman machine start

# 检查podman是否可用
podman info
```

windows安装podman:

```powershell
# 使用winget安装podman
winget install RedHat.Podman

# 初始化并启动podman virtual machine
podman machine init
podman machine start

# 检查podman是否可用
podman info
```

### 2. 安装python依赖和创建虚拟环境

```bash
# 仓库路径下安装python依赖并创建.venv
uv sync
```

部分ide需要手动进入环境

```bash
# linux/macos
source .venv/bin/activate
```

```powershell
# windows powershell
.venv\Scripts\Activate.ps1
```

### 3. 创建本地配置

```bash
# 直接把example配置复制成local配置即可
cp configs/example.yaml configs/local.yaml
```

### 4. 启动postgis数据库

```bash
# 使用compose.yml一键启动本地postgresql/postgis容器
podman compose up -d
```

```bash
# 初始化schema, extension, table和index
uv run data2001 init-db

# 检查数据库连接, postgis, table和srid
uv run data2001 check-db
```

### 5. 运行主流程

```bash
# 先查看当前配置会抓取哪些sa4, sa2和bbox
uv run data2001 plan-import
```

```bash
# 一键运行配置中启用的 workflow steps
uv run data2001 run-workflow
```

```bash
# 生成 report 使用的 PNG charts
uv run data2001 generate-figures
```

```bash
# 如果当前设备没有可用chrome, 可以让plotly/kaleido安装本地chrome
uv run plotly_get_chrome
```

### 6. 查看notebook和dashboard

```text
在ide或jupyter中打开notebooks/full_workflow.ipynb
第一次启动要选择python解释器, 选择之前创建的虚拟环境就可以了
```

```bash
# 本地启动visual dashboard服务器
uv run data2001 dashboard
# 然后浏览器打开终端中显示的端口
```

部署后的 dashboard 地址:

```text
https://kscii.tech
```

## 常用命令

- `uv run data2001 init-db`: 初始化schema, extension, table, index.
- `uv run data2001 check-db`: 检查数据库, postgis, 表和srid.
- `uv run data2001 plan-import`: 打印将要抓取的sa4 / sa2 / bbox, 不请求poi api.
- `uv run data2001 import-boundaries`: 抓取并入库sa2/sa4 boundary和population.
- `uv run data2001 import-poi`: 抓取poi raw json, 并清洗入库.
- `uv run data2001 import-income`: 抓取并入库sa2 median income.
- `uv run data2001 compute-score`: 重新计算score和income correlation.
- `uv run data2001 run-workflow`: 执行配置中的完整主流程.
- `uv run data2001 generate-figures`: 导出report使用的png figures.
- `uv run data2001 dashboard`: 启动visual dashboard.
- `uv run data2001 clear-db --yes`: 清空业务表内容, 保留schema/table/index.
- `uv run data2001 reset-db --yes`: 删除schema后重新初始化.

```bash
# 使用指定配置文件运行 workflow
uv run data2001 --config configs/local.yaml run-workflow
```

## 技术栈

- python3.12 + uv: dependency management和command runner.
- pandas / numpy / scipy: data cleaning, score calculation和statistical test.
- requests: arcgis rest api client.
- postgresql + postgis: data import, spatial index和spatial join.
- sqlalchemy + psycopg: python database access.
- plotly + kaleido: notebook figures和report png.
- dash: visual dashboard.
- podman compose: 本地postgis开发环境.

## 项目结构

```text
configs/                    yaml配置 (task2-4 configuration)
data/raw/task1/             task1 csv raw data
data/raw/poi_api/           poi raw json / jsonl (task2 api extraction)
docs/                       设计, 数据库, 容器和快速上手文档
notebooks/                  notebook workflow (task1-4 explanation)
report/                     final report和png figures (task4)
sql/                        postgis schema和indexes (database schema / indexing)
src/data2001/               python package主体
compose.yml                 本地postgis启动入口 (data import)
```

核心package:

```text
task1_cleaning/     CSV cleaning workflow (Task 1)
task1_statistics/   derived statistics workflow (Task 1)
task2_import/       API import, POI cleaning, spatial assignment (Task 2)
task3_score/        well-resourced score and correlation (Task 3)
task4/              notebook/report/dashboard shared charts (Task 4)
db/repositories/    database admin/read/write repository modules
```

## 配置说明

默认配置路径:

```text
configs/local.yaml
```

仓库提供示例:

```text
configs/example.yaml
```

常见需要修改的配置:

- `database`: 本地postgresql/postgis连接信息. (data import)
- `task2_import.crawl_scope`: 控制抓取greater sydney, selected sa4或explicit sa4 codes. (task2 / api extraction)
- `task2_import.selected_sa4_by_member`: 记录unikey到sa4的映射, 便于member-level analysis. (task4 / results analysis)
- `task3_score.min_population`: 过滤人口过低的sa2. (task3 / score calculation)
- `task3_score.score_universe`: 控制score在selected sa4集合或greater sydney内计算. (task3 / score calculation)
- `income.min_income_earners`: 过滤income sample过小的sa2. (correlation analysis)
- `outputs.charts_dir`: report png输出目录. (task4 / data visualisations)

## 输出内容

- raw api files: `data/raw/poi_api/responses/`和`data/raw/poi_api/features.jsonl`. (task2 / api extraction)
- database tables: `sa2`, `sa4`, `poi_clean`, `sa2_poi`, `sa2_score`, `sa2_income`, `score_income_correlation`. (database schema / spatial join / score calculation)
- report figures: `report/figures/*.png`. (task4 / data visualisations)
- notebook workflow: `notebooks/full_workflow.ipynb`. (task1-4 explanation)
- final report draft: `report/final_report.md`. (task4 / results analysis)

## 贡献方式

不要直接push到主分支.建议每个功能开独立分支, 完成后创建pull request.

```bash
# 创建新分支
git checkout -b feat/your-feature
git add <files>
git commit -m "feat: describe your change"
git push

# 在github上检查没问题后, 再创建pull request合并到主分支.
```
