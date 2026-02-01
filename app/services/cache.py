from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import timedelta
from typing import Any, Callable

import akshare as ak
import pandas as pd
import redis
from redis.exceptions import RedisError

from app.config import settings

FUND_LIST_CACHE_KEY = "fund:list"
FUND_BASIC_INFO_CACHE_PREFIX = "fund:basic_info"
FUND_HOLDINGS_CACHE_PREFIX = "fund:latest_holdings"
FUND_ESTIMATE_CACHE_PREFIX = "fund:realtime_estimate"
STOCK_QUOTE_CACHE_PREFIX = "stock:realtime_quote"

_CACHE_TTL = timedelta(minutes=30)
_FUND_BASIC_INFO_TTL = timedelta(hours=12)
_FUND_HOLDINGS_TTL = timedelta(hours=6)
_FUND_ESTIMATE_TTL = timedelta(minutes=1)
_STOCK_QUOTE_TTL = timedelta(seconds=30)
_redis_client: redis.Redis | None = None
_logger = logging.getLogger(__name__)


def _build_cache_key(prefix: str, code: str) -> str:
    return f"{prefix}:{code}"


def _get_or_set_cache(
    key: str,
    loader: Callable[[], Any],
    getter: Callable[[str], Any | None],
    setter: Callable[[str, Any], None],
    should_cache: Callable[[Any], bool] | None = None,
) -> Any:
    cached = getter(key)
    if cached is not None:
        return cached
    data = loader()
    if should_cache is None or should_cache(data):
        setter(key, data)
    return data


def _get_redis_client() -> redis.Redis | None:
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    redis_url = settings.redis_url
    try:
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
    except RedisError as exc:
        _logger.warning("Redis 客户端初始化失败: %s", exc)
        _redis_client = None
    return _redis_client


def close_redis() -> None:
    global _redis_client
    if _redis_client is None:
        return
    try:
        _redis_client.close()
    except RedisError as exc:
        _logger.warning("关闭 Redis 连接失败: %s", exc)
    finally:
        _redis_client = None


def _get_json_cache(key: str) -> Any | None:
    client = _get_redis_client()
    if client is None:
        return None
    try:
        cached = client.get(key)
    except RedisError as exc:
        _logger.warning("读取 Redis 缓存失败: %s", exc)
        return None
    if not cached:
        return None
    try:
        return json.loads(cached)
    except json.JSONDecodeError:
        _logger.warning("Redis 缓存 JSON 解析失败: %s", key)
        return None


def _set_json_cache(key: str, data: Any, ttl: timedelta) -> None:
    client = _get_redis_client()
    if client is None:
        return
    try:
        payload = json.dumps(data, ensure_ascii=True)
    except TypeError as exc:
        _logger.warning("Redis 缓存序列化失败: %s", exc)
        return
    try:
        client.set(key, payload, ex=int(ttl.total_seconds()))
    except RedisError as exc:
        _logger.warning("写入 Redis 缓存失败: %s", exc)


def _get_or_set_json_cache(
    key: str,
    loader: Callable[[], Any],
    ttl: timedelta,
    expected_type: type,
) -> Any:
    def _getter(cache_key: str) -> Any | None:
        cached = _get_json_cache(cache_key)
        return cached if isinstance(cached, expected_type) else None

    def _setter(cache_key: str, data: Any) -> None:
        _set_json_cache(cache_key, data, ttl)

    return _get_or_set_cache(
        key,
        loader,
        _getter,
        _setter,
        should_cache=lambda data: isinstance(data, expected_type),
    )


def _load_fund_list_records() -> list[dict[str, Any]]:
    fund_df = ak.fund_name_em()
    return fund_df.to_dict("records")


def get_fund_list_cache() -> pd.DataFrame:
    cached = _get_or_set_json_cache(
        FUND_LIST_CACHE_KEY,
        _load_fund_list_records,
        _CACHE_TTL,
        list,
    )
    if not cached:
        _logger.warning("基金列表缓存为空，返回空 DataFrame")
        return pd.DataFrame()
    return pd.DataFrame(cached)


def get_fund_basic_info_cache(
    code: str,
    loader: Callable[[], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    key = _build_cache_key(FUND_BASIC_INFO_CACHE_PREFIX, code)
    return _get_or_set_json_cache(key, loader, _FUND_BASIC_INFO_TTL, list)


def get_fund_latest_holdings_cache(
    code: str,
    loader: Callable[[], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    key = _build_cache_key(FUND_HOLDINGS_CACHE_PREFIX, code)
    return _get_or_set_json_cache(key, loader, _FUND_HOLDINGS_TTL, list)


def get_fund_realtime_estimate_cache(
    code: str,
    loader: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    key = _build_cache_key(FUND_ESTIMATE_CACHE_PREFIX, code)
    return _get_or_set_json_cache(key, loader, _FUND_ESTIMATE_TTL, dict)


def get_stock_quote_cache(
    code: str,
    loader: Callable[[], dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    key = _build_cache_key(STOCK_QUOTE_CACHE_PREFIX, code)
    if loader is None:
        cached = _get_json_cache(key)
        return cached if isinstance(cached, dict) else None
    return _get_or_set_json_cache(key, loader, _STOCK_QUOTE_TTL, dict)


def set_stock_quote_cache(code: str, data: dict[str, Any]) -> None:
    key = _build_cache_key(STOCK_QUOTE_CACHE_PREFIX, code)
    _set_json_cache(key, data, _STOCK_QUOTE_TTL)


def _safe_load(name: str, loader: Callable[[], pd.DataFrame]) -> None:
    try:
        loader()
        _logger.info("缓存加载完成: %s", name)
    except Exception as exc:
        _logger.warning("缓存加载失败: %s, 错误: %s", name, exc)


def warm_up_cache(timeout: float | None = None) -> None:
    """应用启动时预加载全量数据"""
    tasks = [
        ("fund_list", get_fund_list_cache),
    ]
    if timeout is None:
        for name, loader in tasks:
            _safe_load(name, loader)
        return
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {
            executor.submit(_safe_load, name, loader): name for name, loader in tasks
        }
        for future, name in futures.items():
            try:
                future.result(timeout=timeout)
            except TimeoutError:
                _logger.warning("缓存加载超时: %s", name)
            except Exception as exc:
                _logger.warning("缓存加载异常: %s, 错误: %s", name, exc)
