# 作为前端调取日志信息的接口
import os
import time

from fastapi import APIRouter

logs_router = APIRouter()

def chg_date(time_str):
    value5 = time.strptime(time_str, '%Y-%m-%d %H:%M:%S,%f')
    value6 = time.strftime("%Y-%m-%d", value5)
    return value6


def read_logs(date = None, level = None, keyword = None):
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
                if date:
                    lin_time = text[0]+","+text[1]
                    if chg_date(lin_time)!=date:
                        continue
                if level:
                    if text[3]!=level:
                        continue
                if keyword:
                    if keyword not in text:
                        continue
                list_log = dict(zip(list_key, text))
                result.append(list_log)
    if result:
        return result
    else:
        return  None


@logs_router.get("/logs")
async def get_logs(date: str = None, level: str = None, keyword: str = None):
    logs = read_logs(date, level, keyword)
    if logs:
        return {"code": 200, "msg": "success", "data": logs}
    else:
        return {"code": 404, "msg": "not found", "data": []}


@logs_router.get("/logs/{date}")
async def logs_page(request: Request):
    # print(request.method)
    return templates.TemplateResponse(
        "pageto.html",
        context={
            'request': request,
            'login_tip': '前往登录'
        }
    )