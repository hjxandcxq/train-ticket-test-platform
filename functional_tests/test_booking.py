# -*- coding: utf-8 -*-
"""下单：成功 + 失败（未登录、座位不存在、余票不足、乘客姓名为空）。"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from browser import (api_session, fail_with_screenshot, login, wait_error,
                     wait_success, wait_url_contains)

WAIT = 8


def _login_and_search(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    driver.get(f"{base_url}/trains")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "fromStation")))
    Select(driver.find_element(By.ID, "fromStation")).select_by_visible_text("北京南")
    Select(driver.find_element(By.ID, "toStation")).select_by_visible_text("上海虹桥")
    driver.find_element(By.ID, "btn-search").click()
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "trainTable")))


def _stock(db, seat_id):
    with db.cursor() as cur:
        cur.execute("SELECT stock FROM train_seats WHERE id=%s", (seat_id,))
        return cur.fetchone()["stock"]


def test_booking_success(driver, base_url, db):
    before = _stock(db, 9101)
    _login_and_search(driver, base_url)

    row = driver.find_element(
        By.XPATH,
        "//table[@id='trainTable']//tr[td[contains(., 'FUNC01')] and td[contains(., '二等座')]]")
    passenger = f"功能乘客{int(time.time())}"
    row.find_element(By.NAME, "passengerName").send_keys(passenger)
    row.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

    wait_url_contains(driver, "/orders")
    msg = wait_success(driver)
    if "购票成功" not in msg:
        fail_with_screenshot(driver, "booking_success", f"预期购票成功，实际「{msg}」")
    assert passenger in driver.page_source
    assert "已支付" in driver.page_source
    assert _stock(db, 9101) == before - 1


def test_booking_without_login(driver, base_url):
    driver.get(f"{base_url}/orders")
    wait_url_contains(driver, "/login")
    assert "火车票预订系统" in driver.page_source


def test_booking_nonexistent_seat_api(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    api = api_session(driver)
    resp = api.post(f"{base_url}/orders",
                    data={"seatId": "999999", "passengerName": "不存在座位"},
                    timeout=5)
    if "车次席别不存在" not in resp.text:
        fail_with_screenshot(driver, "booking_no_seat",
                             "接口下单不存在的座位，未返回「车次席别不存在」")


def test_booking_sold_out_api(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    api = api_session(driver)
    resp = api.post(f"{base_url}/orders",
                    data={"seatId": "9102", "passengerName": "无票乘客"},
                    timeout=5)
    if "该车次余票不足" not in resp.text:
        fail_with_screenshot(driver, "booking_sold_out",
                             "无票座位下单，未返回「该车次余票不足」")


def test_booking_empty_passenger_api(driver, base_url):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    api = api_session(driver)
    resp = api.post(f"{base_url}/orders",
                    data={"seatId": "9101", "passengerName": ""},
                    timeout=5)
    if "乘客姓名必填" not in resp.text:
        fail_with_screenshot(driver, "booking_empty_passenger",
                             "空乘客姓名下单，未返回「乘客姓名必填」")
