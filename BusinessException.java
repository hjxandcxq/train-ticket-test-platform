package com.example.trainticket.service;

/**
 * 业务校验失败：由页面捕获并把 message 显示给用户。
 */
public class BusinessException extends RuntimeException {

    public BusinessException(String message) {
        super(message);
    }
}
