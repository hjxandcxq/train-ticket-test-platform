package com.example.trainticket.service;

import com.example.trainticket.dto.AdminStats;
import com.example.trainticket.dto.OrderView;
import com.example.trainticket.entity.OrderStatus;
import com.example.trainticket.entity.Train;
import com.example.trainticket.entity.TrainSeat;
import com.example.trainticket.repository.TicketOrderRepository;
import com.example.trainticket.repository.TrainRepository;
import com.example.trainticket.repository.TrainSeatRepository;
import com.example.trainticket.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeParseException;
import java.util.List;

@Service
public class AdminService {

    private final UserRepository userRepository;
    private final TrainRepository trainRepository;
    private final TrainSeatRepository trainSeatRepository;
    private final TicketOrderRepository ticketOrderRepository;
    private final OrderService orderService;

    public AdminService(UserRepository userRepository,
                        TrainRepository trainRepository,
                        TrainSeatRepository trainSeatRepository,
                        TicketOrderRepository ticketOrderRepository,
                        OrderService orderService) {
        this.userRepository = userRepository;
        this.trainRepository = trainRepository;
        this.trainSeatRepository = trainSeatRepository;
        this.ticketOrderRepository = ticketOrderRepository;
        this.orderService = orderService;
    }

    public AdminStats stats() {
        BigDecimal revenue = ticketOrderRepository.sumAmountByStatus(OrderStatus.PAID);
        return new AdminStats(
                userRepository.count(),
                trainRepository.count(),
                ticketOrderRepository.count(),
                ticketOrderRepository.countByStatus(OrderStatus.PAID),
                revenue == null ? BigDecimal.ZERO : revenue
        );
    }

    public List<OrderView> recentOrders() {
        return orderService.recent();
    }

    public List<Train> trains() {
        return trainRepository.findAllByOrderByDepartTimeAsc();
    }

    @Transactional
    public Train addTrain(String trainNo, String fromStation, String toStation,
                          String departTime, String arriveTime, String basePrice) {
        String no = trim(trainNo);
        String from = trim(fromStation);
        String to = trim(toStation);

        if (no.isEmpty()) {
            throw new BusinessException("车次号必填");
        }
        if (from.isEmpty() || to.isEmpty()) {
            throw new BusinessException("出发站和到达站不能为空");
        }
        if (from.equals(to)) {
            throw new BusinessException("出发站和到达站不能相同");
        }
        if (trainRepository.existsByTrainNoAndFromStationAndToStation(no, from, to)) {
            throw new BusinessException("该车次线路已存在");
        }

        LocalTime depart = parseTime(departTime, "出发时间");
        LocalTime arrive = parseTime(arriveTime, "到达时间");
        long minutes = Duration.between(depart, arrive).toMinutes();
        if (minutes <= 0) {
            minutes += 24 * 60;      // 跨天车次
        }

        BigDecimal price;
        try {
            price = new BigDecimal(trim(basePrice));
        } catch (NumberFormatException e) {
            throw new BusinessException("票价格式不正确");
        }
        if (price.compareTo(BigDecimal.ZERO) <= 0) {
            throw new BusinessException("票价必须大于0");
        }
        price = price.setScale(2, RoundingMode.HALF_UP);

        Train train = new Train();
        train.setTrainNo(no);
        train.setFromStation(from);
        train.setToStation(to);
        train.setDepartTime(depart);
        train.setArriveTime(arrive);
        train.setDurationMinutes((int) minutes);
        train.setBasePrice(price);
        Train saved = trainRepository.save(train);

        // 新加车次默认开售未来 3 天：二等座 100 张、一等座 20 张
        for (int i = 1; i <= 3; i++) {
            LocalDate date = LocalDate.now().plusDays(i);
            createSeat(saved, date, "二等座", price, 100);
            createSeat(saved, date, "一等座",
                    price.multiply(new BigDecimal("1.60")).setScale(2, RoundingMode.HALF_UP), 20);
        }
        return saved;
    }

    private void createSeat(Train train, LocalDate date, String seatType,
                            BigDecimal price, int stock) {
        TrainSeat seat = new TrainSeat();
        seat.setTrain(train);
        seat.setTravelDate(date);
        seat.setSeatType(seatType);
        seat.setPrice(price);
        seat.setStock(stock);
        trainSeatRepository.save(seat);
    }

    private LocalTime parseTime(String value, String field) {
        try {
            return LocalTime.parse(trim(value));
        } catch (DateTimeParseException e) {
            throw new BusinessException(field + "格式应为 HH:mm");
        }
    }

    private String trim(String value) {
        return value == null ? "" : value.trim();
    }
}
