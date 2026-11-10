-- 压测结束后清理专用数据（可选）
-- 注意：会删除 PERF01 车次、座位 9001 及其测试订单
USE train_ticket;

DELETE FROM ticket_orders
WHERE seat_id IN (SELECT id FROM train_seats WHERE train_id = 9001);

DELETE FROM train_seats WHERE train_id = 9001;
DELETE FROM trains WHERE id = 9001;
