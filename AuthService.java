package com.example.trainticket.service;

import com.example.trainticket.entity.Role;
import com.example.trainticket.entity.User;
import com.example.trainticket.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.regex.Pattern;

@Service
public class AuthService {

    private static final Pattern USERNAME_RE = Pattern.compile("^[A-Za-z0-9_]+$");
    private static final Pattern PASSWORD_RE = Pattern.compile("^[A-Za-z0-9@#$_\\.]+$");
    private static final Pattern HAS_LETTER = Pattern.compile("[A-Za-z]");
    private static final Pattern HAS_DIGIT = Pattern.compile("\\d");

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    public User login(String username, String password) {
        String name = username == null ? "" : username.trim();
        String pwd = password == null ? "" : password;
        if (name.isEmpty() || pwd.isEmpty()) {
            throw new BusinessException("用户名和密码不能为空");
        }
        User user = userRepository.findByUsername(name)
                .orElseThrow(() -> new BusinessException("用户名或密码错误"));
        if (!passwordEncoder.matches(pwd, user.getPasswordHash())) {
            throw new BusinessException("用户名或密码错误");
        }
        return user;
    }

    @Transactional
    public User register(String username, String password, String confirm) {
        String name = username == null ? "" : username.trim();
        String pwd = password == null ? "" : password;
        String confirmPwd = confirm == null ? "" : confirm;

        if (name.isEmpty()) {
            throw new BusinessException("用户名必填");
        }
        if (name.length() < 4 || name.length() > 20) {
            throw new BusinessException("用户名长度4-20位");
        }
        if (!USERNAME_RE.matcher(name).matches()) {
            throw new BusinessException("用户名只能包含字母、数字和下划线");
        }
        if (pwd.isEmpty()) {
            throw new BusinessException("密码必填");
        }
        if (pwd.length() < 6 || pwd.length() > 20) {
            throw new BusinessException("密码长度6-20位");
        }
        if (!PASSWORD_RE.matcher(pwd).matches()) {
            throw new BusinessException("密码只能包含字母、数字和@#$._");
        }
        if (!HAS_LETTER.matcher(pwd).find() || !HAS_DIGIT.matcher(pwd).find()) {
            throw new BusinessException("密码必须同时包含字母和数字");
        }
        if (!pwd.equals(confirmPwd)) {
            throw new BusinessException("两次密码不一致");
        }
        if (userRepository.existsByUsername(name)) {
            throw new BusinessException("用户名已存在");
        }

        User user = new User();
        user.setUsername(name);
        user.setPasswordHash(passwordEncoder.encode(pwd));
        user.setRole(Role.USER);
        return userRepository.save(user);
    }
}
