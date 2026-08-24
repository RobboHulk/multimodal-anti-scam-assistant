package com.juntong.multimodalantiscamassistant.module.detect.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

/**
 * 批量测评结果总体模型
 */
@Data
@Schema(description = "批量自动化测评结果模型 (含 F1/准确率指标)")
public class BatchDetectResultVO {

    @Schema(description = "测评样本总数")
    private Integer totalCount;

    @Schema(description = "真正例 (正确识别为诈骗)")
    private Integer truePositive;

    @Schema(description = "假正例 (误报)")
    private Integer falsePositive;

    @Schema(description = "真负例 (正确识别为正常)")
    private Integer trueNegative;

    @Schema(description = "假负例 (漏报)")
    private Integer falseNegative;

    @Schema(description = "准确率 (Accuracy)")
    private Double accuracy;

    @Schema(description = "精确率 (Precision)")
    private Double precision;

    @Schema(description = "召回率 (Recall)")
    private Double recall;

    @Schema(description = "F1-score 综合评估指标")
    private Double f1Score;

    @Schema(description = "每一个测评项的明细检测结果列表")
    private List<DetectResultVO> detailResults;
}
