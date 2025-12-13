# 作为前端调取日志信息的接口
import os
import time

from fastapi import APIRouter, Request, Depends
from security.cookie import templates, get_current_user

from fuzzywuzzy import fuzz, process

logs_router = APIRouter()

def chg_date(time_str):
    value5 = time.strptime(time_str, '%Y-%m-%d %H:%M:%S,%f')
    value6 = time.strftime("%Y-%m-%d", value5)
    return value6

# 模糊匹配字符串  返回匹配度  100完全匹配
def partial_match(str1, str2):
    return fuzz.partial_ratio(str1, str2)

def read_logs(str_date = None, end_date = None, level = None, keyword = None):
    log_file = "./apilog/app.log"
    list_key = ["datetime", "timeframe", "server", "level", "message"]
    result = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            data = f.read().split("\n")
            for line in data:
                text = str(line).split(",")
                if len(text)<3:
                    continue
                lin_time = text[0] + "," + text[1]
                if str_date:
                    if chg_date(lin_time) < str_date:
                        continue
                if end_date:
                    if chg_date(lin_time) > end_date:
                        continue
                if level:
                    if text[3]!=level:
                        continue
                if keyword:
                    t_value = partial_match(text[4], keyword)
                    if t_value < 50:
                        continue
                list_log = dict(zip(list_key, text))
                result.append(list_log)
    if result:
        return result
    else:
        return  None


@logs_router.get("/get_logs")
async def get_logs(str_date : str = None, end_date : str = None, level: str = None, keyword: str = None,
                   user: dict = Depends(get_current_user)
                ):
    logs = read_logs(str_date, end_date, level, keyword)
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
            'login_tip': '日志查询'
        }
    )