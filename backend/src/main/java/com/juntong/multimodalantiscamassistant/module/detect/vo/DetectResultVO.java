package com.juntong.multimodalantiscamassistant.module.detect.vo;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * 单次检测结果模型
 */
@Data
@Schema(description = "单次风险检测结果模型")
public class DetectResultVO {

    @Schema(description = "检测记录唯一ID", example = "1001")
    private Long recordId;

    @Schema(description = "风险评估得分 (0~100)", example = "89.5")
    private Double riskScore;

    @Schema(description = "风险等级标识", example = "HIGH")
    private String riskLevel;

    @Schema(description = "判定的具体诈骗类型", example = "虚假投资理财诈骗")
    private String scamType;

    @Schema(description = "细分行为特征标签列表，是 scamType 的补充", example = "[\"safe_account\", \"fake_police_id\"]")
    private List<String> tags;

    @Schema(description = "算法置信度 (0~1)", example = "0.98")
    private Double confidence;

    @Schema(description = "系统建议采取的即时行动干预")
    private String riskAction;

    @Schema(description = "支持风险判定的核心证据片段列表")
    private List<String> evidence;

    @Schema(description = "本次检测结果的综合风险摘要")
    private String summary;

    @Schema(description = "检测触发时间")
    private LocalDateTime createdAt;
}
