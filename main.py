import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from apilog import logs_router
from apilog.log_middleware import log_record, openapi_protect_middleware
from apps import FilesManage
from security import jwt_router, cok_router
from security.cookie import templates


# 创建FastAPI实例
app = FastAPI(
    title="FastAPI-接口文档",
    description="DENNISCHEN - FastAPI接口文档",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

# 添加日志中间件
app.middleware("http")(log_record)                    # 日志中间件
app.middleware("http")(openapi_protect_middleware)    # 拦截限制访问中间件

# 挂载本地静态资源
app.mount("/static", StaticFiles(directory="static"), name="static")

# prefix路由路径会影响前端获取服务根路径,如需调整,还需在对应路由下的templates前端页面文件调整调用的static路径
app.include_router(FilesManage, prefix="/files", tags=["文件管理"])
app.include_router(jwt_router, tags=["JWT认证管理"]) # 该路由不能加前缀,否则会导致验证失败
app.include_router(cok_router, tags=["Cookie认证管理"])
app.include_router(logs_router,prefix="/apilog", tags=["日志管理"])


@app.get("/", summary="跳转页面", response_class=HTMLResponse, tags=["Cookie认证管理"])
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