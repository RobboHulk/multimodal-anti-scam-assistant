package com.juntong.multimodalantiscamassistant.module.chat.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Schema(description = "用户画像载荷")
public class UserProfilePayload {

    @Schema(description = "用户ID", example = "1001")
    private Long id;

    @Schema(description = "用户名", example = "alice")
    private String username;

    @Schema(description = "年龄段", example = "2")
    private Integer ageGroup;

    @Schema(description = "性别", example = "2")
    private Integer gender;

    @Schema(description = "职业", example = "student")
    private String occupation;

    @Schema(description = "风险偏好", example = "1")
    private Integer riskPreference;

    @Schema(description = "风险阈值", example = "0.7")
    private BigDecimal riskThreshold;

    @Schema(description = "干预策略", example = "1")
    private Integer interventionStrategy;
}
