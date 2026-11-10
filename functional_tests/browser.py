# -*- coding: utf-8 -*-
"""Selenium 浏览器封装：驱动、登录、消息等待、截图、会话 Cookie。"""
import os
import sys
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parent
SCREENSHOT_DIR = ROOT / "screenshots"
BASE_URL = os.environ.get("TT_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
WAIT = int(os.environ.get("TT_WAIT", "8"))

_WIN_CANDIDATES = [
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

_LINUX_CANDIDATES = [
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/microsoft-edge",
]


def find_browser():
    env_bin = os.environ.get("TT_BROWSER_BINARY", "").strip()
    if env_bin:
        if not os.path.exists(env_bin):
            raise RuntimeError(f"TT_BROWSER_BINARY 指向的文件不存在: {env_bin}")
        kind = "edge" if "msedge" in os.path.basename(env_bin).lower() else "chrome"
        return kind, env_bin

    candidates = _WIN_CANDIDATES if sys.platform.startswith("win") else _LINUX_CANDIDATES
    for path in candidates:
        if path and os.path.exists(path):
            kind = "edge" if "msedge" in os.path.basename(path).lower() else "chrome"
            return kind, path
    return None, None


def create_driver(headless=None):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService

    kind, binary = find_browser()
    if kind is None:
        raise RuntimeError("未找到 Chrome / Edge，请安装或设置 TT_BROWSER_BINARY")

    if headless is None:
        headless = os.environ.get("TT_HEADLESS", "1") != "0"

    options, service_cls = (
        (EdgeOptions(), EdgeService) if kind == "edge" else (ChromeOptions(), ChromeService)
    )
    if headless:
        options.add_argument("--headless=new")
    for arg in ("--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
                "--disable-software-rasterizer", "--disable-extensions",
                "--window-size=1600,900", "--log-level=3"):
        options.add_argument(arg)
    options.binary_location = binary

    driver_path = os.environ.get("TT_DRIVER_PATH", "").strip()
    service = service_cls(driver_path) if driver_path else service_cls()
    driver = webdriver.Chrome(service=service, options=options) if kind == "chrome" \
        else webdriver.Edge(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver


def save_screenshot(driver, name):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        driver.save_screenshot(str(path))
    except Exception:
        return None
    return str(path)


def fail_with_screenshot(driver, name, message):
    shot = save_screenshot(driver, name)
    raise AssertionError(f"{message}（失败截图：{shot}）" if shot else message)


def login(driver, base_url, username, password):
    """打开登录页并提交，不判断结果。"""
    driver.get(f"{base_url}/login")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.NAME, "uname")))
    user = driver.find_element(By.NAME, "uname")
    pwd = driver.find_element(By.NAME, "pword")
    user.clear()
    user.send_keys(username)
    pwd.clear()
    pwd.send_keys(password)
    driver.find_element(By.ID, "btn-login").click()


def logout(driver, base_url):
    driver.get(f"{base_url}/logout")


def wait_error(driver, timeout=None):
    el = WebDriverWait(driver, timeout or WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".msg.error")))
    return el.text.strip()


def wait_success(driver, timeout=None):
    el = WebDriverWait(driver, timeout or WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".msg.success")))
    return el.text.strip()


def wait_url_contains(driver, fragment, timeout=None):
    WebDriverWait(driver, timeout or WAIT).until(lambda d: fragment in d.current_url)


def api_session(driver):
    """把浏览器当前会话 Cookie 复制到 requests.Session，便于做接口级失败用例。"""
    import requests

    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])
    return session
