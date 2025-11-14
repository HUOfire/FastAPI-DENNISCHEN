import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jwt.exceptions import InvalidTokenError

from .setting import Config as St, LoginRequest, UserInDB
from .stdjwt import password_hash

cok_router = APIRouter()

# 安全性依赖
security = HTTPBearer(auto_error=False)


# 挂载本地静态资源
cok_router.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.now() + datetime.timedelta(minutes=St.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, St.SECRET_KEY, algorithm=St.ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, St.SECRET_KEY, algorithms=[St.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except InvalidTokenError:
        return None


# Cookie 认证依赖
async def get_current_user(request: Request):
    token = request.cookies.get("auth_token")

    if not token:
        # 也检查 Authorization 头，方便 API 调用
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    username = verify_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return {"username": username, "role": "user"}


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def authenticate_user(fake_db, username: str, password: str):
    # 简单的用户验证逻辑 - 在实际应用中应该查询数据库
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return {"username": user.username, "role": user.role}


@cok_router.post("/api/login")
async def login(login_data: LoginRequest, response: Response):
    user_role = authenticate_user(St.fake_users_db,login_data.username, login_data.password)
    if not user_role:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 创建 JWT token
    access_token = create_access_token(data={"sub": user_role["username"]})

    # 设置 HttpOnly Cookie
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        max_age=St.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=False,  # 开发环境设为 False，生产环境设为 True
        samesite="lax",
        path="/"
    )

    return {
        "message": "登录成功",
        "user": user_role,
        "token_type": "bearer"
    }

# 注销登录
@cok_router.post("/api/logout")
async def logout(response: Response):
    # 清除 Cookie
    response.delete_cookie(
        key="auth_token",
        path="/"
    )
    return {"message": "退出登录成功"}

# 验证登录状态
@cok_router.get("/api/verify")
async def verify_token_endpoint(user: dict = Depends(get_current_user)):
    return {"valid": True, "user": user}

# 受保护的 API
@cok_router.get("/api/protected-data")
async def get_protected_data(user: dict = Depends(get_current_user)):
    return {
        "message": "这是受保护的数据",
        "user": user,
        "data": ["敏感数据1", "敏感数据2", "敏感数据3"]
    }


# 文档页面保护
@cok_router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def protected_docs(
        user: dict = Depends(get_current_user)
):
    """受 Cookie 保护的 API 文档页面"""
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="受保护的API文档",
        swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui/swagger-ui.css",
        swagger_favicon_url="/static/swagger-ui/favicon.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1, # 隐藏模型部分
            "docExpansion": "none", # 隐藏文档折叠按钮
            "filter": True, # 开启过滤功能
            "showExtensions": True, # 显示扩展按钮
            "persistAuthorization": True # 记住授权状态
        }
    )


# 公开的登录页面
@cok_router.get("/login", response_class=HTMLResponse)
async def goto_login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        context={
            'request': request,
            'login_tip': '用户登录'
        }
    )

@cok_router.get("/index", summary="登录页面", response_class=HTMLResponse)
async def read_item(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "index.html",
        context={
            'request': request,
            'login_tip': '用户登录'
        }
    )