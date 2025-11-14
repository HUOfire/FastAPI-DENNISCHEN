from pydantic import BaseModel
from typing import Union


class Config:

    SECRET_KEY = "7302d92f95a5507697954582a8abb3a963052731cab0f9142078b1adfda56787"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 5


    fake_users_db = {
                "system": {
                        "username": "system",
                        "full_name": "DENNIS CHEN",
                        "email": "dennischen@example.com",
                        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$/Aoq+Lu+3gGg/bebIx+sjw$kR2GceT6th43hgQV/Uea25LeFfrrrbe1GqtdyfEWAok",
                        "role": "admin",
                        "disabled": False,
                }
            }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    role: Union[str, None] = None
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserRole(BaseModel):
    username: str
    role: str