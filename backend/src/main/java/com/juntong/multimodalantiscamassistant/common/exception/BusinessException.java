package com.juntong.multimodalantiscamassistant.common.exception;

import lombok.Getter;

/**
 * 业务异常，由 GlobalExceptionHandler 统一捕获并返回友好提示
 */
@Getter
public class BusinessException extends RuntimeException {

    private final Integer code;

    public BusinessException(String message) {
        super(message);
        this.code = 500;
    }

    public BusinessException(Integer code, String message) {
        super(message);
        this.code = code;
    }
}
