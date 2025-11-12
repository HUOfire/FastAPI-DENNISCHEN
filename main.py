from fastapi import FastAPI
import uvicorn, os, logging
from apps import FilesManage
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html

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

# 挂载本地静态资源
if os.path.exists("static/swagger-ui"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(FilesManage, prefix="/files", tags=["文件管理"])


@app.get("/docs", summary="Swagger UI", tags=["接口文档"], include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,  # 隐藏模型部分
            "docExpansion": "none",  # 默认折叠所有操作
            "filter": True,  # 启用搜索过滤
            "showExtensions": True,
            "persistAuthorization": True  # 保持认证状态
        }
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)