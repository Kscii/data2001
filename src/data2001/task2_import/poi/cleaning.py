from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from data2001.config import Settings
from data2001.task2_import.records import ArcGISFeature, PoiRecord, Sa2PopulationRecord


def arcgis_millis_to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC)
    except (OverflowError, OSError, TypeError, ValueError):
        return None


def normalize_coordinate(value: Any) -> float:
    return round(float(value), 12)


def clean_poi_feature(settings: Settings, feature: ArcGISFeature) -> PoiRecord | None:
    attrs = feature.get("attributes", {})
    geometry = feature.get("geometry", {})
    objectid = attrs.get("objectid")
    longitude = geometry.get("x")
    latitude = geometry.get("y")
    if objectid is None or longitude is None or latitude is None:
        return None

    poigroup_code = attrs.get("poigroup")
    poigroup_name = settings.poi.group_names.get(poigroup_code)

    return PoiRecord(
        objectid=int(objectid),
        topoid=attrs.get("topoid"),
        poigroup_code=poigroup_code,
        poigroup_name=poigroup_name,
        poitype=attrs.get("poitype"),
        poiname=attrs.get("poiname"),
        poilabel=attrs.get("poilabel"),
        poilabeltype=attrs.get("poilabeltype"),
        poialtlabel=attrs.get("poialtlabel"),
        poisourcefeatureoid=attrs.get("poisourcefeatureoid"),
        accesscontrol=attrs.get("accesscontrol"),
        startdate=arcgis_millis_to_datetime(attrs.get("startdate")),
        enddate=arcgis_millis_to_datetime(attrs.get("enddate")),
        lastupdate=arcgis_millis_to_datetime(attrs.get("lastupdate")),
        msoid=attrs.get("msoid"),
        centroidid=attrs.get("centroidid"),
        shapeuuid=attrs.get("shapeuuid"),
        changetype=attrs.get("changetype"),
        processstate=attrs.get("processstate"),
        urbanity=attrs.get("urbanity"),
        longitude=normalize_coordinate(longitude),
        latitude=normalize_coordinate(latitude),
    )


def parse_population_feature(settings: Settings, feature: ArcGISFeature) -> Sa2PopulationRecord:
    attrs = feature["attributes"]
    return Sa2PopulationRecord(
        sa2_code=attrs.get(settings.population.sa2_code_field),
        population=attrs.get(settings.population.population_field),
        population_density=attrs.get(settings.population.population_density_field),
    )
