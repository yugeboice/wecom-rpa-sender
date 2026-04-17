"""
企业微信桌面客户端 RPA 执行器

通过 pyautogui 操控 macOS 企业微信桌面客户端完成消息发送。
预留 OCR / 图像匹配扩展接口。
"""

import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol

import pyautogui

from app.config.settings import settings

logger = logging.getLogger(__name__)

# 安全设置
pyautogui.FAILSAFE = True
pyautogui.PAUSE = settings.rpa_step_delay


# === 扩展接口 ===

class ImageMatcher(Protocol):
    """图像匹配扩展接口（预留）"""
    def locate(self, image_path: str) -> Optional[tuple[int, int]]: ...


class OCRReader(Protocol):
    """OCR 扩展接口（预留）"""
    def read_screen(self, region: Optional[tuple] = None) -> str: ...


# === 用户映射 ===

def load_user_mapping() -> dict[str, str]:
    path = Path(settings.user_mapping_file)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("_comment", None)
        return data
    return {}


def resolve_search_keyword(
    target_user_id: str, target_display_name: Optional[str] = None
) -> str:
    mapping = load_user_mapping()
    if target_user_id in mapping:
        return mapping[target_user_id]
    if target_display_name:
        return target_display_name
    return target_user_id


# === 截图 ===

def take_screenshot(task_id: str, step: str) -> Optional[str]:
    try:
        ss_dir = Path(settings.screenshot_dir)
        ss_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{task_id}_{step}_{ts}.png"
        filepath = ss_dir / filename
        pyautogui.screenshot(str(filepath))
        logger.info("Screenshot saved: %s", filepath)
        return str(filepath)
    except Exception as e:
        logger.warning("Screenshot failed: %s", e)
        return None


# === 核心 RPA 步骤 ===

def activate_wecom():
    """激活企业微信窗口（macOS）"""
    script = f'''
    tell application "System Events"
        set frontApp to name of first process whose frontmost is true
    end tell
    tell application "{settings.wecom_window_title}"
        activate
    end tell
    delay 0.5
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=5)
        time.sleep(settings.rpa_step_delay)
        logger.info("企业微信窗口已激活")
    except Exception as e:
        raise RuntimeError(f"无法激活企业微信窗口: {e}") from e


def open_search():
    """打开搜索框 (Cmd+F)"""
    pyautogui.hotkey("command", "f")
    time.sleep(settings.rpa_search_wait)


def search_user(keyword: str):
    """在搜索框输入关键字并等待结果"""
    # 清空已有内容
    pyautogui.hotkey("command", "a")
    time.sleep(0.1)
    pyautogui.press("delete")
    time.sleep(0.1)
    # 输入搜索关键字（使用剪贴板方式输入中文）
    _type_chinese(keyword)
    time.sleep(settings.rpa_search_wait)


def select_first_result():
    """选择搜索结果的第一项"""
    pyautogui.press("enter")
    time.sleep(settings.rpa_step_delay)


def type_message(text: str):
    """在聊天输入框输入消息"""
    _type_chinese(text)
    time.sleep(settings.rpa_send_wait)


def send_message():
    """发送消息 (Enter)"""
    pyautogui.press("enter")
    time.sleep(settings.rpa_step_delay)


def _type_chinese(text: str):
    """通过剪贴板粘贴方式输入中文"""
    try:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True, timeout=2)
        pyautogui.hotkey("command", "v")
        time.sleep(0.2)
    except Exception:
        # fallback: 逐字符输入（可能丢失中文）
        pyautogui.typewrite(text, interval=0.05)


# === 主执行函数 ===

class RPAResult:
    def __init__(self, success: bool, message: str = "", screenshot: Optional[str] = None):
        self.success = success
        self.message = message
        self.screenshot = screenshot


def execute_send(
    task_id: str,
    target_user_id: str,
    message_text: str,
    target_display_name: Optional[str] = None,
) -> RPAResult:
    """
    执行完整的 RPA 发送流程：
    激活窗口 → 搜索用户 → 选择用户 → 输入消息 → 发送
    """
    keyword = resolve_search_keyword(target_user_id, target_display_name)
    logger.info("Task %s: 开始发送, 搜索关键字=%s", task_id, keyword)

    try:
        # 1. 激活企业微信
        activate_wecom()
        take_screenshot(task_id, "01_activated")

        # 2. 打开搜索
        open_search()
        take_screenshot(task_id, "02_search_opened")

        # 3. 搜索用户
        search_user(keyword)
        take_screenshot(task_id, "03_searched")

        # 4. 选中第一个结果
        select_first_result()
        take_screenshot(task_id, "04_user_selected")

        # 5. 输入消息
        type_message(message_text)
        take_screenshot(task_id, "05_message_typed")

        # 6. 发送
        send_message()
        ss = take_screenshot(task_id, "06_sent")

        logger.info("Task %s: 发送成功", task_id)
        return RPAResult(success=True, message="发送成功", screenshot=ss)

    except Exception as e:
        logger.error("Task %s: 发送失败 - %s", task_id, e)
        ss = take_screenshot(task_id, "error")
        return RPAResult(success=False, message=str(e), screenshot=ss)
