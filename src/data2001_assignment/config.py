"""Load local YAML overrides and build the project Settings object."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Literal, cast

import yaml

from data2001_assignment.common.paths import DEFAULT_CONFIG_PATH, resolve_project_path
from data2001_assignment.defaults import DEFAULT_SETTINGS_DATA


CrawlScope = Literal["greater_sydney", "selected_sa4", "explicit_sa4_codes"]
ScoreUniverse = Literal["selected_sa4", "greater_sydney"]


@dataclass(frozen=True)
class DatabaseSettings:
    """Database connection settings."""
    driver: str
    host: str
    port: int
    database: str
    user: str
    password: str
    schema_name: str


@dataclass(frozen=True)
class LayerSettings:
    """ArcGIS layer contract and query fields."""
    url: str
    geometry_type: str | None
    expected_srid: int | None
    expected_fields: list[str]
    out_fields: list[str]

    @property
    def metadata_url(self) -> str:
        """Return the layer metadata URL for a query endpoint."""
        if self.url.endswith("/query"):
            return self.url[: -len("/query")]
        return self.url


@dataclass(frozen=True)
class APISettings:
    """ArcGIS API settings and layer lookup."""
    layers: dict[str, LayerSettings]
    page_size: int
    timeout_seconds: int
    max_retries: int
    sleep_seconds: float
    out_sr: int

    def layer(self, name: str) -> LayerSettings:
        """Return one configured ArcGIS layer by name."""
        try:
            return self.layers[name]
        except KeyError as exc:
            raise KeyError(f"Missing api.layers.{name}") from exc


@dataclass(frozen=True)
class POISettings:
    """POI group code lookup."""
    group_names: dict[int, str]


@dataclass(frozen=True)
class SpatialSettings:
    """Spatial assignment settings."""
    assignment_method: str
    database_srid: int


@dataclass(frozen=True)
class Task2ImportSettings:
    """Task 2 import area and batch settings."""
    crawl_scope: CrawlScope
    gccsa_name: str
    selected_sa4_by_member: dict[str, str]
    sa4_codes: list[str]
    clean_batch_size: int


@dataclass(frozen=True)
class Task3ScoreSettings:
    """Task 3 score settings."""
    score_universe: ScoreUniverse
    min_population: int
    output_scale: int
    score_version: str


@dataclass(frozen=True)
class PopulationSettings:
    """SA2 population field mapping."""
    sa2_code_field: str
    population_field: str
    population_density_field: str


@dataclass(frozen=True)
class IncomeSettings:
    """SA2 income field mapping and filters."""
    enabled: bool
    sa2_code_field: str
    sa2_name_field: str
    income_earners_current_field: str
    income_earners_previous_field: str
    income_earners_change_field: str
    income_earners_change_pct_field: str
    median_income_field: str
    min_income_earners: int
    source_year: str
    source_name: str


@dataclass(frozen=True)
class CorrelationSettings:
    """Score-income correlation settings."""
    enabled: bool
    method: str
    robustness_method: str
    alpha: float


@dataclass(frozen=True)
class OutputSettings:
    """Project output paths."""
    charts_dir: str
    raw_poi_response_dir: str
    raw_poi_features_jsonl: str
    raw_task1_csv: str
    processed_task1_cleaned_csv: str


@dataclass(frozen=True)
class ChartSettings:
    """Report chart export settings."""
    format: str
    width: int
    height: int
    scale: int
    map_engine: str
    top_n: int
    score_histogram_nbins: int


@dataclass(frozen=True)
class ProgressSettings:
    """Terminal progress settings."""
    enabled: bool
    bbox_log_interval: int


@dataclass(frozen=True)
class DashboardSettings:
    """Read-only Dash dashboard settings."""
    enabled: bool
    host: str
    port: int
    debug: bool
    title: str
    poi_limit: int | None
    default_top_n: int
    table_max_rows: int
    table_page_size: int


@dataclass(frozen=True)
class WorkflowSettings:
    """Enabled workflow steps."""
    enabled_steps: list[str]


@dataclass(frozen=True)
class Settings:
    """Project settings used by workflows and CLI commands."""
    database: DatabaseSettings
    api: APISettings
    poi: POISettings
    spatial: SpatialSettings
    task2_import: Task2ImportSettings
    task3_score: Task3ScoreSettings
    population: PopulationSettings
    income: IncomeSettings
    correlation: CorrelationSettings
    outputs: OutputSettings
    charts: ChartSettings
    progress: ProgressSettings
    dashboard: DashboardSettings
    workflow: WorkflowSettings


def merge_settings_data(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Deep merge local YAML overrides into the code defaults."""
    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_settings_data(cast(dict[str, Any], result[key]), value)
        else:
            result[key] = value
    return result


def _coerce_env_value(value: str, target_type: type) -> Any:
    """Convert environment variable strings to the target setting type."""
    if target_type is int:
        return int(value)
    return value


def _apply_database_env_overrides(database_data: dict[str, Any]) -> dict[str, Any]:
    """Allow container environment variables to override database settings."""
    env_mapping = {
        "DATA2001_DATABASE_DRIVER": ("driver", str),
        "DATA2001_DATABASE_HOST": ("host", str),
        "DATA2001_DATABASE_PORT": ("port", int),
        "DATA2001_DATABASE_NAME": ("database", str),
        "DATA2001_DATABASE_USER": ("user", str),
        "DATA2001_DATABASE_PASSWORD": ("password", str),
        "DATA2001_DATABASE_SCHEMA": ("schema_name", str),
    }
    result = dict(database_data)
    for env_name, (setting_name, target_type) in env_mapping.items():
        value = os.getenv(env_name)
        if value is not None:
            result[setting_name] = _coerce_env_value(value, target_type)
    return result


def _load_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file and treat an empty file as an empty mapping."""
    config_path = resolve_project_path(path)
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise TypeError("Config file must contain a YAML mapping")
    return data


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    """Read a top-level settings section as a mapping."""
    value = data.get(name)
    if not isinstance(value, dict):
        raise TypeError(f"Config section {name} must be a mapping")
    return value


def load_settings(path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    """Load code defaults, apply YAML overrides, and return Settings."""
    data = merge_settings_data(DEFAULT_SETTINGS_DATA, _load_yaml(path))

    database_data = _section(data, "database")
    if "schema" in database_data and "schema_name" not in database_data:
        database_data["schema_name"] = database_data.pop("schema")
    database_data = _apply_database_env_overrides(database_data)

    api_data = _section(data, "api")
    layer_data = _section(api_data, "layers")
    layers = {
        name: LayerSettings(**value)
        for name, value in layer_data.items()
    }
    api_data = {
        key: value
        for key, value in api_data.items()
        if key != "layers"
    }

    return Settings(
        database=DatabaseSettings(**database_data),
        api=APISettings(layers=layers, **api_data),
        poi=POISettings(
            group_names={
                int(key): value
                for key, value in _section(data, "poi")["group_names"].items()
            }
        ),
        spatial=SpatialSettings(**_section(data, "spatial")),
        task2_import=Task2ImportSettings(**_section(data, "task2_import")),
        task3_score=Task3ScoreSettings(**_section(data, "task3_score")),
        population=PopulationSettings(**_section(data, "population")),
        income=IncomeSettings(**_section(data, "income")),
        correlation=CorrelationSettings(**_section(data, "correlation")),
        outputs=OutputSettings(**_section(data, "outputs")),
        charts=ChartSettings(**_section(data, "charts")),
        progress=ProgressSettings(**_section(data, "progress")),
        dashboard=DashboardSettings(**_section(data, "dashboard")),
        workflow=WorkflowSettings(**_section(data, "workflow")),
    )
