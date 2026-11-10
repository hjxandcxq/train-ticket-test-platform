package com.example.trainticket.repository;

import com.example.trainticket.entity.Train;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface TrainRepository extends JpaRepository<Train, Long> {

    List<Train> findAllByOrderByDepartTimeAsc();

    boolean existsByTrainNoAndFromStationAndToStation(String trainNo,
                                                      String fromStation,
                                                      String toStation);

    @Query("select distinct t.fromStation from Train t order by t.fromStation")
    List<String> findDistinctFromStations();

    @Query("select distinct t.toStation from Train t order by t.toStation")
    List<String> findDistinctToStations();
}
