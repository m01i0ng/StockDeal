from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.models.schemas import StockMarket, StockRealtimeQuoteResponse
from app.services.cache import get_stock_quote_cache, set_stock_quote_cache
from app.utils.parsing import parse_float


def _normalize_code(code: str) -> str:
    return str(code).strip().upper()


def _resolve_market(code: str) -> StockMarket:
    pure_code = code.replace("SH", "").replace("SZ", "").replace("BJ", "")
    if pure_code.isdigit() and len(pure_code) == 5:
        return StockMarket.h_share
    if pure_code.isdigit() and len(pure_code) == 6:
        return StockMarket.a_share
    raise ValueError(f"无法识别股票代码: {code}")


def _build_nowapi_symbol(symbol: str, market: StockMarket) -> str:
    pure_code = symbol.replace("SH", "").replace("SZ", "").replace("BJ", "")
    if market == StockMarket.h_share:
        return f"hk{pure_code}"
    if not symbol.startswith(("SH", "SZ", "BJ")):
        if pure_code.startswith("6"):
            return f"sh{pure_code}"
        if pure_code.startswith(("0", "3")):
            return f"sz{pure_code}"
        if pure_code.startswith(("8", "4")):
            return f"bj{pure_code}"
    if symbol.startswith("SH"):
        return f"sh{pure_code}"
    if symbol.startswith("SZ"):
        return f"sz{pure_code}"
    if symbol.startswith("BJ"):
        return f"bj{pure_code}"
    return f"sh{pure_code}"


def _get_nowapi_config() -> tuple[str, str, str]:
    appkey = settings.nowapi_appkey.strip()
    sign = settings.nowapi_sign.strip()
    base_url = settings.nowapi_base_url.strip()
    if not appkey or not sign:
        raise RuntimeError("NowAPI 配置缺失，请设置 NOWAPI_APPKEY 与 NOWAPI_SIGN")
    return appkey, sign, base_url


_nowapi_client: httpx.Client | None = None


def _get_nowapi_client() -> httpx.Client:
    """获取复用的 HTTP 客户端，减少连接建立开销。"""
    global _nowapi_client
    if _nowapi_client is not None:
        return _nowapi_client
    _nowapi_client = httpx.Client(
        timeout=8.0,
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    )
    return _nowapi_client


def close_nowapi_client() -> None:
    """关闭复用的 HTTP 客户端。"""
    global _nowapi_client
    if _nowapi_client is None:
        return
    _nowapi_client.close()
    _nowapi_client = None


def _request_nowapi(symbol: str) -> dict[str, Any]:
    appkey, sign, base_url = _get_nowapi_config()
    query = urlencode(
        {
            "app": "finance.stock_realtime",
            "stoSym": symbol,
            "appkey": appkey,
            "sign": sign,
            "format": "json",
        }
    )
    url = f"{base_url}/?{query}"
    client = _get_nowapi_client()
    response = client.get(url)
    response.raise_for_status()
    return response.json()


def _extract_nowapi_quote(payload: dict[str, Any]) -> tuple[float | None, float | None]:
    quote_map = _extract_nowapi_quotes(payload)
    if not quote_map:
        return None, None
    return next(iter(quote_map.values()))


def _extract_nowapi_quotes(
    payload: dict[str, Any],
) -> dict[str, tuple[float | None, float | None]]:
    if str(payload.get("success")) != "1":
        message = payload.get("msg") or "NowAPI 请求失败"
        raise RuntimeError(str(message))
    result = payload.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("NowAPI 返回结果缺失")
    lists = result.get("lists")
    if not isinstance(lists, dict) or not lists:
        return {}
    output: dict[str, tuple[float | None, float | None]] = {}
    for key, row in lists.items():
        if not isinstance(row, dict):
            continue
        latest_price = parse_float(row.get("last_price"))
        change_percent = parse_float(row.get("rise_fall_per"))
        output[str(key)] = (latest_price, change_percent)
    return output


def get_stock_realtime_quotes(
    codes: list[str],
) -> dict[str, StockRealtimeQuoteResponse]:
    output: dict[str, StockRealtimeQuoteResponse] = {}
    pending_symbols: dict[str, str] = {}
    pending_markets: dict[str, StockMarket] = {}

    for code in codes:
        symbol = _normalize_code(code)
        market = _resolve_market(symbol)
        pure_code = symbol.replace("SH", "").replace("SZ", "").replace("BJ", "")
        cached = get_stock_quote_cache(pure_code)
        if isinstance(cached, dict):
            output[code] = StockRealtimeQuoteResponse(
                code=pure_code,
                market=StockMarket(cached.get("market", market.value)),
                latest_price=cached.get("latest_price"),
                change_percent=cached.get("change_percent"),
            )
            continue
        nowapi_symbol = _build_nowapi_symbol(symbol, market)
        pending_symbols[code] = nowapi_symbol
        pending_markets[code] = market

    if pending_symbols:
        payload = _request_nowapi(",".join(pending_symbols.values()))
        quote_map = _extract_nowapi_quotes(payload)
        for code, nowapi_symbol in pending_symbols.items():
            market = pending_markets[code]
            symbol = _normalize_code(code)
            pure_code = symbol.replace("SH", "").replace("SZ", "").replace("BJ", "")
            latest_price, change_percent = quote_map.get(nowapi_symbol, (None, None))
            cache_payload = {
                "code": pure_code,
                "market": market.value,
                "latest_price": latest_price,
                "change_percent": change_percent,
            }
            set_stock_quote_cache(pure_code, cache_payload)
            output[code] = StockRealtimeQuoteResponse(
                code=pure_code,
                market=market,
                latest_price=latest_price,
                change_percent=change_percent,
            )

    return output


def get_stock_realtime_quote(code: str) -> StockRealtimeQuoteResponse:
    quotes = get_stock_realtime_quotes([code])
    if code not in quotes:
        raise RuntimeError("NowAPI 返回结果缺失")
    return quotes[code]
