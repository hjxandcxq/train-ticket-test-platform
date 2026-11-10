# -*- coding: utf-8 -*-
"""登录：成功 + 失败（密码错、账号不存在、空字段）。"""
from selenium.webdriver.common.by import By

from browser import fail_with_screenshot, login, wait_error, wait_url_contains


def test_login_success(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    assert driver.find_element(By.CSS_SELECTOR, ".nav .user").text.strip() == "alice01"
    assert "车次查询" in driver.page_source


def test_login_wrong_password(driver, base_url):
    login(driver, base_url, "alice01", "Pass124")
    msg = wait_error(driver)
    if msg != "用户名或密码错误":
        fail_with_screenshot(driver, "login_wrong_password",
                             f"预期「用户名或密码错误」，实际「{msg}」")
    assert "/login" in driver.current_url


def test_login_unknown_user(driver, base_url):
    login(driver, base_url, "no_such_user", "Pass123")
    msg = wait_error(driver)
    if msg != "用户名或密码错误":
        fail_with_screenshot(driver, "login_unknown_user",
                             f"预期「用户名或密码错误」，实际「{msg}」")


def test_login_empty_fields(driver, base_url):
    login(driver, base_url, "", "")
    msg = wait_error(driver)
    if msg != "用户名和密码不能为空":
        fail_with_screenshot(driver, "login_empty",
                             f"预期「用户名和密码不能为空」，实际「{msg}」")
