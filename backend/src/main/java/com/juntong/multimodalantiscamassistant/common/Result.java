package com.juntong.multimodalantiscamassistant.common;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 统一响应体
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "统一响应包装模型")
public class Result<T> {

    @Schema(description = "状态码: 200=成功, 其余为异常码", example = "200")
    private Integer code;

    @Schema(description = "提示信息", example = "success")
    private String message;

    @Schema(description = "具体的业务数据内容")
    private T data;

    public static <T> Result<T> ok(T data) {
        return new Result<>(200, "success", data);
    }

    public static <T> Result<T> ok() {
        return new Result<>(200, "success", null);
    }

    public static <T> Result<T> fail(String message) {
        return new Result<>(500, message, null);
    }

    public static <T> Result<T> fail(Integer code, String message) {
        return new Result<>(code, message, null);
    }
}
