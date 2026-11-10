package com.example.trainticket.web;

import com.example.trainticket.entity.TicketOrder;
import com.example.trainticket.service.BookingService;
import com.example.trainticket.service.BusinessException;
import com.example.trainticket.service.OrderService;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class OrderController extends BaseController {

    private final BookingService bookingService;
    private final OrderService orderService;

    public OrderController(BookingService bookingService, OrderService orderService) {
        this.bookingService = bookingService;
        this.orderService = orderService;
    }

    @GetMapping("/orders")
    public String orders(HttpSession session, Model model) {
        Long userId = (Long) session.getAttribute("userId");
        model.addAttribute("orders", orderService.listForUser(userId));
        return "orders";
    }

    @PostMapping("/orders")
    public String book(@RequestParam("seatId") Long seatId,
                       @RequestParam("passengerName") String passengerName,
                       HttpSession session,
                       RedirectAttributes redirectAttributes) {
        Long userId = (Long) session.getAttribute("userId");
        try {
            TicketOrder order = bookingService.book(userId, seatId, passengerName);
            redirectAttributes.addFlashAttribute("success",
                    "购票成功，订单号 " + order.getOrderNo());
        } catch (BusinessException e) {
            redirectAttributes.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/orders";
    }

    @PostMapping("/orders/{id}/refund")
    public String refund(@PathVariable("id") Long orderId,
                         HttpSession session,
                         RedirectAttributes redirectAttributes) {
        Long userId = (Long) session.getAttribute("userId");
        try {
            bookingService.refund(orderId, userId, false);
            redirectAttributes.addFlashAttribute("success", "退票成功，票款将原路退回");
        } catch (BusinessException e) {
            redirectAttributes.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/orders";
    }
}
