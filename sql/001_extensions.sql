-- 初始化 PostGIS.compose 使用 postgis/postgis 镜像时通常可以直接创建.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS {schema};
