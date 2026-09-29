import multiprocessing
import os
import signal
import sys
import threading
import time
from typing import Optional

import pystray
import uvicorn
from PIL import Image, ImageDraw

# ==================== 配置项 ====================
CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "auto_start": True,  # 程序启动时自动开启服务
    "graceful_timeout": 5  # 优雅关闭等待超时时间（秒）
}

# ==================== Uvicorn 进程控制逻辑 ====================
# 使用 Optional 兼容 Python 3.8
server_process: Optional[multiprocessing.Process] = None


def run_uvicorn():
    """子进程入口：运行Uvicorn服务"""
    config = uvicorn.Config(
         "main:app",
        host=CONFIG["host"],
        port=CONFIG["port"],
        log_level="info",
        reload=False  # 必须关闭reload，避免多进程冲突
    )
    server = uvicorn.Server(config)
    server.run()


def is_server_running() -> bool:
    """检查Uvicorn服务是否正在运行"""
    global server_process
    return server_process is not None and server_process.is_alive()


def start_server():
    """启动Uvicorn服务"""
    global server_process
    if is_server_running():
        return

    server_process = multiprocessing.Process(
        target=run_uvicorn,
        daemon=False,  # 非守护进程，以便手动控制关闭
        name="UvicornWorker"
    )
    server_process.start()
    time.sleep(0.5)  # 等待进程初始化
    print(f"[管理器] Uvicorn已启动，PID: {server_process.pid}")


def stop_server():
    """停止Uvicorn服务"""
    global server_process
    if not is_server_running():
        server_process = None
        return

    print("[管理器] 正在停止Uvicorn服务...")
    # 跨平台发送终止信号
    if sys.platform == "win32":
        server_process.terminate()
    else:
        os.kill(server_process.pid, signal.SIGTERM)

    # 等待优雅关闭
    server_process.join(timeout=CONFIG["graceful_timeout"])

    # 超时强制杀死
    if server_process.is_alive():
        print("[管理器] 优雅关闭超时，强制终止")
        server_process.kill()
        server_process.join()

    server_process = None
    print("[管理器] Uvicorn服务已停止")


def restart_server():
    """重启Uvicorn服务"""
    stop_server()
    time.sleep(0.5)  # 等待端口释放
    start_server()


# ==================== 托盘菜单回调 ====================
def on_start(icon, item):
    start_server()
    update_tray_state(icon)


def on_stop(icon, item):
    stop_server()
    update_tray_state(icon)


def on_restart(icon, item):
    restart_server()
    update_tray_state(icon)


def on_quit(icon, item):
    stop_server()
    icon.stop()


# ==================== 托盘状态更新 ====================
# 构建托盘字母图标
def create_line_icon(text="F", size=64, line_color=(255, 255, 255)):
    """
    创建基于文字或简单线条的图标
    """
    # 背景设为透明或深色
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 绘制一个圆形背景板 (半透明黑色，确保在浅色任务栏也能看清)
    draw.ellipse([0, 0, size, size], fill=(0, 0, 0, 180))

    # 绘制文字
    # 注意：PIL 默认字体较小，生产环境建议加载自定义 .ttf 字体
    try:
        from PIL import ImageFont
        # 尝试加载系统字体，如果失败则使用默认
        font = ImageFont.truetype("arial.ttf", size=int(size * 0.6))
    except:
        font = ImageFont.load_default()

    # 计算文字位置使其居中
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size - text_width) / 2
    y = (size - text_height) / 2 - bbox[1]  # 修正 baseline

    draw.text((x, y), text, font=font, fill=line_color)

    return image

ICON_RUNNING = create_line_icon(line_color = (0, 180, 0))  # 绿色
ICON_STOPPED = create_line_icon(line_color = (180, 0, 0))  # 红色


def create_menu():
    """动态生成菜单"""
    running = is_server_running()
    status_text = "✅ 服务状态：运行中" if running else "❌ 服务状态：已停止"
    return pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("启动服务", on_start, enabled=not running),
        pystray.MenuItem("停止服务", on_stop, enabled=running),
        pystray.MenuItem("重启服务", on_restart, enabled=running),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f"地址: http://{CONFIG['host']}:{CONFIG['port']}", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出程序", on_quit)
    )


def update_tray_state(icon):
    """更新托盘图标和菜单"""
    running = is_server_running()
    icon.icon = ICON_RUNNING if running else ICON_STOPPED
    icon.menu = create_menu()
    icon.update_menu()


def health_check():
    """定期检查服务状态并更新托盘"""
    update_tray_state(tray)
    # 使用 threading.Timer 替代 tray.after
    # 参数: 间隔秒数, 要执行的函数
    timer = threading.Timer(2.0, health_check)
    timer.daemon = True  # 设置为守护线程，主程序退出时自动结束
    timer.start()


def tray_main():
    multiprocessing.freeze_support()
    global server_process
    server_process = None
    if CONFIG["auto_start"]:
        start_server()

    initial_icon = ICON_RUNNING if is_server_running() else ICON_STOPPED
    global tray
    tray = pystray.Icon(
        "uvicorn_tray",
        initial_icon,
        "Uvicorn服务管理器",
        menu=create_menu()
    )

    # 【修改点】启动健康检查定时器，而不是调用 tray.after
    health_check_timer = threading.Timer(1.0, health_check)
    health_check_timer.daemon = True
    health_check_timer.start()

    try:
        tray.run()
    finally:
        stop_server()