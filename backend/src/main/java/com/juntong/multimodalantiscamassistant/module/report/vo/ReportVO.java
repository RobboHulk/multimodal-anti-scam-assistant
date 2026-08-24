package com.juntong.multimodalantiscamassistant.module.report.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;

/**
 * 取证安全报告响应模型
 */
@Data
@Schema(description = "取证安全报告响应模型（含 SM3 哈希防篡改字段）")
public class ReportVO {

    @Schema(description = "报告 ID")
    private Long id;

    @Schema(description = "统计开始日期")
    private LocalDate startDate;

    @Schema(description = "统计结束日期")
    private LocalDate endDate;

    @Schema(description = "报告生成时间")
    private LocalDateTime createdAt;

    @Schema(description = "检测期内总检测次数")
    private Integer totalDetections;

    @Schema(description = "高风险检测次数（riskScore >= 0.7）")
    private Integer highRiskCount;

    @Schema(description = "中风险检测次数（0.4 <= riskScore < 0.7）")
    private Integer midRiskCount;

    @Schema(description = "低风险检测次数（riskScore < 0.4）")
    private Integer lowRiskCount;

    @Schema(description = "攻击类型分布统计（Key: 类型, Value: 次数）")
    private Map<String, Integer> scamTypeStats;

    @Schema(description = "路由策略分布（FAST/EXPAND/DEEP/BLOCK 各自次数）")
    private Map<String, Integer> routeLevelStats;

    @Schema(description = "最常见攻击链标签 TOP5")
    private Map<String, Integer> topKillChainTags;

    @Schema(description = "AI 生成的风险趋势总结与防护建议")
    private String summary;

    @Schema(description = "报告内容 SM3 国密哈希摘要（64位十六进制），用于防篡改验证")
    private String contentHash;

    @Schema(description = "报告生成时间戳（Unix 毫秒），用于可信时间戳核验")
    private Long generatedTimestamp;
}
