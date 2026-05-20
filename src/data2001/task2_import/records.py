from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


JsonObject = dict[str, Any]
ArcGISFeature = dict[str, Any]
ArcGISPayload = dict[str, Any]


@dataclass(frozen=True)
class Sa4AreaRecord:
    sa4_code: str | None
    sa4_name: str | None
    gccsa_code: str | None
    gccsa_name: str | None
    state_code: str | None
    state_name: str | None
    area_albers_sqkm: float | None
    asgs_loci_uri: str | None
    geometry_geojson: JsonObject
    bbox_minx: float
    bbox_miny: float
    bbox_maxx: float
    bbox_maxy: float

    def to_db_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Sa2AreaRecord:
    sa2_code: str | None
    sa2_name: str | None
    sa3_code: str | None
    sa3_name: str | None
    sa4_code: str | None
    sa4_name: str | None
    gccsa_code: str | None
    gccsa_name: str | None
    state_code: str | None
    state_name: str | None
    area_albers_sqkm: float | None
    asgs_loci_uri: str | None
    geometry_geojson: JsonObject
    bbox_minx: float
    bbox_miny: float
    bbox_maxx: float
    bbox_maxy: float

    def to_db_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BoundaryRecords:
    sa4: list[Sa4AreaRecord]
    sa2: list[Sa2AreaRecord]


@dataclass(frozen=True)
class Sa2PopulationRecord:
    sa2_code: str | None
    population: int | float | None
    population_density: int | float | None

    def to_db_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PoiRecord:
    objectid: int
    topoid: str | int | None
    poigroup_code: int | str | None
    poigroup_name: str | None
    poitype: str | None
    poiname: str | None
    poilabel: str | None
    poilabeltype: str | None
    poialtlabel: str | None
    poisourcefeatureoid: str | int | None
    accesscontrol: str | None
    startdate: datetime | None
    enddate: datetime | None
    lastupdate: datetime | None
    msoid: str | int | None
    centroidid: str | int | None
    shapeuuid: str | None
    changetype: str | int | None
    processstate: str | int | None
    urbanity: str | None
    longitude: float
    latitude: float

    def to_db_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Sa2IncomeRecord:
    sa2_code: str | None
    sa2_name: str | None
    income_earners_2022_23: int | float | None
    income_earners_2021_22: int | float | None
    income_earners_change: int | float | None
    income_earners_change_pct: int | float | None
    median_income_2022_23: int | float | None
    source_year: str
    source_name: str

    def to_db_dict(self) -> dict[str, Any]:
        return asdict(self)


def sa4_records_to_db_rows(records: list[Sa4AreaRecord]) -> list[dict[str, Any]]:
    return [record.to_db_dict() for record in records]


def sa2_records_to_db_rows(records: list[Sa2AreaRecord]) -> list[dict[str, Any]]:
    return [record.to_db_dict() for record in records]


def population_records_to_db_rows(records: list[Sa2PopulationRecord]) -> list[dict[str, Any]]:
    return [record.to_db_dict() for record in records]


def poi_records_to_db_rows(records: list[PoiRecord]) -> list[dict[str, Any]]:
    return [record.to_db_dict() for record in records]


def income_records_to_db_rows(records: list[Sa2IncomeRecord]) -> list[dict[str, Any]]:
    return [record.to_db_dict() for record in records]
