"""统一入口：支持 `python main.py` 启动服务。"""

import uvicorn


def main() -> None:
    """启动 FastAPI 应用。"""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
