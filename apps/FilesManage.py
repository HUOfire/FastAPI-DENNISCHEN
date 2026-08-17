import os
import json
from fastapi import APIRouter, HTTPException, status, Response, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 文件存储目录
UPLOAD_DIR = "Z:/"

# 文件管理系统API路由
FilesManage = APIRouter()


# 挂载本地静态资源
FilesManage.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@FilesManage.get("/browse/{path:str}/{vcr:str}", response_class=HTMLResponse, summary="获取目录文件列表详情")
async def browse_files(path: str = "", vcr: str = ""):
    """文件目录浏览接口"""
    full_path = os.path.join(os.path.join(UPLOAD_DIR, path), vcr)
    if not os.path.exists(full_path):
        raise HTTPException(404, detail="目录不存在")

    items = []
    for item in os.listdir(full_path):
        item_path = os.path.join(full_path, item)
        items.append({
            "name": item,
            "is_file": os.path.isfile(item_path),
            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
            "path": os.path.join(f"{path}/{vcr}", item)
        })

    return f"""
    <html>
        <head>
            <title>文件浏览器</title>
            <link href="/static/style.css" rel="stylesheet">
        </head>
        <body>
            <!--<h1>文件浏览器</h1>-->
            <ul>
                {"".join([
        f'<li><a href="/preview/{item["path"]}">{item["name"]}</a>'
        f'{" (文件)" if item["is_file"] else " (目录)"}</li>'
        for item in items
    ])}
            </ul>
        </body>
    </html>
    """


@FilesManage.get("/preview/{filepath:path}", summary="文件预览下载接口")
async def preview_file(filepath: str):
    """文件预览接口"""
    full_path = os.path.join(UPLOAD_DIR, filepath)
    if not os.path.exists(full_path):
        raise HTTPException(404, detail="文件不存在")

    if os.path.isdir(full_path):
        return await browse_files(filepath)

    # 根据文件类型返回不同响应
    if filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return FileResponse(full_path, media_type="image/*")
    elif filepath.lower().endswith('.pdf'):
        return FileResponse(full_path, media_type="application/pdf")
    else:
        return FileResponse(full_path, media_type="text/plain")


@FilesManage.get("/KTEST/", summary="判断文件是否存在接口正式版")
async def test(path: str = None, vcr: str = None, response: Response = Response()):
    """判断文件是否存在接口"""
    full_path = os.path.join(os.path.join(UPLOAD_DIR, path), vcr)
    if not os.path.exists(full_path):
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status_code": 404, "title": "失败", "message": "目录不存在"}
    else:
        response.status_code = status.HTTP_200_OK
        return {"status_code": 200, "title": "成功", "message": "存在文件"}


@FilesManage.get("/browse-view/{path:str}/{vcr:str}", response_class=HTMLResponse, summary="获取目录文件列表详情")
async def browse_files(request: Request, path: str = "", vcr: str = ""):
    """文件目录浏览接口"""
    base_url = str(request.base_url)
    full_path = os.path.join(os.path.join(UPLOAD_DIR, path), vcr)
    if not os.path.exists(full_path):
        raise HTTPException(404, detail="目录不存在")

    items = []
    for item in os.listdir(full_path):
        item_id = 1
        items.append({
            "id": item_id,
            "alt": item,
            "src": f"{base_url}files/preview/{path}/{vcr}/{item}"
        })
        item_id += 1
    json_data = json.dumps(items)
    print(json_data)
    return templates.TemplateResponse(
        "viewport.html",
        context={
            'request': request,
            'items': json_data
        }
    )