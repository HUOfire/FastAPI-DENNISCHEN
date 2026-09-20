"""文件管理路由。

修复内容：
- 路径遍历漏洞：所有传入路径都会被 realpath 校验在 UPLOAD_DIR 内；
- 函数名覆盖：原代码两个 browse_files 同名，第二个改为 browse_files_view；
- 默认参数陷阱：去掉 Response() 默认值；
- 路径拼接使用 os.path.join(*parts)；
- 增加认证依赖，所有接口需要登录。
"""
import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from security.cookie import get_current_user
from security.setting import settings

FilesManage = APIRouter()
FilesManage.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = os.path.realpath(settings.upload_dir)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _safe_join(*parts: str) -> str:
    """把用户传入的相对路径安全拼接到 UPLOAD_DIR 下，并校验不越界。"""
    # 允许单段为空
    cleaned = [p for p in parts if p]
    candidate = os.path.realpath(os.path.join(UPLOAD_DIR, *cleaned))
    # 必须以 UPLOAD_DIR + 分隔符 开头，防止形如 Z:/evil.txt 并列目录被访问
    if not (candidate == UPLOAD_DIR or candidate.startswith(UPLOAD_DIR + os.sep)):
        raise HTTPException(status_code=403, detail="非法路径访问")
    return candidate


@FilesManage.get(
    "/browse/{path:str}/{vcr:str}",
    response_class=HTMLResponse,
    summary="获取目录文件列表详情",
)
async def browse_files(
    path: str = "",
    vcr: str = "",
    user: dict = Depends(get_current_user),
):
    full_path = _safe_join(path, vcr)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        raise HTTPException(404, detail="目录不存在")

    items_html = []
    rel_base = f"{path}/{vcr}".strip("/")
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        rel = f"{rel_base}/{item}" if rel_base else item
        kind = " (文件)" if os.path.isfile(item_path) else " (目录)"
        items_html.append(
            f'<li><a href="/files/preview/{rel}">{item}</a>{kind}</li>'
        )

    return f"""
    <html>
        <head>
            <title>文件浏览器</title>
            <link href="/static/style.css" rel="stylesheet">
        </head>
        <body>
            <ul>{''.join(items_html)}</ul>
        </body>
    </html>
    """


@FilesManage.get("/preview/{filepath:path}", summary="文件预览/下载接口")
async def preview_file(
    filepath: str,
    user: dict = Depends(get_current_user),
):
    full_path = _safe_join(filepath)
    if not os.path.exists(full_path):
        raise HTTPException(404, detail="文件不存在")

    if os.path.isdir(full_path):
        # 目录浏览：拆分路径复用 browse_files 逻辑
        rel = os.path.relpath(full_path, UPLOAD_DIR)
        parts = rel.split(os.sep)
        path_part = parts[0] if len(parts) >= 1 else ""
        vcr_part = os.path.join(*parts[1:]) if len(parts) >= 2 else ""
        return await browse_files(path_part, vcr_part, user)

    lower = filepath.lower()
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")):
        return FileResponse(full_path)
    if lower.endswith(".pdf"):
        return FileResponse(full_path, media_type="application/pdf")
    if lower.endswith((".txt", ".log", ".md", ".json", ".csv", ".xml", ".html", ".py", ".js", ".css")):
        return FileResponse(full_path, media_type="text/plain; charset=utf-8")
    return FileResponse(full_path, filename=os.path.basename(full_path))


@FilesManage.get("/KTEST/", summary="判断文件是否存在接口")
async def check_file_exists(
    request: Request,
    response: Response,
    path: Optional[str] = None,
    vcr: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    if not path or not vcr:
        raise HTTPException(status_code=400, detail="缺少 path 或 vcr 参数")

    full_path = _safe_join(path, vcr)
    if not os.path.exists(full_path):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status_code": 404, "title": "失败", "message": "路径不存在"}
    response.status_code = status.HTTP_200_OK
    return {"status_code": 200, "title": "成功", "message": "路径存在"}


@FilesManage.get(
    "/browse-view/{path:str}/{vcr:str}",
    response_class=HTMLResponse,
    summary="附件浏览页",
)
async def browse_files_view(
    request: Request,
    path: str = "",
    vcr: str = "",
    user: dict = Depends(get_current_user),
):
    full_path = _safe_join(path, vcr)
    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        raise HTTPException(404, detail="目录不存在")

    base_url = str(request.base_url)
    rel_base = f"{path}/{vcr}".strip("/")
    items = []
    for item_id, item in enumerate(os.listdir(full_path), start=1):
        rel = f"{rel_base}/{item}" if rel_base else item
        items.append(
            {
                "id": item_id,
                "src": f"{base_url}files/preview/{rel}",
                "alt": item,
            }
        )
    return templates.TemplateResponse(
        "viewport.html",
        context={
            "request": request,
            "items": json.dumps(items),
            "vals": {"path": path, "vcr": vcr},
        },
    )
