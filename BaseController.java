package com.example.trainticket.web;

import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.ModelAttribute;

public abstract class BaseController {

    @ModelAttribute("username")
    public String currentUsername(HttpSession session) {
        Object value = session.getAttribute("username");
        return value == null ? "" : value.toString();
    }

    @ModelAttribute("role")
    public String currentRole(HttpSession session) {
        Object value = session.getAttribute("role");
        return value == null ? "" : value.toString();
    }
}
