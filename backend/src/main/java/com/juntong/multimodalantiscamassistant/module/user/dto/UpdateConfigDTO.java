package com.juntong.multimodalantiscamassistant.module.user.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.*;
import lombok.Data;

import java.math.BigDecimal;

/**
 * 更新风险配置请求体
 */
@Data
@Schema(description = "风险配置更新模型")
public class UpdateConfigDTO {

    @Schema(description = "风险灵敏度: 1=低 2=中 3=高", example = "2")
    @Min(value = 1, message = "风险灵敏度取值范围: 1~3")
    @Max(value = 3, message = "风险灵敏度取值范围: 1~3")
    private Integer riskPreference;

    @Schema(description = "风险分阈值 (0~100)，超过此分值触发预警", example = "75.50")
    @DecimalMin(value = "0.00", message = "风险阈值最小为 0")
    @DecimalMax(value = "100.00", message = "风险阈值最大为 100")
    private BigDecimal riskThreshold;

    @Schema(description = "干预策略: 1=弹窗提醒 2=语音阻断 3=自动联系监护人", example = "1")
    @Min(value = 1, message = "干预策略取值范围: 1~3")
    @Max(value = 3, message = "干预策略取值范围: 1~3")
    private Integer interventionStrategy;

    @Schema(description = "通知策略", example = "IMMEDIATE")
    private String notifyPolicy;
}
