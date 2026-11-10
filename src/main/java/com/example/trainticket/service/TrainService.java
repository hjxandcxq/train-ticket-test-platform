package com.example.trainticket.service;

import com.example.trainticket.dto.TrainSeatView;
import com.example.trainticket.entity.Train;
import com.example.trainticket.entity.TrainSeat;
import com.example.trainticket.repository.TrainRepository;
import com.example.trainticket.repository.TrainSeatRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.List;

@Service
public class TrainService {

    private static final DateTimeFormatter HH_MM = DateTimeFormatter.ofPattern("HH:mm");

    private final TrainRepository trainRepository;
    private final TrainSeatRepository trainSeatRepository;

    public TrainService(TrainRepository trainRepository,
                        TrainSeatRepository trainSeatRepository) {
        this.trainRepository = trainRepository;
        this.trainSeatRepository = trainSeatRepository;
    }

    @Transactional(readOnly = true)
    public List<TrainSeatView> search(String fromStation, String toStation, String travelDate) {
        String from = fromStation == null ? "" : fromStation.trim();
        String to = toStation == null ? "" : toStation.trim();

        if (from.isEmpty() || to.isEmpty()) {
            throw new BusinessException("出发站和到达站不能为空");
        }
        if (from.equals(to)) {
            throw new BusinessException("出发站和到达站不能相同");
        }

        LocalDate date;
        try {
            date = LocalDate.parse(travelDate == null ? "" : travelDate.trim());
        } catch (DateTimeParseException e) {
            throw new BusinessException("请选择正确的出行日期");
        }
        if (date.isBefore(LocalDate.now())) {
            throw new BusinessException("出行日期不能早于今天");
        }

        return trainSeatRepository.search(from, to, date).stream()
                .map(this::toView)
                .toList();
    }

    public List<String> fromStations() {
        return trainRepository.findDistinctFromStations();
    }

    public List<String> toStations() {
        return trainRepository.findDistinctToStations();
    }

    public List<Train> allTrains() {
        return trainRepository.findAllByOrderByDepartTimeAsc();
    }

    private TrainSeatView toView(TrainSeat seat) {
        Train train = seat.getTrain();
        return new TrainSeatView(
                seat.getId(),
                train.getTrainNo(),
                train.getFromStation(),
                train.getToStation(),
                seat.getTravelDate().toString(),
                train.getDepartTime().format(HH_MM),
                train.getArriveTime().format(HH_MM),
                formatDuration(train.getDurationMinutes()),
                seat.getSeatType(),
                seat.getPrice(),
                seat.getStock()
        );
    }

    public static String formatDuration(int minutes) {
        return (minutes / 60) + "小时" + (minutes % 60) + "分";
    }
}
