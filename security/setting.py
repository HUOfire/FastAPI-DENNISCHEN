"""应用配置 + Pydantic 模型定义。"""
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项，所有字段均可通过环境变量或 .env 覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- 运行环境 ----
    env: str = Field(default="development", description="运行环境: development / production")

    # ---- JWT ----
    secret_key: str = Field(..., description="JWT 签名密钥，必须从环境变量提供")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # ---- OpenAPI 保护 ----
    openapi_allowed_ips: str = Field(default="127.0.0.1,::1")

    # ---- 文件管理 ----
    upload_dir: str = Field(default="./uploads")

    # ---- 日志 ----
    log_file: str = Field(default="./logs/app.log")
    log_max_bytes: int = Field(default=5 * 1024 * 1024)
    log_backup_count: int = Field(default=5)

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        return self.is_production

    @property
    def openapi_allowed_ip_list(self) -> List[str]:
        return [ip.strip() for ip in self.openapi_allowed_ips.split(",") if ip.strip()]

    @property
    def fake_users_db(self) -> dict:
        return {
            "system": {
                "username": "system",
                "full_name": "DENNIS CHEN",
                "email": "dennischen@example.com",
                # 默认密码：system
                "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$/Aoq+Lu+3gGg/bebIx+sjw$kR2GceT6th43hgQV/Uea25LeFfrrrbe1GqtdyfEWAok",
                "role": "admin",
                "disabled": False,
            }
        }


settings = Settings()


# ===================== Pydantic 数据模型 =====================
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    role: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class LoginRequest(BaseModel):
    username: str
    password: str
