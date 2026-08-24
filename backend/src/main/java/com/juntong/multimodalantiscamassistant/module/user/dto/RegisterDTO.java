package com.juntong.multimodalantiscamassistant.module.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 用户注册请求体
 */
@Data
@Schema(description = "用户注册请求体")
public class RegisterDTO {

    @Schema(description = "用户名 (3~50字)", example = "zhangsan")
    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度需在 3~50 个字符之间")
    private String username;

    @Schema(description = "密码 (至少6位)", example = "123456")
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 100, message = "密码长度至少 6 位")
    private String password;

    @Schema(description = "手机号", example = "13800000000")
    @NotBlank(message = "手机号不能为空")
    private String phone;

    @Schema(description = "图片验证码", example = "A3mK")
    @NotBlank(message = "验证码不能为空")
    private String captcha;

    @Schema(description = "图片验证码 key（由 /api/user/image-captcha 返回）", example = "a1b2c3d4e5f6g7h8")
    @NotBlank(message = "验证码 key 不能为空")
    private String captchaKey;
}
