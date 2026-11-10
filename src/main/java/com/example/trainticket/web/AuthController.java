package com.example.trainticket.web;

import com.example.trainticket.entity.User;
import com.example.trainticket.service.AuthService;
import com.example.trainticket.service.BusinessException;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @GetMapping("/")
    public String index(HttpSession session) {
        return session.getAttribute("userId") == null ? "redirect:/login" : "redirect:/trains";
    }

    @GetMapping("/login")
    public String loginPage(HttpSession session,
                            @RequestParam(value = "registered", required = false) String registered,
                            Model model) {
        if (session.getAttribute("userId") != null) {
            return "redirect:/trains";
        }
        if (registered != null) {
            model.addAttribute("success", "注册成功，请登录");
        }
        return "login";
    }

    @PostMapping("/login")
    public String login(@RequestParam("uname") String username,
                        @RequestParam("pword") String password,
                        HttpSession session,
                        Model model) {
        try {
            User user = authService.login(username, password);
            session.setAttribute("userId", user.getId());
            session.setAttribute("username", user.getUsername());
            session.setAttribute("role", user.getRole().name());
            return "redirect:/trains";
        } catch (BusinessException e) {
            model.addAttribute("error", e.getMessage());
            model.addAttribute("uname", username);
            return "login";
        }
    }

    @GetMapping("/register")
    public String registerPage() {
        return "register";
    }

    @PostMapping("/register")
    public String register(@RequestParam("username") String username,
                           @RequestParam("password") String password,
                           @RequestParam("confirm") String confirm,
                           Model model) {
        try {
            authService.register(username, password, confirm);
            return "redirect:/login?registered=1";
        } catch (BusinessException e) {
            model.addAttribute("error", e.getMessage());
            model.addAttribute("username", username);
            return "register";
        }
    }

    @GetMapping("/logout")
    public String logout(HttpSession session) {
        session.invalidate();
        return "redirect:/login";
    }
}
