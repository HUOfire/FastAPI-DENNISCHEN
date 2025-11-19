import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from apps import FilesManage
from security import jwt_router, cok_router
from security.cookie import templates

# 配置标准库logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler()]
)

# 创建FastAPI实例
app = FastAPI(
    title="FastAPI-接口文档",
    description="DENNISCHEN - FastAPI接口文档",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# 设置跨域请求的白名单
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
]

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,    # 或使用 ["*"] 允许所有源
    allow_credentials=False,
    allow_methods=["*"],       # 允许所有HTTP方法
    allow_headers=["*"],       # 允许所有请求头
)

# 挂载本地静态资源
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(FilesManage, prefix="/files", tags=["文件管理"])
app.include_router(jwt_router, tags=["JWT认证管理"]) # 该路由不能加前缀，否则会导致验证失败
app.include_router(cok_router, tags=["Cookie认证管理"])

@app.get("/", summary="登录页面", response_class=HTMLResponse, tags=["Cookie认证管理"])
async def goto_login_page(request: Request):
    # print(request.method)
    return templates.TemplateResponse(
        "pageto.html",
        context={
            'request': request,
            'login_tip': '前往登录'
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)