-- ============================================================
-- 压测数据：20 个用户 + 5 条线路（每条 3 种席别、不同价格、充足库存）
-- 可重复执行：先清该批车次的订单/座位/车次，再重建
-- ============================================================

USE train_ticket;

-- 清理旧压测订单与车次（9001~9005）
DELETE FROM ticket_orders
WHERE seat_id IN (SELECT id FROM train_seats WHERE train_id BETWEEN 9001 AND 9005)
   OR user_id IN (SELECT id FROM users WHERE username LIKE 'perf%');

DELETE FROM train_seats WHERE train_id BETWEEN 9001 AND 9005;
DELETE FROM trains WHERE id BETWEEN 9001 AND 9005;

-- 20 个压测用户，密码统一 Pass123（BCrypt）
INSERT INTO users (username, password_hash, role) VALUES
    ('perf01', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf02', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf03', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf04', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf05', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf06', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf07', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf08', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf09', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf10', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf11', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf12', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf13', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf14', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf15', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf16', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf17', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf18', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf19', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER'),
    ('perf20', '$2b$10$lrs0wkWcmebUg/586pgQROyayWMNdw04XmDaTuTqcedlS5lwf4w/G', 'USER')
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role = VALUES(role);

-- 5 条线路，价格/历时不同
INSERT INTO trains (id, train_no, from_station, to_station, depart_time,
                    arrive_time, duration_minutes, base_price) VALUES
    (9001, 'PERF01', '北京南',   '上海虹桥', '08:00:00', '12:30:00', 270, 553.00),
    (9002, 'PERF02', '上海虹桥', '北京南',   '14:00:00', '18:30:00', 270, 553.00),
    (9003, 'PERF03', '广州南',   '深圳北',   '07:30:00', '08:05:00',  35,  75.00),
    (9004, 'PERF04', '成都东',   '重庆北',   '16:20:00', '18:05:00', 105,  96.00),
    (9005, 'PERF05', '武汉',     '长沙南',   '11:40:00', '13:10:00',  90, 164.00);

-- 每条线路 3 种席别：二等座 1000 张、一等座 200 张、商务座 50 张
INSERT INTO train_seats (id, train_id, travel_date, seat_type, price, stock) VALUES
    (9001, 9001, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '二等座',  553.00, 1000),
    (9002, 9001, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '一等座',  884.80,  200),
    (9003, 9001, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '商务座', 1382.50,   50),
    (9004, 9002, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '二等座',  553.00, 1000),
    (9005, 9002, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '一等座',  884.80,  200),
    (9006, 9002, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '商务座', 1382.50,   50),
    (9007, 9003, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '二等座',   75.00, 1000),
    (9008, 9003, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '一等座',  120.00,  200),
    (9009, 9003, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '商务座',  187.50,   50),
    (9010, 9004, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '二等座',   96.00, 1000),
    (9011, 9004, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '一等座',  153.60,  200),
    (9012, 9004, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '商务座',  240.00,   50),
    (9013, 9005, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '二等座',  164.00, 1000),
    (9014, 9005, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '一等座',  262.40,  200),
    (9015, 9005, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '商务座',  410.00,   50);
