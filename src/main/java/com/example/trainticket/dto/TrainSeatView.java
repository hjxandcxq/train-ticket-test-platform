package com.example.trainticket.dto;

import java.math.BigDecimal;

public record TrainSeatView(
        Long seatId,
        String trainNo,
        String fromStation,
        String toStation,
        String travelDate,
        String departTime,
        String arriveTime,
        String duration,
        String seatType,
        BigDecimal price,
        int stock
) {
}
