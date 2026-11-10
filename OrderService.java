package com.example.trainticket.service;

import com.example.trainticket.dto.OrderView;
import com.example.trainticket.entity.TicketOrder;
import com.example.trainticket.entity.Train;
import com.example.trainticket.entity.TrainSeat;
import com.example.trainticket.repository.TicketOrderRepository;
import com.example.trainticket.repository.TrainSeatRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;

@Service
public class OrderService {

    private static final DateTimeFormatter DATE_TIME =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter HH_MM = DateTimeFormatter.ofPattern("HH:mm");

    private final TicketOrderRepository ticketOrderRepository;
    private final TrainSeatRepository trainSeatRepository;

    public OrderService(TicketOrderRepository ticketOrderRepository,
                        TrainSeatRepository trainSeatRepository) {
        this.ticketOrderRepository = ticketOrderRepository;
        this.trainSeatRepository = trainSeatRepository;
    }

    @Transactional(readOnly = true)
    public List<OrderView> listForUser(Long userId) {
        return ticketOrderRepository.findByUserIdOrderByCreatedAtDesc(userId).stream()
                .map(this::toView)
                .toList();
    }

    @Transactional(readOnly = true)
    public List<OrderView> recent() {
        return ticketOrderRepository.findTop20ByOrderByCreatedAtDesc().stream()
                .map(this::toView)
                .toList();
    }

    private OrderView toView(TicketOrder order) {
        Optional<TrainSeat> seatOpt = trainSeatRepository.findById(order.getSeatId());
        if (seatOpt.isEmpty()) {
            return new OrderView(order.getId(), order.getOrderNo(), "-", "车次信息缺失",
                    "-", "-", "-", order.getPassengerName(), order.getAmount(),
                    order.getStatus().name(), order.getCreatedAt().format(DATE_TIME));
        }
        TrainSeat seat = seatOpt.get();
        Train train = seat.getTrain();
        return new OrderView(
                order.getId(),
                order.getOrderNo(),
                train.getTrainNo(),
                train.getFromStation() + " → " + train.getToStation(),
                seat.getTravelDate().toString(),
                train.getDepartTime().format(HH_MM),
                seat.getSeatType(),
                order.getPassengerName(),
                order.getAmount(),
                order.getStatus().name(),
                order.getCreatedAt().format(DATE_TIME)
        );
    }
}
