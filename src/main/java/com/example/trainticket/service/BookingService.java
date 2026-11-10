package com.example.trainticket.service;

import com.example.trainticket.entity.OrderStatus;
import com.example.trainticket.entity.TicketOrder;
import com.example.trainticket.entity.TrainSeat;
import com.example.trainticket.repository.TicketOrderRepository;
import com.example.trainticket.repository.TrainSeatRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class BookingService {

    private final TrainSeatRepository trainSeatRepository;
    private final TicketOrderRepository ticketOrderRepository;

    public BookingService(TrainSeatRepository trainSeatRepository,
                          TicketOrderRepository ticketOrderRepository) {
        this.trainSeatRepository = trainSeatRepository;
        this.ticketOrderRepository = ticketOrderRepository;
    }

    /**
     * 下单：先原子扣减余票，再写订单；两步在同一个事务里。
     * 并发下只有抢到余票的线程能生成订单，不会超卖。
     */
    @Transactional
    public TicketOrder book(Long userId, Long seatId, String passengerName) {
        if (userId == null) {
            throw new BusinessException("请先登录");
        }
        String passenger = passengerName == null ? "" : passengerName.trim();
        if (passenger.isEmpty()) {
            throw new BusinessException("乘客姓名必填");
        }
        if (passenger.length() > 50) {
            throw new BusinessException("乘客姓名不能超过50个字符");
        }

        TrainSeat seat = trainSeatRepository.findById(seatId)
                .orElseThrow(() -> new BusinessException("车次席别不存在"));
        if (seat.getTravelDate().isBefore(LocalDate.now())) {
            throw new BusinessException("该日期已无法购票");
        }

        int updated = trainSeatRepository.decrementStock(seatId);
        if (updated == 0) {
            throw new BusinessException("该车次余票不足");
        }

        TicketOrder order = new TicketOrder();
        order.setOrderNo(nextOrderNo());
        order.setUserId(userId);
        order.setSeatId(seatId);
        order.setPassengerName(passenger);
        order.setAmount(seat.getPrice());
        order.setStatus(OrderStatus.PAID);
        return ticketOrderRepository.save(order);
    }

    /**
     * 退票：先原子改订单状态（防重复退），再把余票加回去。
     */
    @Transactional
    public void refund(Long orderId, Long userId, boolean admin) {
        TicketOrder order = ticketOrderRepository.findById(orderId)
                .orElseThrow(() -> new BusinessException("订单不存在"));
        if (!admin && !order.getUserId().equals(userId)) {
            throw new BusinessException("无权操作该订单");
        }
        int updated = ticketOrderRepository.markStatus(
                orderId, OrderStatus.PAID, OrderStatus.REFUNDED, LocalDateTime.now());
        if (updated == 0) {
            throw new BusinessException("订单已退票或状态不允许");
        }
        trainSeatRepository.incrementStock(order.getSeatId());
    }

    private String nextOrderNo() {
        return "T" + System.currentTimeMillis()
                + UUID.randomUUID().toString().substring(0, 6).toUpperCase();
    }
}
