# 项目简介

本项目提供基金与股票的查询接口，包含基金快照、历史净值与实时预估净值等功能，并提供 Swagger 文档。

## 功能说明

- 基金快照：返回基金基本信息、最新净值与最新季度持仓。
- 历史净值：按周期查询基金历史净值（支持一周/一月/三月/一年/成立以来）。
- 实时预估净值：基于基金最新持仓与股票实时涨跌幅，估算基金当前涨幅与预估净值。
- 股票实时行情：按股票代码获取实时行情。
- 基金转换：同一账户内基金转换，生成转出与转入两笔交易记录。

## 配置说明

### 环境变量

- `REDIS_URL`：Redis 连接地址，默认 `redis://localhost:6379/0`。
- `DATABASE_URL`：完整 MySQL 连接地址（优先生效），配置后会忽略下方 `MYSQL_*`。
- `MYSQL_HOST`：MySQL 主机，默认 `localhost`。
- `MYSQL_PORT`：MySQL 端口，默认 `3306`。
- `MYSQL_USER`：MySQL 用户名，默认 `root`。
- `MYSQL_PASSWORD`：MySQL 密码，默认 `password`。
- `MYSQL_DATABASE`：数据库名，默认 `stock_deal`。
- `NOWAPI_APPKEY`：NowAPI AppKey，用于股票行情请求。
- `NOWAPI_SIGN`：NowAPI Sign，用于股票行情请求。
- `NOWAPI_BASE_URL`：NowAPI 接口地址，默认 `https://sapi.k780.com`。
- `DB_AUTO_MIGRATE`：启动时是否自动执行数据库迁移，默认 `true`。
- `CACHE_WARMUP_ENABLED`：启动时是否预热缓存，默认 `true`。
- `SCHEDULER_ENABLED`：是否启用定时任务，默认 `true`。
- `SCHEDULER_CONFIRM_HOUR`：定时任务执行小时（24 小时制），默认 `15`。
- `SCHEDULER_CONFIRM_MINUTE`：定时任务执行分钟，默认 `5`。
- `LOG_LEVEL`：日志级别，默认 `INFO`。
- `LOG_FILE`：日志文件路径，默认 `logs/app.log`。
- `LOG_MAX_BYTES`：单个日志文件最大字节数（滚动），默认 `10485760`。
- `LOG_BACKUP_COUNT`：保留的日志文件数量，默认 `10`。

> 建议将所有配置写入项目根目录的 `.env` 文件，应用启动时会自动加载。

### .env 示例

```env
REDIS_URL=redis://localhost:6379/0
# DATABASE_URL=完整连接地址，优先生效
# DATABASE_URL=mysql+pymysql://user:password@localhost:3306/stock_deal
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=stock_deal
NOWAPI_APPKEY=your_appkey
NOWAPI_SIGN=your_sign
NOWAPI_BASE_URL=https://sapi.k780.com
DB_AUTO_MIGRATE=true
CACHE_WARMUP_ENABLED=true
SCHEDULER_ENABLED=true
SCHEDULER_CONFIRM_HOUR=15
SCHEDULER_CONFIRM_MINUTE=5
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=10
```

### 日志与 Trace ID 说明

- 服务默认写入文件日志，路径由 `LOG_FILE` 控制，启动时会自动创建目录。
- 每次请求会自动生成 `trace_id`，也可通过请求头传入：
   - `X-Trace-Id`（优先使用）
   - `X-Request-Id`（兼容）
- 响应会回写 `X-Trace-Id`，方便链路追踪。

### 依赖服务

- Redis：用于缓存基金列表、基金基本信息、持仓、实时行情与预估净值数据。

## 净值计算原理

实时预估净值的计算逻辑如下：

1. 获取基金最新季度持仓，并解析每只股票的占净值比例。
2. 批量获取持仓股票的实时涨跌幅（百分比）。
3. 对每只股票计算贡献值：

   ```math
   	ext{贡献值}_i = \text{持仓占比}_i \times \frac{\text{股票涨跌幅}_i}{100}
   ```

4. 将所有股票贡献值求和，得到基金预估涨幅：

   ```math
   	ext{预估涨幅} = \sum_{i=1}^{n} \text{贡献值}_i
   ```

5. 根据最新净值计算预估净值：

   ```math
   	ext{预估净值} = \text{最新净值} \times \left(1 + \frac{\text{预估涨幅}}{100}\right)
   ```

若某只股票缺失行情，则该股票会进入 `skipped` 列表，不参与贡献值计算。

## 接口文档

- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

### 基金转换接口

- `POST /fund-holdings/conversions`：创建基金转换，生成转出/转入两笔交易记录。
- `GET /fund-holdings/conversions?account_id=1`：查询账户下的转换记录。

请求字段要点：

- `from_amount`/`to_amount` 分别对应转出/转入金额。
- `from_fee_percent`/`to_fee_percent` 分别对应转出/转入手续费比例（百分比）。
- `trade_time` 用于确认 15:00 前后净值日期。

## Docker 构建与运行

### 构建镜像

```bash
docker build -t stock-deal .
```

### 运行容器

```bash
docker run --rm -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e MYSQL_HOST=host.docker.internal \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=root \
  -e MYSQL_PASSWORD=password \
  -e MYSQL_DATABASE=stock_deal \
  -e NOWAPI_APPKEY=your_appkey \
  -e NOWAPI_SIGN=your_sign \
  -e CACHE_WARMUP_ENABLED=true \
  stock-deal
```

如需连接本地 Redis，请确保 Docker 能访问宿主机地址（macOS 可使用 `host.docker.internal`）。

## Docker Compose

### 启动服务

```bash
export NOWAPI_APPKEY=your_appkey
export NOWAPI_SIGN=your_sign
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=password
export MYSQL_DATABASE=stock_deal
export CACHE_WARMUP_ENABLED=true
docker compose up --build
```

### 访问接口

- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`
