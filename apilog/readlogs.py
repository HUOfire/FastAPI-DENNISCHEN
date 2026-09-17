# 作为前端调取日志信息的接口
import os
import time
import ast
from datetime import date

from fastapi import APIRouter, Request, Depends
from security.cookie import templates, get_current_user

from fuzzywuzzy import fuzz, process

logs_router = APIRouter()

def chg_date(time_str):
    value5 = time.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    value6 = time.strftime("%Y-%m-%d", value5)
    return value6

# 模糊匹配字符串  返回匹配度  100完全匹配
def partial_match(str1, str2):
    return fuzz.partial_ratio(str1, str2)

def read_logs(str_date = None, end_date = None, level = None):
    log_file = f"./logs/app.log"

    result = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            data = f.read().split("\n")
            for line in data:
                start_index = line.find('{')
                if start_index != -1:
                    lin_time = line[:19]
                    lin_level = line[22:start_index - 3]
                    json_str = line[start_index:]
                    if str_date:
                        if chg_date(lin_time) < str_date:
                            continue
                    if end_date:
                        if chg_date(lin_time) > end_date:
                            continue
                    if level != "全部":
                        if lin_level != level:
                            continue
                    try:
                        new_json = ast.literal_eval(json_str)
                        new_json['ltime'] = lin_time
                        new_json['level'] = lin_level
                        result.append(new_json)
                    except (ValueError, SyntaxError) as e:
                        print(f"解析错误: {e}")
                    continue
    if result:
        return result
    else:
        return  None


@logs_router.get("/get_logs")
async def get_logs(str_date : str = None, end_date : str = None, level: str = None,
                   user: dict = Depends(get_current_user)
                ):
    logs = read_logs(str_date, end_date, level)
    if logs:
        return {"code": 200, "msg": "success", "logs": logs}
    else:
        return {"code": 404, "msg": "not found", "logs": []}


@logs_router.get("/logs")
async def logs_page(request: Request,  user: dict = Depends(get_current_user)):
    return templates.TemplateResponse(
        "logs.html",
        context={
            'request': request,
            "user": user
        }
    )


if __name__ == "__main__":
    read_logs()