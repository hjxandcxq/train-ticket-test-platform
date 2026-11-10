# functional_tests — Selenium 功能自动化

覆盖登录、注册、车次查询、下单、退票、管理后台的成功与失败场景。

## 前置

- 8080 上的应用使用 MySQL 模式运行（`TrainTicketApplication (MySQL)`）
- MySQL 已有 `db/01_schema.sql`、`db/02_seed.sql` 的初始数据
- 本机有 Chrome 或 Edge

## 安装

```bat
cd D:\AIBase\测试作业\train-ticket-java
python -m venv .venv-tests
.venv-tests\Scripts\python.exe -m pip install -r functional_tests\requirements.txt
```

## 运行

```bat
cd functional_tests
..\.venv-tests\Scripts\python.exe -m pytest -v --html=report.html --self-contained-html
```

或直接双击 `functional_tests\run_tests.bat`。

套件启动时会自动执行 `00_test_seed.sql`，重置功能测试专用车次 `FUNC01`（id=9100）和座位：

- 9101 二等座：余票 50（下单成功）
- 9102 一等座：余票 0（余票不足）
- 9103 商务座：余票 50（退票）

数据库连接从环境变量或 `functional_tests/.env` 读取，默认 `train_app @ 127.0.0.1:3306/train_ticket`；
**没有默认密码**，请新建 `.env` 并填写本机数据库密码（仓库不提供模板，`.env` 已被 `.gitignore` 忽略）：

```bat
rem 新建 functional_tests\.env，写入：
rem DB_HOST=127.0.0.1
rem DB_USERNAME=train_app
rem DB_PASSWORD=你的本机密码
set TT_BASE_URL=http://127.0.0.1:8080
set TT_HEADLESS=0   &:: 显示浏览器窗口
```

也可以直接用环境变量覆盖（不创建 `.env`）：

```bat
set DB_HOST=127.0.0.1
set DB_PORT=3306
set DB_USERNAME=train_app
set DB_PASSWORD=你的本机密码
set DB_NAME=train_ticket
```

## 用例清单

| 文件 | 成功 | 失败 |
|------|------|------|
| `test_login.py` | 正确账号密码登录 | 密码错误、账号不存在、用户名/密码为空 |
| `test_register.py` | 注册成功并登录 | 用户名已存在、两次密码不一致、弱密码、用户名过短 |
| `test_search.py` | 北京南→上海虹桥查询到 G101/FUNC01 | 同站、缺站、无结果、过去日期 |
| `test_booking.py` | 有票座位下单成功 | 未登录访问订单、座位不存在、余票不足、乘客姓名为空 |
| `test_refund.py` | 退票成功且库存回补 | 重复退票、退别人的订单 |
| `test_admin.py` | 管理员进入后台、添加车次 | 普通用户越权、重复线路 |

失败用例的截图保存在 `functional_tests/screenshots/`，HTML 报告为 `functional_tests/report.html`。
