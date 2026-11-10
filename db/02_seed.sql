-- ============================================================
-- 火车票预订系统 —— 初始化演示数据（MySQL 8.x）
-- 前置：先执行 01_schema.sql
-- 说明：可重复执行；车票日期为“执行脚本当天 + 1/2/3 天”
-- ============================================================

USE train_ticket;

-- 账号：admin/admin123（管理员）、alice01/Pass123（普通用户）、bob01/Pass123（普通用户）
INSERT INTO users (username, password_hash, role) VALUES
    ('admin',   '$2b$10$5iPZBRU6uEVqnYTzmVqR0OnMStQ16Zick4pESYY01dmyBH7Z1Hr86', 'ADMIN'),
    ('alice01', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('bob01',   '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER')
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role = VALUES(role);

INSERT INTO trains (train_no, from_station, to_station, depart_time,
                    arrive_time, duration_minutes, base_price) VALUES
    ('G101', '北京南',   '上海虹桥', '08:00:00', '12:30:00', 270, 553.00),
    ('G102', '上海虹桥', '北京南',   '14:00:00', '18:30:00', 270, 553.00),
    ('D301', '北京南',   '南京南',   '09:15:00', '13:20:00', 245, 443.00),
    ('G201', '广州南',   '深圳北',   '07:30:00', '08:05:00',  35,  75.00),
    ('G202', '深圳北',   '广州南',   '18:10:00', '18:45:00',  35,  75.00),
    ('K101', '北京西',   '西安',     '20:00:00', '06:30:00', 630, 156.00),
    ('Z201', '上海',     '杭州东',   '10:00:00', '11:10:00',  70,  73.00),
    ('G301', '杭州东',   '南京南',   '13:00:00', '14:40:00', 100, 309.00),
    ('D401', '成都东',   '重庆北',   '16:20:00', '18:05:00', 105,  96.00),
    ('G401', '武汉',     '长沙南',   '11:40:00', '13:10:00',  90, 164.00)
ON DUPLICATE KEY UPDATE
    depart_time = VALUES(depart_time),
    arrive_time = VALUES(arrive_time),
    duration_minutes = VALUES(duration_minutes),
    base_price = VALUES(base_price);

-- 每个车次开售未来 3 天：二等座 100 张（基准价）、一等座 20 张（1.6 倍）
INSERT INTO train_seats (train_id, travel_date, seat_type, price, stock)
SELECT t.id,
       DATE_ADD(CURDATE(), INTERVAL d.n DAY),
       s.seat_type,
       ROUND(t.base_price * s.factor, 2),
       s.stock
FROM trains t
         CROSS JOIN (SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3) d
         CROSS JOIN (SELECT '二等座' AS seat_type, 1.00 AS factor, 100 AS stock
                     UNION ALL
                     SELECT '一等座', 1.60, 20) s
WHERE 1 = 1
ON DUPLICATE KEY UPDATE
    price = VALUES(price),
    stock = VALUES(stock);

-- 执行后自检（可选）
-- SELECT COUNT(*) AS users FROM users;
-- SELECT COUNT(*) AS trains FROM trains;
-- SELECT COUNT(*) AS seats FROM train_seats;
