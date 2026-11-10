-- ============================================================
-- 步骤 2：建表脚本
-- 前置：已执行 00_create_database.sql，数据库 train_ticket 已存在
-- ============================================================

USE train_ticket;

CREATE TABLE IF NOT EXISTS users (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'USER',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_username (username)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS trains (
    id               BIGINT        NOT NULL AUTO_INCREMENT,
    train_no         VARCHAR(20)   NOT NULL,
    from_station     VARCHAR(50)   NOT NULL,
    to_station       VARCHAR(50)   NOT NULL,
    depart_time      TIME          NOT NULL,
    arrive_time      TIME          NOT NULL,
    duration_minutes INT           NOT NULL,
    base_price       DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_train_route (train_no, from_station, to_station),
    KEY idx_train_route (from_station, to_station)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS train_seats (
    id          BIGINT         NOT NULL AUTO_INCREMENT,
    train_id    BIGINT         NOT NULL,
    travel_date DATE           NOT NULL,
    seat_type   VARCHAR(20)    NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    stock       INT            NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_seat (train_id, travel_date, seat_type),
    KEY idx_seat_route_date (train_id, travel_date),
    CONSTRAINT fk_seat_train FOREIGN KEY (train_id) REFERENCES trains (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS ticket_orders (
    id             BIGINT         NOT NULL AUTO_INCREMENT,
    order_no       VARCHAR(32)    NOT NULL,
    user_id        BIGINT         NOT NULL,
    seat_id        BIGINT         NOT NULL,
    passenger_name VARCHAR(50)    NOT NULL,
    amount         DECIMAL(10, 2) NOT NULL,
    status         VARCHAR(20)    NOT NULL DEFAULT 'PAID',
    created_at     DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    refunded_at    DATETIME       NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uk_order_no (order_no),
    KEY idx_order_user (user_id),
    KEY idx_order_seat (seat_id),
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_order_seat FOREIGN KEY (seat_id) REFERENCES train_seats (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;
