package com.example.trainticket.web;

import com.example.trainticket.service.AdminService;
import com.example.trainticket.service.BookingService;
import com.example.trainticket.service.BusinessException;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.time.LocalDate;

@Controller
public class AdminController extends BaseController {

    private final AdminService adminService;
    private final BookingService bookingService;

    public AdminController(AdminService adminService, BookingService bookingService) {
        this.adminService = adminService;
        this.bookingService = bookingService;
    }

    @GetMapping("/admin")
    public String dashboard(Model model) {
        model.addAttribute("stats", adminService.stats());
        model.addAttribute("recentOrders", adminService.recentOrders());
        model.addAttribute("trains", adminService.trains());
        model.addAttribute("defaultDate", LocalDate.now().plusDays(1).toString());
        return "admin";
    }

    @PostMapping("/admin/trains")
    public String addTrain(@RequestParam("trainNo") String trainNo,
                           @RequestParam("fromStation") String fromStation,
                           @RequestParam("toStation") String toStation,
                           @RequestParam("departTime") String departTime,
                           @RequestParam("arriveTime") String arriveTime,
                           @RequestParam("basePrice") String basePrice,
                           RedirectAttributes redirectAttributes) {
        try {
            adminService.addTrain(trainNo, fromStation, toStation,
                    departTime, arriveTime, basePrice);
            redirectAttributes.addFlashAttribute("success", "车次添加成功，已开售未来 3 天车票");
        } catch (BusinessException e) {
            redirectAttributes.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/admin";
    }

    @PostMapping("/admin/orders/{id}/refund")
    public String refund(@PathVariable("id") Long orderId,
                         RedirectAttributes redirectAttributes) {
        try {
            bookingService.refund(orderId, null, true);
            redirectAttributes.addFlashAttribute("success", "订单已退票");
        } catch (BusinessException e) {
            redirectAttributes.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/admin";
    }
}
