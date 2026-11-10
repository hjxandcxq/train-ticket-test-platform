# -*- coding: utf-8 -*-
"""管理后台：成功 + 失败（普通用户越权、重复线路）。"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from browser import fail_with_screenshot, login, wait_error, wait_success, wait_url_contains

WAIT = 8


def test_admin_forbidden_for_normal_user(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    driver.get(f"{base_url}/admin")
    wait_url_contains(driver, "forbidden=1")
    msg = wait_error(driver)
    if msg != "没有管理员权限":
        fail_with_screenshot(driver, "admin_forbidden",
                             f"预期「没有管理员权限」，实际「{msg}」")


def test_admin_dashboard_success(driver, base_url):
    login(driver, base_url, "admin", "admin123")
    wait_url_contains(driver, "/trains")
    driver.get(f"{base_url}/admin")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "adminTrainTable")))
    assert "新增车次" in driver.page_source
    assert "最近订单" in driver.page_source


def test_admin_add_train_success(driver, base_url):
    login(driver, base_url, "admin", "admin123")
    wait_url_contains(driver, "/trains")
    driver.get(f"{base_url}/admin")

    no = f"F{int(time.time() * 1000) % 10_000_000}"
    driver.find_element(By.ID, "trainNo").send_keys(no)
    driver.find_element(By.ID, "fromStation").send_keys("天津南")
    driver.find_element(By.ID, "toStation").send_keys("济南西")
    driver.execute_script("arguments[0].value='08:00';",
                          driver.find_element(By.ID, "departTime"))
    driver.execute_script("arguments[0].value='10:00';",
                          driver.find_element(By.ID, "arriveTime"))
    driver.find_element(By.ID, "basePrice").send_keys("99.00")
    driver.find_element(By.ID, "btn-add-train").click()

    msg = wait_success(driver)
    if "车次添加成功" not in msg:
        fail_with_screenshot(driver, "admin_add_train", f"预期添加成功，实际「{msg}」")
    assert no in driver.page_source


def test_admin_add_duplicate_route(driver, base_url):
    login(driver, base_url, "admin", "admin123")
    wait_url_contains(driver, "/trains")
    driver.get(f"{base_url}/admin")

    driver.find_element(By.ID, "trainNo").send_keys("G101")
    driver.find_element(By.ID, "fromStation").send_keys("北京南")
    driver.find_element(By.ID, "toStation").send_keys("上海虹桥")
    driver.execute_script("arguments[0].value='08:00';",
                          driver.find_element(By.ID, "departTime"))
    driver.execute_script("arguments[0].value='12:30';",
                          driver.find_element(By.ID, "arriveTime"))
    driver.find_element(By.ID, "basePrice").send_keys("553.00")
    driver.find_element(By.ID, "btn-add-train").click()

    msg = wait_error(driver)
    if msg != "该车次线路已存在":
        fail_with_screenshot(driver, "admin_duplicate_train",
                             f"预期「该车次线路已存在」，实际「{msg}」")
