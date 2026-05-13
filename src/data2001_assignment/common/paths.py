"""项目路径常量和相对路径解析工具."""
from pathlib import Path


# 从当前文件向上回到仓库根目录：src/data2001_assignment/common/paths.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORT_DIR = PROJECT_ROOT / "report"
CHARTS_DIR = REPORT_DIR / "figures"
SQL_DIR = PROJECT_ROOT / "sql"
DOCS_DIR = PROJECT_ROOT / "docs"

DEFAULT_CONFIG_PATH = CONFIG_DIR / "local.yaml"


def resolve_project_path(path: str | Path) -> Path:
    """把相对路径解析成基于项目根目录的绝对路径."""
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate
