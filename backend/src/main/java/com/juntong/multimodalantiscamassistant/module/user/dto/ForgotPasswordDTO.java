package com.juntong.multimodalantiscamassistant.module.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 忘记密码请求体
 */
@Data
@Schema(description = "忘记密码请求体")
public class ForgotPasswordDTO {

    @Schema(description = "用户名", example = "admin")
    @NotBlank(message = "用户名不能为空")
    private String username;

    @Schema(description = "图片验证码 key", example = "a1b2c3d4e5f6g7h8")
    @NotBlank(message = "验证码 key 不能为空")
    private String captchaKey;

    @Schema(description = "图片验证码", example = "A3mK")
    @NotBlank(message = "验证码不能为空")
    private String captchaCode;
}
