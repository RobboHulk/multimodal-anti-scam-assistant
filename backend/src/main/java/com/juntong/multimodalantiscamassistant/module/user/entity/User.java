package com.juntong.multimodalantiscamassistant.module.user.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 用户实体，对应 user 表
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("user")
public class User {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String username;

    /** 查询时不返回密码字段 */
    @TableField(select = false)
    private String password;

    private String phone;

    /** 头像路径 */
    private String avatar;

    /** 年龄段: 1=儿童 2=青壮年 3=老年 */
    private Integer ageGroup;

    /** 性别: 1=男 2=女 */
    private Integer gender;

    private String occupation;

    /** 风险灵敏度: 1=低 2=中 3=高 */
    private Integer riskPreference;

    /** 触发预警的风险分阈值 (0.0~1.0，与 ML 返回 riskScore 同口径，默认 0.700) */
    private BigDecimal riskThreshold;

    /** 干预策略: 1=弹窗提醒 2=语音阻断 3=自动联系监护人 */
    private Integer interventionStrategy;

    @TableLogic
    private Integer deleted;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;
}
