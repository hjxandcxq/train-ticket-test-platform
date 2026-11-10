package com.example.trainticket.web;

import com.example.trainticket.dto.TrainSeatView;
import com.example.trainticket.service.BusinessException;
import com.example.trainticket.service.TrainService;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.time.LocalDate;
import java.util.List;

@Controller
public class TrainController extends BaseController {

    private final TrainService trainService;

    public TrainController(TrainService trainService) {
        this.trainService = trainService;
    }

    @GetMapping("/trains")
    public String trains(Model model,
                         @RequestParam(value = "forbidden", required = false) String forbidden) {
        prepareForm(model);
        model.addAttribute("results", List.of());
        model.addAttribute("searched", false);
        if (forbidden != null) {
            model.addAttribute("error", "没有管理员权限");
        }
        return "trains";
    }

    @PostMapping("/trains/search")
    public String search(@RequestParam("fromStation") String fromStation,
                         @RequestParam("toStation") String toStation,
                         @RequestParam("travelDate") String travelDate,
                         Model model) {
        prepareForm(model);
        model.addAttribute("fromStation", fromStation);
        model.addAttribute("toStation", toStation);
        model.addAttribute("travelDate", travelDate);
        model.addAttribute("searched", true);
        try {
            model.addAttribute("results",
                    trainService.search(fromStation, toStation, travelDate));
        } catch (BusinessException e) {
            model.addAttribute("error", e.getMessage());
            model.addAttribute("results", List.of());
        }
        return "trains";
    }

    private void prepareForm(Model model) {
        model.addAttribute("fromStations", trainService.fromStations());
        model.addAttribute("toStations", trainService.toStations());
        model.addAttribute("defaultDate", LocalDate.now().plusDays(1).toString());
        model.addAttribute("today", LocalDate.now().toString());
    }
}
