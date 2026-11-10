# -*- coding: utf-8 -*-
"""注册：成功 + 失败（重名、两次密码不一致、弱密码、用户名过短）。"""
import time

from browser import fail_with_screenshot, login, wait_error, wait_success, wait_url_contains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

WAIT = 8


def _unique(prefix="func_"):
    return f"{prefix}{int(time.time() * 1000) % 10_000_000_000}"


def _register(driver, base_url, username, password, confirm):
    driver.get(f"{base_url}/register")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "username")))
    for field, value in (("username", username),
                         ("password", password),
                         ("confirm", confirm)):
        el = driver.find_element(By.NAME, field)
        el.clear()
        el.send_keys(value)
    driver.find_element(By.ID, "btn-register").click()


def test_register_success_then_login(driver, base_url):
    username = _unique()
    _register(driver, base_url, username, "Pass123", "Pass123")
    wait_url_contains(driver, "/login?registered=1")
    msg = wait_success(driver)
    if "注册成功" not in msg:
        fail_with_screenshot(driver, "register_success",
                             f"预期注册成功提示，实际「{msg}」")

    login(driver, base_url, username, "Pass123")
    wait_url_contains(driver, "/trains")
    assert "车次查询" in driver.page_source


def test_register_duplicate_username(driver, base_url):
    _register(driver, base_url, "alice01", "Pass123", "Pass123")
    msg = wait_error(driver)
    if msg != "用户名已存在":
        fail_with_screenshot(driver, "register_duplicate",
                             f"预期「用户名已存在」，实际「{msg}」")


def test_register_password_mismatch(driver, base_url):
    _register(driver, base_url, _unique(), "Pass123", "Pass124")
    msg = wait_error(driver)
    if msg != "两次密码不一致":
        fail_with_screenshot(driver, "register_mismatch",
                             f"预期「两次密码不一致」，实际「{msg}」")


def test_register_weak_password(driver, base_url):
    _register(driver, base_url, _unique(), "abcdef", "abcdef")
    msg = wait_error(driver)
    if msg != "密码必须同时包含字母和数字":
        fail_with_screenshot(driver, "register_weak_pwd",
                             f"预期「密码必须同时包含字母和数字」，实际「{msg}」")


def test_register_short_username(driver, base_url):
    _register(driver, base_url, "abc", "Pass123", "Pass123")
    msg = wait_error(driver)
    if msg != "用户名长度4-20位":
        fail_with_screenshot(driver, "register_short_name",
                             f"预期「用户名长度4-20位」，实际「{msg}」")
