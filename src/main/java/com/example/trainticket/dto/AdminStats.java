package com.example.trainticket.dto;

import java.math.BigDecimal;

public record AdminStats(
        long users,
        long trains,
        long orders,
        long paidOrders,
        BigDecimal revenue
) {
}
