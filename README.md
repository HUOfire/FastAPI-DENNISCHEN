# FastAPI-DENNISCHEN（已优化版）

基于 FastAPI 的管理平台脚手架，提供 JWT / Cookie 双模式认证、受保护的 Swagger 文档、文件浏览、访问日志等功能。

> 基于原项目 [HUOfire/FastAPI-DENNISCHEN](https://github.com/HUOfire/FastAPI-DENNISCHEN) 进行了安全、架构与工程化优化，详见文末《优化清单》。

**兼容 Python 3.8+**（已全部移除 `X | Y` 联合类型、`list[X]` 泛型下标等 3.9+ 语法，`Annotated` 通过 `typing_extensions` 兼容）

---

## 功能特性

- 🔐 **双认证模式**：OAuth2 Bearer Token + HttpOnly Cookie
- 🛡️ **受保护的 Swagger UI**：登录后通过 `/docs` 访问，`/openapi.json` 受 IP 白名单保护
- 📁 **文件浏览**：目录浏览、文件预览、图片/PDF/文本文件在线查看
- 📝 **访问日志**：按接口路径记录请求/响应体，自动脱敏敏感字段（password/token 等）
- ⚡ **登录限流**：单 IP 每分钟最多 5 次登录尝试，防暴力破解
- 🩺 **健康检查**：`/health` 端点便于运维探活

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制配置模板，按需修改（尤其生产环境务必更换 `SECRET_KEY`）：

```bash
cp .env.example .env
# 编辑 .env，重点修改：
#   ENV=production              （生产环境会自动开启 Cookie secure）
#   SECRET_KEY=你的随机密钥      （生成方式：openssl rand -hex 32）
#   UPLOAD_DIR=/path/to/files   （文件根目录）
#   OPENAPI_ALLOWED_IPS=127.0.0.1,10.0.0.1
```

### 3. 启动

```bash
python main.py
# 或
uvicorn main:app --host 0.0.0.0 --port 8000
```

开发模式会自动开启 `reload`；当 `ENV=production` 时自动关闭热重载并启用 Cookie `Secure` 标志。

### 4. 默认账号

| 字段 | 值 |
|------|-----|
| 用户名 | `system` |
| 密码 | `system` |

> ⚠️ 上线前请务必修改默认密码，或将 `fake_users_db` 替换为真实数据库查询。

---

## 主要路由

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | 首页跳转 | 否 |
| GET | `/login` | 登录页 | 否 |
| POST | `/api/login` | 登录（Cookie） | 限流 |
| POST | `/api/logout` | 注销 | 是 |
| GET | `/api/verify` | 验证登录态 | 是 |
| GET | `/api/protected-data` | 受保护数据示例 | 是 |
| POST | `/token` | OAuth2 获取 Bearer Token | 否 |
| GET | `/users/me/` | 当前用户信息 | Bearer |
| GET | `/docs` | 受保护的 Swagger UI | Cookie |
| GET | `/files/browse/...` | 文件目录浏览 | Cookie |
| GET | `/files/preview/...` | 文件预览/下载 | Cookie |
| GET | `/apilog/logs` | 日志查看页面 | Cookie |
| GET | `/apilog/get_logs` | 日志查询接口 | Cookie |
| GET | `/health` | 健康检查 | 否 |

---

## 目录结构

```
FastAPI-DENNISCHEN/
├── main.py                 # FastAPI 入口
├── requirements.txt        # 精简后的直接依赖
├── .env.example            # 环境变量模板
├── .env                    # 本地配置（不提交到 git）
├── .gitignore
├── security/
│   ├── setting.py          # pydantic-settings 配置 + 数据模型
│   ├── jwt_utils.py        # JWT/密码工具（共用）
│   ├── deps.py             # 通用依赖（登录限流等）
│   ├── stdjwt.py           # Bearer Token 路由
│   └── cookie.py           # Cookie 路由 + 页面
├── apilog/
│   ├── log_config.py       # 日志器、脱敏字段、记录路径配置
│   ├── log_middleware.py   # 请求日志 + openapi 保护中间件
│   └── readlogs.py         # 日志查询接口（倒序分页读取）
├── apps/
│   └── FilesManage.py      # 文件浏览/预览（带路径越界防护）
├── static/                 # 静态资源
├── templates/              # Jinja2 模板
└── logs/                   # 运行日志
```

---

## 优化清单（相对原仓库）

### 🔴 安全修复
1. **密钥硬编码** → 使用 `pydantic-settings` + `.env` 从环境变量加载
2. **路径遍历漏洞** → 所有用户传入路径经 `os.path.realpath` 校验，越界直接 403
3. **登录无速率限制** → 新增 IP 滑动窗口限流（5 次/分钟），超限返回 429
4. **Cookie secure 硬编码** → 根据 `ENV` 环境变量自动切换
5. **openapi.json 路径绕过** → 路径使用 `rstrip('/')` 规范化后再匹配白名单
6. **文件接口未鉴权** → 所有 `/files/*` 接口统一加入登录依赖

### 🟡 架构与性能
7. **JWT/密码逻辑重复** → 抽至 `security/jwt_utils.py` 共用
8. **中间件每请求实例化** → 改用 `app.add_middleware(LogMiddleware)` 全局单例
9. **日志全量读入内存** → 倒序块读取 + 分页（默认最近 5000 行），避免大文件 OOM
10. **冗余依赖** → 移除 `passlib`/`bcrypt`/`fuzzywuzzy`/`python-Levenshtein`/`rapidfuzz` 等无用包
11. **requirements 编码问题** → 由 UTF-16 改为标准 UTF-8，只保留直接依赖

### 🟢 代码质量
12. **`import *` 污染** → 所有 `__init__.py` 改为显式导出 `__all__`
13. **类/函数命名** → `Sensitive_Keys`→`SensitiveKeys`，函数名覆盖（两个 `browse_files`）已修复
14. **默认参数陷阱** → `Response()` 默认值移除
15. **脱敏逻辑不一致** → 统一使用递归版 `mask_sensitive_data`，支持嵌套对象
16. **日志解析脆弱** → 使用正则 + `json.loads` 替代固定下标切片 + `ast.literal_eval`
17. **`print` 调试残留** → 统一使用 logger
18. **`os.path.join` 嵌套** → 改为多参数调用
19. **未使用 import** → `import datetime` 等已清理

### ⚙️ 工程化
20. 新增 `/health` 健康检查端点
21. 新增全局异常处理器（ValidationError / 500）
22. 新增 `.gitignore`，自动排除 `.env`、`__pycache__`、IDE 配置
23. `reload` 根据环境变量自动开关
24. 日志目录自动创建，handler 注册幂等（避免 uvicorn reload 重复打日志）
25. **Python 3.8 兼容**：全部移除 `X | Y` 联合类型、`list[X]` 泛型下标等 3.9+ 语法，`Annotated` 通过 `typing_extensions` 兼容
