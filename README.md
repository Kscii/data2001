# DATA2001 Group Assignment

![python](https://img.shields.io/badge/python-3.12-blue)
![uv](https://img.shields.io/badge/uv-managed-green)
![postgresql](https://img.shields.io/badge/postgresql%20%2B%20postgis-enabled-blue)
![dashboard](https://img.shields.io/badge/visual-dashboard-purple)

## Project Links

- Dashboard: https://kscii.tech
- Repository: https://github.sydney.edu.au/xfan0282/data2001-group-assignment

## Requirements

Before running the project, make sure these tools are available:

- git: clone the repository and work with branches.
- python3.12: the Python version used by the project.
- uv: Python dependency manager and command runner.
- podman: run the local PostgreSQL/PostGIS container.
- podman compose or docker compose: start the database from `compose.yml`.
- Jupyter support: open and run `notebooks/full_workflow.ipynb`.
- Chrome or Kaleido-managed Chrome: export Plotly report figures as PNG files.

## Quick Start

### 1. Install uv and Podman

Install uv on macOS:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Check that uv is available
uv --version
```

Install uv on Windows PowerShell:

```powershell
# Install uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Check that uv is available
uv --version
```

Install Podman on macOS:

```bash
# Install Podman
brew install podman

# Initialise and start the Podman virtual machine
podman machine init
podman machine start

# Check that Podman is available
podman info
```

Install Podman on Windows:

```powershell
# Install Podman with winget
winget install RedHat.Podman

# Initialise and start the Podman virtual machine
podman machine init
podman machine start

# Check that Podman is available
podman info
```

### 2. Install Python Dependencies

```bash
# Install Python dependencies and create the .venv environment
uv sync
```

Some IDEs may require manual environment activation:

```bash
# Linux/macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

### 3. Create Local Configuration

```bash
# Copy the example configuration to the local configuration path
cp configs/example.yaml configs/local.yaml
```

### 4. Start the PostGIS Database

```bash
# Start the local PostgreSQL/PostGIS container from compose.yml
podman compose up -d
```

```bash
# Initialise schema, extensions, tables, and indexes
uv run data2001 init-db

# Check database connection, PostGIS, tables, and SRID
uv run data2001 check-db
```

### 5. Run the Main Workflow

```bash
# Preview the SA4, SA2, and bbox import plan without requesting the POI API
uv run data2001 plan-import
```

```bash
# Run the workflow steps enabled in the configuration
uv run data2001 run-workflow
```

```bash
# Generate PNG charts used by the report
uv run data2001 generate-figures
```

```bash
# If no local Chrome is available, let Plotly/Kaleido install one
uv run plotly_get_chrome
```

### 6. Open the Notebook and Dashboard

```text
Open notebooks/full_workflow.ipynb in an IDE or Jupyter.
On first launch, select the Python interpreter from the .venv environment created by uv.
```

```bash
# Start the local visual dashboard server
uv run data2001 dashboard
# Then open the port printed in the terminal.
```

Deployed dashboard:

```text
https://kscii.tech
```

## Common Commands

- `uv run data2001 init-db`: initialise schema, extensions, tables, and indexes.
- `uv run data2001 check-db`: check database connection, PostGIS, tables, and SRID.
- `uv run data2001 plan-import`: print the planned SA4, SA2, and bbox crawl without requesting the POI API.
- `uv run data2001 import-boundaries`: fetch and store SA2/SA4 boundaries and population.
- `uv run data2001 validate-boundaries`: validate that imported SA2 polygons belong to their expected SA4 polygons.
- `uv run data2001 import-poi`: fetch raw POI JSON, clean POI records, and store them in the database.
- `uv run data2001 import-income`: fetch and store SA2 median income data.
- `uv run data2001 compute-score`: recompute the well-resourced score and income correlation.
- `uv run data2001 run-workflow`: run the configured end-to-end workflow.
- `uv run data2001 generate-figures`: export PNG figures used by the report.
- `uv run data2001 dashboard`: start the visual dashboard.
- `uv run data2001 clear-db --yes`: clear business table contents while keeping schema, tables, and indexes.
- `uv run data2001 reset-db --yes`: drop the schema and reinitialise the database.

```bash
# Run the workflow with an explicit configuration file
uv run data2001 --config configs/local.yaml run-workflow
```

## Technology Stack

- python3.12 + uv: dependency management and command runner.
- pandas / numpy / scipy: data cleaning, score calculation, and statistical tests.
- requests: ArcGIS REST API client.
- PostgreSQL + PostGIS: data import, spatial indexes, and spatial joins.
- sqlalchemy + psycopg: Python database access.
- plotly + kaleido: notebook figures and report PNG export.
- dash: visual dashboard.
- podman compose: local PostGIS development environment.

## Project Structure

```text
configs/                    YAML configuration for Tasks 2-4
data/raw/task1/             Task 1 raw CSV data
data/raw/poi_api/           POI raw JSON / JSONL output from Task 2 API extraction
docs/                       Design, database, container, and quick-start documentation
notebooks/                  Notebook workflow and member evidence
report/                     Final report draft and PNG figures
sql/                        PostGIS schema and indexes
src/data2001/               Main Python package
compose.yml                 Local PostGIS startup entry point
```

Core package layout:

```text
task1_cleaning/     CSV cleaning workflow (Task 1)
task1_statistics/   derived statistics workflow (Task 1)
task2_import/       API import, POI cleaning, spatial assignment (Task 2)
task3_score/        well-resourced score and correlation (Task 3)
task4/              notebook/report/dashboard shared charts (Task 4)
db/repositories/    database admin/read/write repository modules
```

## Documentation

- [API Reference](docs/api_reference.md): API endpoints, expected fields, field mappings, and persisted workflow files.
- [Architecture Design](docs/architecture_design.md): project structure, configuration flow, workflow steps, module boundaries, and call-chain diagrams.
- [Database Reference](docs/database_reference.md): database tables, keys, indexes, ERD, and spatial join design.

## Configuration

Default local configuration path:

```text
configs/local.yaml
```

The repository provides an example configuration:

```text
configs/example.yaml
```

Commonly edited settings:

- `database`: local PostgreSQL/PostGIS connection settings.
- `task2_import.crawl_scope`: controls whether the POI crawl uses Greater Sydney, selected SA4s, or explicit SA4 codes.
- `task2_import.selected_sa4_by_member`: maps each member unikey to the SA4 used for member-level analysis.
- `task3_score.min_population`: excludes very-low-population SA2 areas from score calculation.
- `task3_score.score_universe`: controls whether scores are calculated within selected SA4s or Greater Sydney.
- `income.min_income_earners`: filters SA2 income records with very small income samples.
- `outputs.charts_dir`: output directory for report PNG figures.

## Outputs

- Raw API files: `data/raw/poi_api/responses/` and `data/raw/poi_api/features.jsonl`.
- Database tables: `sa2`, `sa4`, `poi_clean`, `sa2_poi`, `sa2_score`, `sa2_income`, and `score_income_correlation`.
- Report figures: `report/figures/*.png`.
- Notebook workflow: `notebooks/full_workflow.ipynb` and member notebooks under `notebooks/<unikey>/`.
- Final report draft: `report/report.md`.

## Contributing

Do not push directly to the main branch. Create a feature branch for each change and open a pull request after the work is ready.

```bash
# Create a new branch
git checkout -b feat/your-feature
git add <files>
git commit -m "feat: describe your change"
git push

# After checking the branch on GitHub, open a pull request into the main branch.
```
