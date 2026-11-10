# -*- coding: utf-8 -*-
"""退票：成功 + 失败（重复退票、退别人的订单）。"""
import re
import time

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from browser import (api_session, fail_with_screenshot, login, wait_success,
                     wait_url_contains)

WAIT = 8


def _stock(db, seat_id):
    with db.cursor() as cur:
        cur.execute("SELECT stock FROM train_seats WHERE id=%s", (seat_id,))
        return cur.fetchone()["stock"]


def _book(api, base_url, seat_id, passenger):
    resp = api.post(f"{base_url}/orders",
                    data={"seatId": str(seat_id), "passengerName": passenger},
                    timeout=5)
    if "购票成功" not in resp.text:
        raise AssertionError(f"前置下单失败：{resp.text[:200]}")
    return resp


def _order_id_by_passenger(db, passenger):
    with db.cursor() as cur:
        cur.execute("SELECT id FROM ticket_orders WHERE passenger_name=%s "
                    "ORDER BY id DESC LIMIT 1", (passenger,))
        row = cur.fetchone()
        return row["id"] if row else None


def test_refund_success_and_no_repeat(driver, base_url, db):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    api = api_session(driver)

    before = _stock(db, 9103)
    passenger = f"退票乘客{int(time.time())}"
    _book(api, base_url, 9103, passenger)
    order_id = _order_id_by_passenger(db, passenger)
    assert order_id is not None

    driver.get(f"{base_url}/orders")
    WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "orderTable")))
    row = driver.find_element(
        By.XPATH, f"//table[@id='orderTable']//tr[td[contains(., '{passenger}')]]")
    row.find_element(By.CSS_SELECTOR, "button").click()

    msg = wait_success(driver)
    if "退票成功" not in msg:
        fail_with_screenshot(driver, "refund_success", f"预期退票成功，实际「{msg}」")
    assert "已退票" in driver.page_source
    assert _stock(db, 9103) == before

    # 重复退票：接口层再退一次，应被拒绝且不再回补库存
    resp = api.post(f"{base_url}/orders/{order_id}/refund", timeout=5)
    if "订单已退票或状态不允许" not in resp.text:
        fail_with_screenshot(driver, "refund_repeat",
                             "重复退票未返回「订单已退票或状态不允许」")
    assert _stock(db, 9103) == before


def test_refund_other_users_order(driver, base_url, db):
    login(driver, base_url, "alice01", "Pass123")
    wait_url_contains(driver, "/trains")
    alice_api = api_session(driver)

    passenger = f"越权退票{int(time.time())}"
    _book(alice_api, base_url, 9103, passenger)
    order_id = _order_id_by_passenger(db, passenger)

    # bob01 自己登录，尝试退 alice01 的订单
    bob = requests.Session()
    bob.post(f"{base_url}/login",
             data={"uname": "bob01", "pword": "Pass123"}, timeout=5)
    resp = bob.post(f"{base_url}/orders/{order_id}/refund", timeout=5)
    if "无权操作该订单" not in resp.text:
        fail_with_screenshot(driver, "refund_forbidden",
                             "普通用户退别人订单，未返回「无权操作该订单」")

    # 清理：alice 正常退掉，避免库存长期被占用
    alice_api.post(f"{base_url}/orders/{order_id}/refund", timeout=5)
