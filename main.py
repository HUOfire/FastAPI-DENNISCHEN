"""FastAPI-DENNISCHEN 应用入口。

优化点：
- 使用 add_middleware 注册中间件，避免每个请求实例化;
- 增加 /health 健康检查端点;
- 全局异常处理;
- reload 根据环境变量自动开关。
"""
import os

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from apilog import LogMiddleware, logs_router, openapi_protect_middleware
from apps import FilesManage
from security import cok_router, jwt_router
from security.cookie import templates
from security.setting import settings


app = FastAPI(
    title="FastAPI-接口文档",
    description="DENNISCHEN - FastAPI 接口文档",
    version="1.1.0",
    docs_url=None,
    redoc_url=None,
)

# ---- 中间件注册（顺序：先注册的外层包装） ----
app.add_middleware(LogMiddleware)
app.middleware("http")(openapi_protect_middleware)

# ---- 静态资源 ----
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---- 路由 ----
app.include_router(FilesManage, prefix="/files", tags=["文件管理"])
app.include_router(jwt_router, tags=["JWT认证管理"])  # 勿加前缀，否则影响 OAuth2 tokenUrl
app.include_router(cok_router, tags=["Cookie认证管理"])
app.include_router(logs_router, prefix="/apilog", tags=["日志管理"])


# ---- 健康检查 ----
@app.get("/health", summary="健康检查", tags=["系统"])
async def health():
    return {"status": "ok", "env": settings.env}


# ---- 首页 ----
@app.get("/", summary="跳转登录页", response_class=HTMLResponse, tags=["Cookie认证管理"])
async def goto_login_page(request: Request):
    return templates.TemplateResponse(
        "pageto.html",
        context={"request": request, "login_tip": "前往登录"},
    )


# ---- 全局异常处理 ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"code": 422, "detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"code": 500, "detail": "服务器内部错误"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=not settings.is_production,
    )
