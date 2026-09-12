import logging
import time
import json
import re
from . import log_config

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

SENSITIVE_KEYS = log_config.Sensitive_Keys.SENSITIVE_KEYS
LOGGED_PATHS = log_config.Logged_Paths.LOGGED_PATHS
logger = log_config.setup_logging()

def mask_sensitive_data(data):
    """
    递归处理字典或列表，对敏感字段值进行脱敏
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                new_dict[key] = "&zwnj;***MASKED***&zwnj;"
            else:
                new_dict[key] = mask_sensitive_data(value)
        return new_dict
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    else:
        return data


def safe_desensitize_body(body_str: str, max_len: int = 2000) -> str:
    """
    安全地反序列化、脱敏并重新序列化 Body
    """
    if not body_str:
        return ""

    # 限制长度，防止超大 Body 导致性能问题
    if len(body_str) > max_len:
        return f"<Body Truncated, Length: {len(body_str)}>"

    try:
        # 尝试解析 JSON
        data = json.loads(body_str)
        # 执行脱敏
        masked_data = mask_sensitive_data(data)
        # 重新序列化为字符串
        return json.dumps(masked_data, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        # 如果不是 JSON，尝试简单的正则替换（针对 form-data 或纯文本）
        # 注意：正则替换不如 JSON 解析精准，仅作兜底
        masked_str = body_str
        for key in SENSITIVE_KEYS:
            # 匹配 key=value 或 "key": "value" 格式
            pattern = rf'("{key}"\s*:\s*"[^"]*"|{key}=[^&\s]*)'
            masked_str = re.sub(pattern, lambda m: m.group(0).split('=') + '=&zwnj;***' if '=' in m.group(
                0) else f'"{key}": "***&zwnj;"', masked_str, flags=re.IGNORECASE)
        return masked_str



class LogMiddleware(BaseHTTPMiddleware):
    """日志中间件"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # --- A. 获取请求信息 ---
        method = request.method
        url = str(request.url.path)

        # 判断是否需要记录详细日志
        should_log = any(url.startswith(logged_path) for logged_path in LOGGED_PATHS)
        if not should_log:
            # 如果不需记录，直接放行，减少开销
            return await call_next(request)

        # 读取请求 Body
        body_bytes = await request.body()

        try:
            request_body_raw = body_bytes.decode("utf-8")
        except Exception:
            request_body_raw = "<Binary Data>"

        # 【关键步骤】对请求 Body 进行脱敏
        safe_request_body = safe_desensitize_body(request_body_raw)

        # --- B. 执行后续处理 ---
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request Error: {method} {url} | Error: {str(e)}")
            raise e

        # --- C. 获取响应信息 ---
        status_code = response.status_code

        response_body_bytes = b""
        if hasattr(response, 'body_iterator'):
            async for chunk in response.body_iterator:
                response_body_bytes += chunk
            new_response = Response(
                content=response_body_bytes,
                status_code=status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        else:
            response_body_bytes = response.body
            new_response = response

        try:
            response_body_raw = response_body_bytes.decode("utf-8")
        except Exception:
            response_body_raw = "<Binary Data>"

        # 【关键步骤】对响应 Body 进行脱敏
        safe_response_body = safe_desensitize_body(response_body_raw)

        # --- D. 计算耗时 ---
        process_time = time.time() - start_time

        # --- E. 组装并记录日志 ---
        log_entry = {
            "path": url,
            "request_body": safe_request_body,
            "status_code": status_code,
            "response_body": safe_response_body,
            "duration_ms": round(process_time * 1000, 2)
        }

        logger.info(log_entry)
        return new_response


def log_record(request: Request, call_next):
    """日志记录中间件函数"""
    middleware = LogMiddleware(app = None)
    return middleware.dispatch(request, call_next)


async def openapi_protect_middleware(request: Request, call_next):
    # 仅拦截openapi.json路径
    if request.url.path == "/openapi.json":
        # 此处可替换为项目已有的JWT校验、IP白名单、内部服务鉴权逻辑
        is_internal_request = request.client.host in ["127.0.0.1","192.168.1.112"]
        if not is_internal_request:
            return JSONResponse(
                status_code=403,
                content={"detail": "Access to openapi.json is forbidden"}
            )
    response = await call_next(request)
    return response


