package com.juntong.multimodalantiscamassistant.module.user.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 用户信息响应体（个人安全档案）
 */
@Data
@Schema(description = "用户安全档案响应模型")
public class UserVO {

    @Schema(description = "用户ID")
    private Long id;

    @Schema(description = "用户名")
    private String username;

    @Schema(description = "手机号")
    private String phone;

    @Schema(description = "头像路径")
    private String avatar;

    @Schema(description = "年龄段: 1=儿童 2=青壮年 3=老年")
    private Integer ageGroup;

    @Schema(description = "性别: 1=男 2=女")
    private Integer gender;

    @Schema(description = "职业", example = "财务人员")
    private String occupation;

    @Schema(description = "风险灵敏度: 1=低 2=中 3=高")
    private Integer riskPreference;

    @Schema(description = "风险分阈值 (0.0~1.0)", example = "0.700")
    private BigDecimal riskThreshold;

    @Schema(description = "干预策略: 1=弹窗提醒 2=语音播报 3=强制阻断")
    private Integer interventionStrategy;

    @Schema(description = "账号创建时间")
    private LocalDateTime createdAt;
}
