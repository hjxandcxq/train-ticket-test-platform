package com.example.trainticket.repository;

import com.example.trainticket.entity.TrainSeat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;

public interface TrainSeatRepository extends JpaRepository<TrainSeat, Long> {

    @Query("""
            select s from TrainSeat s
            join fetch s.train t
            where t.fromStation = :fromStation
              and t.toStation = :toStation
              and s.travelDate = :travelDate
            order by t.departTime asc, s.price asc
            """)
    List<TrainSeat> search(@Param("fromStation") String fromStation,
                           @Param("toStation") String toStation,
                           @Param("travelDate") LocalDate travelDate);

    /**
     * 原子扣减余票：stock > 0 时才减 1。
     * 返回 0 表示余票不足，这是并发下单不超卖的关键。
     */
    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("update TrainSeat s set s.stock = s.stock - 1 where s.id = :id and s.stock > 0")
    int decrementStock(@Param("id") Long id);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("update TrainSeat s set s.stock = s.stock + 1 where s.id = :id")
    int incrementStock(@Param("id") Long id);
}
