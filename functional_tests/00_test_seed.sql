-- 功能自动化测试专用数据
-- 车次 FUNC01（id=9100）：二等座有票、一等座无票、商务座用于退票
USE train_ticket;

DELETE FROM ticket_orders
WHERE seat_id IN (SELECT id FROM train_seats WHERE train_id = 9100);

DELETE FROM train_seats WHERE train_id = 9100;
DELETE FROM trains WHERE id = 9100;

DELETE FROM ticket_orders
WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'func_%');
DELETE FROM users WHERE username LIKE 'func_%';

INSERT INTO trains (id, train_no, from_station, to_station, depart_time,
                    arrive_time, duration_minutes, base_price)
VALUES (9100, 'FUNC01', '北京南', '上海虹桥', '22:00:00', '22:30:00', 30, 1.00);

INSERT INTO train_seats (id, train_id, travel_date, seat_type, price, stock) VALUES
    (9101, 9100, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '二等座', 1.00, 50),
    (9102, 9100, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '一等座', 2.00, 0),
    (9103, 9100, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '商务座', 3.00, 50);
