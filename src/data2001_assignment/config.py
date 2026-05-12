"""读取 YAML 配置, 并把配置整理成项目统一使用的 Settings 对象."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Literal

import yaml

from data2001_assignment.common.paths import DEFAULT_CONFIG_PATH, resolve_project_path


CrawlScope = Literal["greater_sydney", "selected_sa4", "explicit_sa4_codes"]
ScoreUniverse = Literal["selected_sa4", "greater_sydney"]


@dataclass(frozen=True)
class DatabaseSettings:
    """数据库连接配置."""
    driver: str
    host: str
    port: int
    database: str
    user: str
    password: str
    schema_name: str


@dataclass(frozen=True)
class LayerSettings:
    """单个 ArcGIS layer 的字段和 metadata 契约配置."""
    url: str
    geometry_type: str | None
    expected_srid: int | None
    expected_fields: list[str]
    out_fields: list[str]

    @property
    def metadata_url(self) -> str:
        """返回当前 query endpoint 对应的 layer metadata URL."""
        if self.url.endswith("/query"):
            return self.url[: -len("/query")]
        return self.url


@dataclass(frozen=True)
class APISettings:
    """ArcGIS API 全局配置和 layer 查找方法."""
    layers: dict[str, LayerSettings]
    page_size: int
    timeout_seconds: int
    max_retries: int
    sleep_seconds: float
    out_sr: int

    def layer(self, name: str) -> LayerSettings:
        """按名称读取某个 ArcGIS layer 的配置."""
        try:
            return self.layers[name]
        except KeyError as exc:
            raise KeyError(f"配置中缺少 api.layers.{name}") from exc


@dataclass(frozen=True)
class POISettings:
    """POI 类型映射配置."""
    group_names: dict[int, str]


@dataclass(frozen=True)
class SpatialSettings:
    """空间归属策略配置."""
    assignment_method: str
    database_srid: int


@dataclass(frozen=True)
class MaintenanceSettings:
    """数据库维护命令的安全配置."""
    require_yes: bool


@dataclass(frozen=True)
class Task2Settings:
    """Task 2 抓取范围和 SA4 选择配置."""
    crawl_scope: CrawlScope
    gccsa_name: str
    selected_sa4_by_member: dict[str, str]
    sa4_codes: list[str]
    clean_batch_size: int


@dataclass(frozen=True)
class ScoringSettings:
    """Task 3 score 口径和阈值配置."""
    score_universe: ScoreUniverse
    min_population: int
    output_scale: int
    score_version: str


@dataclass(frozen=True)
class PopulationSettings:
    """SA2 population layer 的字段映射配置."""
    sa2_code_field: str
    population_field: str
    population_density_field: str


@dataclass(frozen=True)
class IncomeSettings:
    """SA2 median income 数据源和过滤阈值配置."""
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
    """score-income correlation 检验方法配置."""
    enabled: bool
    method: str
    robustness_method: str
    alpha: float


@dataclass(frozen=True)
class OutputSettings:
    """项目输出路径配置."""
    figures_dir: str
    raw_poi_response_dir: str
    raw_poi_features_jsonl: str
    raw_task1_csv: str
    processed_task1_cleaned_csv: str


@dataclass(frozen=True)
class FigureSettings:
    """report PNG 图表导出配置."""
    format: str
    width: int
    height: int
    scale: int
    map_engine: str
    top_n: int
    score_histogram_nbins: int


@dataclass(frozen=True)
class ProgressSettings:
    """终端进度输出配置."""
    enabled: bool
    bbox_log_interval: int


@dataclass(frozen=True)
class DashboardSettings:
    """Dash 只读 dashboard 的运行配置."""
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
class PipelineSettings:
    """可用 pipeline steps 和默认启用 steps 配置."""
    steps_available: list[str]
    steps_enabled: list[str]


@dataclass(frozen=True)
class Settings:
    """项目总配置对象, 聚合数据库、接口、pipeline 和可视化配置."""
    database: DatabaseSettings
    api: APISettings
    poi: POISettings
    spatial: SpatialSettings
    maintenance: MaintenanceSettings
    task2: Task2Settings
    scoring: ScoringSettings
    population: PopulationSettings
    income: IncomeSettings
    correlation: CorrelationSettings
    outputs: OutputSettings
    figures: FigureSettings
    progress: ProgressSettings
    dashboard: DashboardSettings
    pipeline: PipelineSettings


def _coerce_env_value(value: str, target_type: type) -> Any:
    """把环境变量字符串转换成配置字段需要的类型."""
    if target_type is int:
        return int(value)
    return value


def _apply_database_env_overrides(database_data: dict[str, Any]) -> dict[str, Any]:
    """允许容器环境覆盖数据库连接；YAML 仍是本地开发的默认来源."""
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
    """读取 YAML 文件, 并把空文件统一当作空配置."""
    config_path = resolve_project_path(path)
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    """读取一个顶层配置段, 并确认它是 mapping."""
    if name not in data:
        raise KeyError(f"配置文件缺少顶层配置项: {name}")
    value = data[name]
    if not isinstance(value, dict):
        raise TypeError(f"配置项 {name} 必须是一个 mapping")
    return value


def load_settings(path: str | Path = DEFAULT_CONFIG_PATH) -> Settings:
    """读取 YAML 并返回后续 pipeline 统一使用的配置对象."""
    data = _load_yaml(path)
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

    database_data = _section(data, "database")
    if "schema" in database_data and "schema_name" not in database_data:
        database_data["schema_name"] = database_data.pop("schema")
    database_data = _apply_database_env_overrides(database_data)

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
        maintenance=MaintenanceSettings(**_section(data, "maintenance")),
        task2=Task2Settings(**_section(data, "task2")),
        scoring=ScoringSettings(**_section(data, "scoring")),
        population=PopulationSettings(**_section(data, "population")),
        income=IncomeSettings(**_section(data, "income")),
        correlation=CorrelationSettings(**_section(data, "correlation")),
        outputs=OutputSettings(**_section(data, "outputs")),
        figures=FigureSettings(**_section(data, "figures")),
        progress=ProgressSettings(**_section(data, "progress")),
        dashboard=DashboardSettings(**_section(data, "dashboard")),
        pipeline=PipelineSettings(**_section(data, "pipeline")),
    )
