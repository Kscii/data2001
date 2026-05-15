# 数据库容器启动指南

本文档给组员本地开发使用，只说明如何在自己的电脑上启动 PostgreSQL/PostGIS 数据库。线上运行说明统一写在本地忽略的 `docs/deployment.md`。

项目默认数据库连接如下：

```text
host=localhost
port=5432
database=data2001
user=data2001
password=data2001
schema=data2001
```

这些值需要和 `configs/local.yaml`、`compose.yml` 保持一致。

## 1. 准备本地配置

在项目根目录复制示例配置：

```bash
cp configs/example.yaml configs/local.yaml
```

如果本机 5432 端口已经被其他 PostgreSQL 占用，可以修改 `compose.yml` 的 host port，并同步修改 `configs/local.yaml` 中的 `database.port`。

## 2. 安装 Podman

官方安装说明：

```text
https://podman.io/docs/installation
```

macOS 可以使用 Homebrew：

```bash
brew install podman
podman machine init
podman machine start
podman info
```

Windows 建议使用官方 installer。安装后在 PowerShell 中运行：

```powershell
podman machine init
podman machine start
podman info
```

常见 Linux：

```bash
# Arch / Manjaro
sudo pacman -S podman

# Ubuntu / Debian
sudo apt-get update
sudo apt-get -y install podman

# Fedora
sudo dnf -y install podman
```

## 3. 使用 Compose 启动数据库

这是组员本地开发推荐方式，macOS、Windows、Linux 都可以使用。

启动数据库：

```bash
podman compose up -d
```

查看状态和日志：

```bash
podman ps
podman logs data2001-postgis
```

停止数据库：

```bash
podman compose down
```

重新启动数据库：

```bash
podman compose up -d
```

如果需要完全重置容器数据，可以删除数据卷。这个命令会删除本地数据库内容：

```bash
podman compose down -v
```

如果使用 Docker，也可以运行：

```bash
docker compose up -d
docker compose down
```

## 4. 初始化项目数据库

数据库容器启动后，在项目根目录运行：

```bash
uv sync
uv run data2001 init-db
uv run data2001 check-db
```

`init-db` 会创建 schema、PostGIS extension、业务表和索引。`check-db` 用来确认数据库、PostGIS、表和 SRID 都可用。

如果 `check-db` 失败，先检查容器是否正在运行：

```bash
podman ps
podman logs data2001-postgis
```

## 5. 本地 smoke test

第一次运行建议先查看抓取计划：

```bash
uv run data2001 plan-import
```

确认范围没问题后，再运行完整 workflow：

```bash
uv run data2001 run-workflow
```

如果只想重新计算 score，可以运行：

```bash
uv run data2001 compute-score
```

如果需要清空业务表但保留 schema/table/index：

```bash
uv run data2001 clear-db --yes
```

如果需要删除 schema 后重新初始化：

```bash
uv run data2001 reset-db --yes
uv run data2001 init-db
```

## 6. 常见问题

如果端口冲突：

```text
症状：connection refused、address already in use、或 check-db 连接到错误数据库。
处理：修改 compose.yml 的 host port，并同步修改 configs/local.yaml 的 database.port。
```

如果容器名冲突：

```bash
podman rm -f data2001-postgis
podman compose up -d
```

如果配置文件不存在：

```bash
cp configs/example.yaml configs/local.yaml
```
