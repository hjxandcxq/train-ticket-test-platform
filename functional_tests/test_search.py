# -*- coding: utf-8 -*-
"""车次查询：成功 + 失败（同站、缺站、无结果、过去日期）。"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from browser import fail_with_screenshot, login, wait_error, wait_url_contains

WAIT = 8


def _login(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")


def _search(driver, base_url, from_station="", to_station="", date_value=None):
    driver.get(f"{base_url}/trains")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "fromStation")))
    Select(driver.find_element(By.ID, "fromStation")).select_by_visible_text(
        from_station or "请选择")
    Select(driver.find_element(By.ID, "toStation")).select_by_visible_text(
        to_station or "请选择")
    if date_value:
        date_el = driver.find_element(By.ID, "travelDate")
        driver.execute_script(
            "arguments[0].removeAttribute('min'); arguments[0].value = arguments[1];",
            date_el, date_value)
    driver.find_element(By.ID, "btn-search").click()


def test_search_success(driver, base_url):
    _login(driver, base_url)
    _search(driver, base_url, "北京南", "上海虹桥")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "trainTable")))
    page = driver.page_source
    assert "G101" in page
    assert "FUNC01" in page
    assert "二等座" in page


def test_search_same_station(driver, base_url):
    _login(driver, base_url)
    _search(driver, base_url, "北京南", "北京南")
    msg = wait_error(driver)
    if msg != "出发站和到达站不能相同":
        fail_with_screenshot(driver, "search_same_station",
                             f"预期「出发站和到达站不能相同」，实际「{msg}」")


def test_search_missing_station(driver, base_url):
    _login(driver, base_url)
    _search(driver, base_url, "", "上海虹桥")
    msg = wait_error(driver)
    if msg != "出发站和到达站不能为空":
        fail_with_screenshot(driver, "search_missing_station",
                             f"预期「出发站和到达站不能为空」，实际「{msg}」")


def test_search_no_result(driver, base_url):
    _login(driver, base_url)
    _search(driver, base_url, "广州南", "北京南")
    assert "没有查询到符合条件的车次" in driver.page_source


def test_search_past_date(driver, base_url):
    _login(driver, base_url)
    _search(driver, base_url, "北京南", "上海虹桥", date_value="2020-01-01")
    msg = wait_error(driver)
    if msg != "出行日期不能早于今天":
        fail_with_screenshot(driver, "search_past_date",
                             f"预期「出行日期不能早于今天」，实际「{msg}」")
