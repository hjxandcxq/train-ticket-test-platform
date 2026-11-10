-- 每轮压测前复位：清压测订单、余票恢复初始值、车票日期刷新为明天
USE train_ticket;

DELETE FROM ticket_orders
WHERE seat_id IN (SELECT id FROM train_seats WHERE train_id BETWEEN 9001 AND 9005)
   OR user_id IN (SELECT id FROM users WHERE username LIKE 'perf%');

UPDATE train_seats
SET travel_date = DATE_ADD(CURDATE(), INTERVAL 1 DAY)
WHERE train_id BETWEEN 9001 AND 9005;

UPDATE train_seats
SET stock = CASE seat_type
                WHEN '二等座' THEN 1000
                WHEN '一等座' THEN 200
                WHEN '商务座' THEN 50
                ELSE stock
            END
WHERE train_id BETWEEN 9001 AND 9005;
