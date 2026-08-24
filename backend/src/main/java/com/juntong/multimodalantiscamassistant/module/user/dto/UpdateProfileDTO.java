package com.juntong.multimodalantiscamassistant.module.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 更新用户角色画像请求体
 */
@Data
@Schema(description = "个人角色画像更新模型")
public class UpdateProfileDTO {

    @Schema(description = "年龄段: 1=儿童 2=青壮年 3=老年", example = "2")
    @Min(value = 1, message = "年龄段取值范围: 1~3")
    @Max(value = 3, message = "年龄段取值范围: 1~3")
    private Integer ageGroup;

    @Schema(description = "性别: 1=男 2=女", example = "1")
    @Min(value = 1, message = "性别取值范围: 1~2")
    @Max(value = 2, message = "性别取值范围: 1~2")
    private Integer gender;

    @Schema(description = "职业", example = "财务人员")
    private String occupation;

    @Schema(description = "手机号", example = "13800138000")
    private String phone;

    @Schema(description = "风险分阈值 (0~100)", example = "75.50")
    private BigDecimal riskThreshold;
}
