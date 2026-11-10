package com.example.trainticket.config;

import com.example.trainticket.entity.Role;
import com.example.trainticket.entity.Train;
import com.example.trainticket.entity.TrainSeat;
import com.example.trainticket.entity.User;
import com.example.trainticket.repository.TrainRepository;
import com.example.trainticket.repository.TrainSeatRepository;
import com.example.trainticket.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

/**
 * 仅 app.seed-demo=true（h2 演示 profile）时执行。
 * MySQL 模式的数据由 db/02_seed.sql 初始化。
 */
@Component
@ConditionalOnProperty(name = "app.seed-demo", havingValue = "true")
public class DemoDataInitializer implements CommandLineRunner {

    private final UserRepository userRepository;
    private final TrainRepository trainRepository;
    private final TrainSeatRepository trainSeatRepository;
    private final PasswordEncoder passwordEncoder;

    public DemoDataInitializer(UserRepository userRepository,
                               TrainRepository trainRepository,
                               TrainSeatRepository trainSeatRepository,
                               PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.trainRepository = trainRepository;
        this.trainSeatRepository = trainSeatRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {
        if (userRepository.count() == 0) {
            createUser("admin", "admin123", Role.ADMIN);
            createUser("alice01", "Pass123", Role.USER);
            createUser("bob01", "Pass123", Role.USER);
        }

        if (trainRepository.count() == 0) {
            List<TrainSeed> seeds = List.of(
                    new TrainSeed("G101", "北京南", "上海虹桥", "08:00", "12:30", "553.00"),
                    new TrainSeed("G102", "上海虹桥", "北京南", "14:00", "18:30", "553.00"),
                    new TrainSeed("D301", "北京南", "南京南", "09:15", "13:20", "443.00"),
                    new TrainSeed("G201", "广州南", "深圳北", "07:30", "08:05", "75.00"),
                    new TrainSeed("G202", "深圳北", "广州南", "18:10", "18:45", "75.00"),
                    new TrainSeed("K101", "北京西", "西安", "20:00", "06:30", "156.00"),
                    new TrainSeed("Z201", "上海", "杭州东", "10:00", "11:10", "73.00"),
                    new TrainSeed("G301", "杭州东", "南京南", "13:00", "14:40", "309.00"),
                    new TrainSeed("D401", "成都东", "重庆北", "16:20", "18:05", "96.00"),
                    new TrainSeed("G401", "武汉", "长沙南", "11:40", "13:10", "164.00")
            );
            for (TrainSeed seed : seeds) {
                createTrain(seed);
            }
        }

        System.out.println("[demo] H2 演示数据就绪：admin/admin123、alice01/Pass123、bob01/Pass123");
    }

    private void createUser(String username, String rawPassword, Role role) {
        User user = new User();
        user.setUsername(username);
        user.setPasswordHash(passwordEncoder.encode(rawPassword));
        user.setRole(role);
        userRepository.save(user);
    }

    private void createTrain(TrainSeed seed) {
        LocalTime depart = LocalTime.parse(seed.depart());
        LocalTime arrive = LocalTime.parse(seed.arrive());
        long minutes = Duration.between(depart, arrive).toMinutes();
        if (minutes <= 0) {
            minutes += 24 * 60;
        }
        BigDecimal basePrice = new BigDecimal(seed.basePrice());

        Train train = new Train();
        train.setTrainNo(seed.trainNo());
        train.setFromStation(seed.from());
        train.setToStation(seed.to());
        train.setDepartTime(depart);
        train.setArriveTime(arrive);
        train.setDurationMinutes((int) minutes);
        train.setBasePrice(basePrice);
        train = trainRepository.save(train);

        for (int i = 1; i <= 3; i++) {
            LocalDate date = LocalDate.now().plusDays(i);
            createSeat(train, date, "二等座", basePrice, 100);
            createSeat(train, date, "一等座",
                    basePrice.multiply(new BigDecimal("1.60")).setScale(2, RoundingMode.HALF_UP), 20);
        }
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

    private record TrainSeed(String trainNo, String from, String to,
                             String depart, String arrive, String basePrice) {
    }
}
