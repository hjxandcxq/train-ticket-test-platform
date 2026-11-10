-- ============================================================
-- 步骤 1：创建数据库与应用账号（用 root 或有权限的账号执行）
--
-- 首次安装前：
--   1) 把下面两处 __DB_PASSWORD__ 替换成本机要用的密码
--   2) 记住这个密码，应用启动时通过 DB_PASSWORD 环境变量传入
--
-- 已经建过库/账号的环境不要重复执行本文件，避免把现有密码改掉。
-- 完整说明见 docs/数据库安装与初始化.md。
-- ============================================================

CREATE DATABASE IF NOT EXISTS train_ticket
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 同时创建 localhost 与 127.0.0.1 两个 host：
-- JDBC 用 127.0.0.1 走 TCP，MySQL 的 host 匹配与 localhost 不是同一个条目。
CREATE USER IF NOT EXISTS 'train_app'@'localhost' IDENTIFIED BY '__DB_PASSWORD__';
CREATE USER IF NOT EXISTS 'train_app'@'127.0.0.1' IDENTIFIED BY '__DB_PASSWORD__';

ALTER USER 'train_app'@'localhost' IDENTIFIED BY '__DB_PASSWORD__';
ALTER USER 'train_app'@'127.0.0.1' IDENTIFIED BY '__DB_PASSWORD__';

GRANT ALL PRIVILEGES ON train_ticket.* TO 'train_app'@'localhost';
GRANT ALL PRIVILEGES ON train_ticket.* TO 'train_app'@'127.0.0.1';
FLUSH PRIVILEGES;
