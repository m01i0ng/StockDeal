import logging
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db import init_db
from app.exceptions import FundAccountNotFoundError, FundNotFoundError
from app.logging_config import bind_trace_id, reset_trace_id, setup_logging
from app.routers.fund_account_controller import router as fund_account_router
from app.routers.fund_controller import router as fund_router
from app.routers.fund_holding_controller import router as fund_holding_router
from app.routers.stock_controller import router as stock_router
from app.services.cache import close_redis, warm_up_cache
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.stock import stock_service

setup_logging(
    log_file=settings.log_file,
    log_level=settings.log_level,
    max_bytes=settings.log_max_bytes,
    backup_count=settings.log_backup_count,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    start_scheduler()
    if settings.cache_warmup_enabled:
        thread = threading.Thread(
            target=warm_up_cache,
            kwargs={"timeout": 80.0},
            daemon=True,
        )
        thread.start()
    yield
    close_redis()
    stock_service.close_nowapi_client()
    stop_scheduler()


app = FastAPI(
    title="Fund Snapshot API",
    version="0.1.0",
    description="提供基金与股票的实时行情、历史净值与持仓快照查询接口。",
    openapi_tags=[
        {"name": "funds", "description": "基金相关接口"},
        {"name": "fund-accounts", "description": "基金账户接口"},
        {"name": "fund-holdings", "description": "基金持仓与交易接口"},
        {"name": "stocks", "description": "股票相关接口"},
    ],
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)
app.include_router(fund_router)
app.include_router(fund_account_router)
app.include_router(fund_holding_router)
app.include_router(stock_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    trace_id = (
        request.headers.get("X-Trace-Id")
        or request.headers.get("X-Request-Id")
        or str(uuid.uuid4())
    )
    token = bind_trace_id(trace_id)
    request.state.trace_id = trace_id
    logger = logging.getLogger("app.request")
    start_time = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "请求异常 method=%s path=%s duration_ms=%.2f client=%s",
            request.method,
            request.url.path,
            duration_ms,
            request.client.host if request.client else "-",
        )
        raise
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code if response else 500
        if response is not None:
            response.headers["X-Trace-Id"] = trace_id
        logger.info(
            "请求完成 method=%s path=%s status=%s duration_ms=%.2f client=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request.client.host if request.client else "-",
        )
        reset_trace_id(token)


@app.exception_handler(FundNotFoundError)
async def handle_fund_not_found(_: FastAPI, exc: FundNotFoundError) -> JSONResponse:
    logging.getLogger("app.error").exception("基金未找到: %s", exc)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(FundAccountNotFoundError)
async def handle_account_not_found(
    _: FastAPI, exc: FundAccountNotFoundError
) -> JSONResponse:
    logging.getLogger("app.error").exception("基金账户未找到: %s", exc)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def handle_value_error(_: FastAPI, exc: ValueError) -> JSONResponse:
    logging.getLogger("app.error").exception("请求参数错误: %s", exc)
    return JSONResponse(status_code=400, content={"detail": str(exc)})
