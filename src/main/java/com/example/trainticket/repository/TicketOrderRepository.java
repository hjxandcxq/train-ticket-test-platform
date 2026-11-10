package com.example.trainticket.repository;

import com.example.trainticket.entity.OrderStatus;
import com.example.trainticket.entity.TicketOrder;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

public interface TicketOrderRepository extends JpaRepository<TicketOrder, Long> {

    List<TicketOrder> findByUserIdOrderByCreatedAtDesc(Long userId);

    List<TicketOrder> findTop20ByOrderByCreatedAtDesc();

    long countByStatus(OrderStatus status);

    @Query("select coalesce(sum(o.amount), 0) from TicketOrder o where o.status = :status")
    BigDecimal sumAmountByStatus(@Param("status") OrderStatus status);

    /**
     * 原子改状态：只有当前状态为 PAID 时才会更新成功，避免并发重复退票。
     * 返回 0 表示订单已被退过或状态不允许。
     */
    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            update TicketOrder o
            set o.status = :newStatus, o.refundedAt = :refundedAt
            where o.id = :id and o.status = :oldStatus
            """)
    int markStatus(@Param("id") Long id,
                   @Param("oldStatus") OrderStatus oldStatus,
                   @Param("newStatus") OrderStatus newStatus,
                   @Param("refundedAt") LocalDateTime refundedAt);
}
