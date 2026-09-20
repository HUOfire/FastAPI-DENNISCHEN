"""日志查询接口：倒序读取、分页、过滤，避免全量载入内存。"""
import json
import os
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from security.cookie import get_current_user
from security.setting import settings

logs_router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 日志行格式: "2026-09-20 12:34:56 - INFO - {...json...}"
_LINE_RE = re.compile(
    r"^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*(?P<level>[A-Z]+)\s*-\s*(?P<body>.*)$"
)


def _parse_line(line: str) -> Optional[dict]:
    line = line.strip()
    if not line:
        return None
    m = _LINE_RE.match(line)
    if not m:
        return None
    try:
        body = json.loads(m.group("body"))
    except json.JSONDecodeError:
        return None
    body["time"] = m.group("time")
    body["level"] = m.group("level")
    return body


def _tail_read(log_file: str, max_lines: int) -> List[str]:
    """从文件末尾倒序读取最多 max_lines 行（不把整个文件读入内存）。"""
    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
        return []

    with open(log_file, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 8192
        data = b""
        lines_found = 0
        pos = size

        while pos > 0 and lines_found <= max_lines:
            read_size = min(block, pos)
            pos -= read_size
            f.seek(pos)
            data = f.read(read_size) + data
            lines_found = data.count(b"\n")

        text = data.decode("utf-8", errors="replace")
        return text.splitlines()


def read_logs(
    str_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[str] = None,
    url: Optional[str] = None,
    page: int = 1,
    page_size: int = 100,
) -> List[dict]:
    log_file = settings.log_file
    if not os.path.exists(log_file):
        return []

    raw_lines = _tail_read(log_file, max_lines=5000)  # 最多回溯最近 5000 行
    parsed: List[dict] = []
    for line in raw_lines:
        entry = _parse_line(line)
        if not entry:
            continue
        # 过滤条件
        log_date = entry["time"][:10]
        if str_date and log_date < str_date:
            continue
        if end_date and log_date > end_date:
            continue
        if level and level != "全部" and entry.get("level") != level:
            continue
        if url and entry.get("url") != url:
            continue
        parsed.append(entry)

    # 倒序（最新在前）+ 分页
    parsed.reverse()
    start = (page - 1) * page_size
    end = start + page_size
    return parsed[start:end]


@logs_router.get("/get_logs", summary="查询日志")
async def get_logs(
    str_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    level: Optional[str] = Query(None, description="日志级别"),
    url: Optional[str] = Query(None, description="URL 路径精确匹配"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=500, description="每页数量"),
    user: dict = Depends(get_current_user),
):
    logs = read_logs(str_date, end_date, level, url, page, page_size)
    return {"code": 200, "info": "success", "message": logs, "page": page, "page_size": page_size}


@logs_router.get("/logs", summary="日志查看页面", response_class=HTMLResponse)
async def logs_page(request: Request, user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "logs.html", context={"request": request, "user": user}
    )
