package com.example.trainticket;

import com.example.trainticket.entity.OrderStatus;
import com.example.trainticket.entity.Role;
import com.example.trainticket.entity.TicketOrder;
import com.example.trainticket.entity.Train;
import com.example.trainticket.entity.TrainSeat;
import com.example.trainticket.entity.User;
import com.example.trainticket.repository.TicketOrderRepository;
import com.example.trainticket.repository.TrainRepository;
import com.example.trainticket.repository.TrainSeatRepository;
import com.example.trainticket.repository.UserRepository;
import com.example.trainticket.service.BookingService;
import com.example.trainticket.service.BusinessException;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * 并发下单/退票的正确性测试
 * 验证：余票10张、50个并发请求，只能成功10单，且不发生超卖
 */
@SpringBootTest(properties = "app.seed-demo=false")
@ActiveProfiles("h2")
class BookingConcurrencyTest {

    @Autowired
    private BookingService bookingService;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private TrainRepository trainRepository;
    @Autowired
    private TrainSeatRepository trainSeatRepository;
    @Autowired
    private TicketOrderRepository ticketOrderRepository;
    @Autowired
    private PasswordEncoder passwordEncoder;

    private Long userId;
    private Long seatId;

    @BeforeEach
    void setUp() {
        ticketOrderRepository.deleteAll();
        trainSeatRepository.deleteAll();
        trainRepository.deleteAll();
        userRepository.deleteAll();

        User user = new User();
        user.setUsername("tester01");
        user.setPasswordHash(passwordEncoder.encode("Pass123"));
        user.setRole(Role.USER);
        userId = userRepository.save(user).getId();

        Train train = new Train();
        train.setTrainNo("G999");
        train.setFromStation("北京南");
        train.setToStation("上海虹桥");
        train.setDepartTime(LocalTime.of(8, 0));
        train.setArriveTime(LocalTime.of(12, 30));
        train.setDurationMinutes(270);
        train.setBasePrice(new BigDecimal("553.00"));
        train = trainRepository.save(train);

        TrainSeat seat = new TrainSeat();
        seat.setTrain(train);
        seat.setTravelDate(LocalDate.now().plusDays(1));
        seat.setSeatType("二等座");
        seat.setPrice(new BigDecimal("553.00"));
        seat.setStock(10);
        seatId = trainSeatRepository.save(seat).getId();
    }

    @AfterEach
    void tearDown() {
        ticketOrderRepository.deleteAll();
        trainSeatRepository.deleteAll();
        trainRepository.deleteAll();
        userRepository.deleteAll();
    }

    @Test
    void fiftyConcurrentBookingsOnlySellTenTickets() throws Exception {
        int attempts = 50;
        ExecutorService pool = Executors.newFixedThreadPool(32);
        CountDownLatch ready = new CountDownLatch(attempts);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(attempts);
        AtomicInteger success = new AtomicInteger();
        AtomicInteger soldOut = new AtomicInteger();
        AtomicInteger unexpected = new AtomicInteger();
        List<String> errors = new ArrayList<>();

        for (int i = 0; i < attempts; i++) {
            final int index = i;
            pool.submit(() -> {
                ready.countDown();
                try {
                    start.await();
                    bookingService.book(userId, seatId, "乘客" + index);
                    success.incrementAndGet();
                } catch (BusinessException e) {
                    if (e.getMessage().contains("余票不足")) {
                        soldOut.incrementAndGet();
                    } else {
                        unexpected.incrementAndGet();
                        synchronized (errors) {
                            errors.add(e.getMessage());
                        }
                    }
                } catch (Exception e) {
                    unexpected.incrementAndGet();
                    synchronized (errors) {
                        errors.add(e.getClass().getSimpleName() + ": " + e.getMessage());
                    }
                } finally {
                    done.countDown();
                }
            });
        }

        ready.await(10, TimeUnit.SECONDS);
        start.countDown();
        boolean finished = done.await(90, TimeUnit.SECONDS);
        pool.shutdownNow();

        assertEquals(true, finished, "并发任务未在 90 秒内完成");
        assertEquals(0, unexpected.get(), "出现非预期异常：" + errors);
        assertEquals(10, success.get(), "成功订单数应等于初始余票数");
        assertEquals(40, soldOut.get(), "其余请求应提示余票不足");
        assertEquals(0, trainSeatRepository.findById(seatId).orElseThrow().getStock(),
                "余票应为 0");
        assertEquals(10, ticketOrderRepository.count(), "订单数应为 10");
    }

    @Test
    void refundRestoresStockAndCannotBeRepeated() {
        TicketOrder order = bookingService.book(userId, seatId, "张三");
        assertEquals(9, trainSeatRepository.findById(seatId).orElseThrow().getStock());

        bookingService.refund(order.getId(), userId, false);
        assertEquals(10, trainSeatRepository.findById(seatId).orElseThrow().getStock());
        assertEquals(OrderStatus.REFUNDED,
                ticketOrderRepository.findById(order.getId()).orElseThrow().getStatus());

        assertThrows(BusinessException.class,
                () -> bookingService.refund(order.getId(), userId, false));
        assertEquals(10, trainSeatRepository.findById(seatId).orElseThrow().getStock(),
                "重复退票不能再次加回余票");
    }
}
