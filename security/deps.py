"""通用依赖：登录速率限制等。

采用「内存滑动窗口」实现简单的 IP 限流，避免引入 redis 等重依赖；
生产环境建议切换为 slowapi + redis backend。
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Depends, HTTPException, Request, status


# ---------- IP 登录限流：单 IP 每分钟最多 5 次登录尝试 ----------
_LOGIN_WINDOW_SEC = 60
_LOGIN_MAX_ATTEMPTS = 5
_login_attempts: Dict[str, Deque[float]] = defaultdict(deque)


def login_rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    dq = _login_attempts[ip]

    # 丢弃窗口外的旧记录
    while dq and now - dq[0] > _LOGIN_WINDOW_SEC:
        dq.popleft()

    if len(dq) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过于频繁，请 {_LOGIN_WINDOW_SEC} 秒后再试",
        )
    dq.append(now)
