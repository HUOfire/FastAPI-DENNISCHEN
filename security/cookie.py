"""Cookie 认证路由（含页面路由）。"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .deps import login_rate_limit
from .setting import LoginRequest, settings
from .jwt_utils import (
    UserInDB,
    authenticate_user,
    create_access_token,
    decode_access_token,
    get_user,
)

cok_router = APIRouter()
cok_router.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# ===================== 当前用户依赖 =====================
async def get_current_user(request: Request) -> dict:
    """从 Cookie 或 Authorization 头获取当前登录用户。"""
    token: Optional[str] = request.cookies.get("auth_token")

    # 兼容 API 调用的 Bearer 头
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user_in_db = get_user(settings.fake_users_db, username)
    if not user_in_db:
        raise HTTPException(status_code=401, detail="用户不存在")

    exp_timestamp = payload.get("exp")
    expire_dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc) if exp_timestamp else None
    return {
        "username": username,
        "role": user_in_db.role,
        "expire_datetime": expire_dt,
    }


# ===================== 登录 / 注销 =====================
@cok_router.post("/api/login", summary="登录操作")
async def login(
    login_data: LoginRequest,
    response: Response,
    _: None = Depends(login_rate_limit),  # 登录接口限流
):
    user = authenticate_user(settings.fake_users_db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    access_token = create_access_token(data={"sub": user.username})

    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        max_age=settings.access_token_expire_minutes * 60,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return {
        "message": "登录成功",
        "user": {"username": user.username, "role": user.role},
        "token_type": "bearer",
    }


@cok_router.post("/api/logout", summary="注销操作")
async def logout(response: Response):
    response.delete_cookie(key="auth_token", path="/")
    return {"message": "退出登录成功"}


@cok_router.get("/api/verify", summary="验证登录状态")
async def verify_token_endpoint(user: dict = Depends(get_current_user)):
    return {"valid": True, "user": user}


@cok_router.get("/api/protected-data", summary="受保护数据示例")
async def get_protected_data(user: dict = Depends(get_current_user)):
    return {
        "message": "这是受保护的数据",
        "user": user,
        "data": ["敏感数据1", "敏感数据2", "敏感数据3"],
    }


# ===================== 页面路由 =====================
@cok_router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def protected_docs(user: dict = Depends(get_current_user)):
    """受 Cookie 保护的 API 文档页面。"""
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="受保护的API文档",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "docExpansion": "none",
            "filter": True,
            "showExtensions": True,
            "persistAuthorization": True,
        },
    )
    return html.body.decode("utf-8")


@cok_router.get("/login", summary="登录页面", response_class=HTMLResponse)
async def goto_login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        context={"request": request, "login_tip": "用户登录"},
    )


@cok_router.get("/index", summary="主页", response_class=HTMLResponse)
async def index_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "index.html", context={"request": request, "user": user}
    )


@cok_router.get("/docs_iframe", summary="文档页", response_class=HTMLResponse)
async def docs_iframe_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "docs.html", context={"request": request, "user": user}
    )
