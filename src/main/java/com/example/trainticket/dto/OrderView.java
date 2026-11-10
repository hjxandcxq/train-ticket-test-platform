package com.example.trainticket.dto;

import java.math.BigDecimal;

public record OrderView(
        Long id,
        String orderNo,
        String trainNo,
        String route,
        String travelDate,
        String departTime,
        String seatType,
        String passengerName,
        BigDecimal amount,
        String status,
        String createdAt
) {
}
