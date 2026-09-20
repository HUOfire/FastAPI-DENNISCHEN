"""HTTP 日志中间件 + openapi.json 保护中间件。"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Union

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .log_config import LoggedPaths, SensitiveKeys, setup_logging
from security.setting import settings

logger: logging.Logger = setup_logging()
SENSITIVE_KEYS = SensitiveKeys.KEYS
LOGGED_PATHS = LoggedPaths.PATHS


# ===================== 脱敏 =====================
def mask_sensitive_data(data: Any) -> Any:
    """递归脱敏 dict / list 中的敏感字段。"""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if isinstance(k, str) and k.lower() in SENSITIVE_KEYS:
                masked[k] = "***MASKED***"
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data


def _safe_json_loads(raw: Union[bytes, str]) -> Any:
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(text)
    except Exception:
        return None


# ===================== 日志中间件 =====================
class LogMiddleware(BaseHTTPMiddleware):
    """记录指定路径的请求/响应体与耗时。"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        url = request.url.path
        method = request.method

        should_log = any(url.startswith(p) for p in LOGGED_PATHS)
        if not should_log:
            return await call_next(request)

        # 读取请求体并脱敏
        body_bytes = await request.body()
        request_body = _safe_json_loads(body_bytes)
        if request_body is None:
            request_body = {"raw": body_bytes.decode("utf-8", errors="replace")[:500]}
        safe_request = mask_sensitive_data(request_body)

        # 调用下游
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "Request Error: %s %s | Error: %s", method, url, str(e)
            )
            raise

        # 读取响应体并脱敏
        status_code = response.status_code
        response_body_bytes = b""
        if hasattr(response, "body_iterator"):
            async for chunk in response.body_iterator:
                response_body_bytes += chunk
            new_response = Response(
                content=response_body_bytes,
                status_code=status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        else:
            response_body_bytes = getattr(response, "body", b"") or b""
            new_response = response

        resp_body = _safe_json_loads(response_body_bytes)
        if resp_body is None:
            resp_body = {"raw": response_body_bytes.decode("utf-8", errors="replace")[:500]}
        safe_response = mask_sensitive_data(resp_body)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            json.dumps(
                {
                    "url": url,
                    "method": method,
                    "request": safe_request,
                    "status": status_code,
                    "response": safe_response,
                    "duration": duration_ms,
                    "client_ip": request.client.host if request.client else "",
                },
                ensure_ascii=False,
            )
        )
        return new_response


# ===================== openapi.json 保护 =====================
async def openapi_protect_middleware(request: Request, call_next):
    """限制 openapi.json 仅允许白名单 IP 访问；路径做规范化处理防绕过。"""
    normalized_path = request.url.path.rstrip("/") or "/"
    if normalized_path == "/openapi.json":
        client_ip = request.client.host if request.client else ""
        if client_ip not in settings.openapi_allowed_ip_list:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access to openapi.json is forbidden"},
            )
    return await call_next(request)
