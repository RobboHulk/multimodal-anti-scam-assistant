package com.juntong.multimodalantiscamassistant.module.chat.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 安全检测响应 VO
 * 包含多模态分析链路各阶段完整输出，供前端可视化展示
 */
@Data
@Schema(description = "多模态安全检测完整响应（含 DLP/深伪/意图/路由/证据/可信决策各层结果）")
public class ChatResponseVO {

    // ─── 基础字段 ───────────────────────────────────────────────

    @Schema(description = "0=日常聊天短路，1=进入安全分析链路", example = "1")
    private Integer chatType;

    @Schema(description = "AI 自然语言分析回复（含 [REF-N] 引用标注）")
    private String chatResponse;

    @Schema(description = "完整 Markdown 分析报告")
    private String report;

    @Schema(description = "风险分值 0~1", example = "0.85")
    private Double riskScore;

    @Schema(description = "风险等级：LOW / MEDIUM / HIGH / CRITICAL", example = "HIGH")
    private String riskLevel;

    @Schema(description = "攻击/诈骗类型枚举", example = "IMPERSONATE_POLICE_GOV")
    private String scamType;

    @Schema(description = "细分行为特征标签列表")
    private List<String> tags;

    @Schema(description = "模型置信度 0~1", example = "0.94")
    private Double confidence;

    @Schema(description = "DepthGate 路由级别：FAST/EXPAND/DEEP/BLOCK")
    private String riskAction;

    // ─── DLP 预处理层 ───────────────────────────────────────────

    @Schema(description = "DLP 脱敏统计：各类敏感字段替换数量")
    private Map<String, Integer> dlpStats;

    // ─── 深伪检测层 ─────────────────────────────────────────────

    @Schema(description = "图像深伪风险分 r_i（0~1）")
    private Double deepfakeImageScore;

    @Schema(description = "音频深伪风险分 r_a，Wav2Vec2-XLSR（0~1）")
    private Double deepfakeAudioScore;

    @Schema(description = "视频深伪风险分 r_v（0~1）")
    private Double deepfakeVideoScore;

    @Schema(description = "多模态融合深伪综合分 r_f（0~1）")
    private Double deepfakeFusionScore;

    // ─── DSCP 意图分解层 ────────────────────────────────────────

    @Schema(description = "意图单元列表（intentType/sourceModal/snippet/confidence）")
    private List<Map<String, Object>> intentUnits;

    @Schema(description = "攻击链标签 killChainTags")
    private List<String> killChainTags;

    @Schema(description = "意图识别整体置信度 0~1")
    private Double intentConfidence;

    // ─── DepthGate 路由层 ────────────────────────────────────────

    @Schema(description = "路由决策：FAST / EXPAND / DEEP / BLOCK")
    private String routeLevel;

    @Schema(description = "各路由链路耗时（毫秒）")
    private Map<String, Long> routeLatencyMs;

    // ─── 证据网络层 ─────────────────────────────────────────────

    @Schema(description = "证据节点列表（refId/source/title/snippet/nodeType）")
    private List<Map<String, Object>> evidenceNodes;

    @Schema(description = "已过滤的幻觉引用 ID 列表（替换为 [UNVERIFIED]）")
    private List<String> hallucinatedRefs;

    // ─── 可信决策层 ─────────────────────────────────────────────

    @Schema(description = "VeriCoT 推理链验证步骤（step/status/evidence）")
    private List<Map<String, Object>> veriCotSteps;

    @Schema(description = "信任分 trustScore 0~1")
    private Double trustScore;

    @Schema(description = "不确定性分数 uncertaintyScore 0~1")
    private Double uncertaintyScore;

    @Schema(description = "Conformal Prediction 置信区间（predictionSet/coverageRate/alpha）")
    private Map<String, Object> conformalInterval;

    @Schema(description = "最终策略动作：PASS / WARN / ESCALATE / BLOCK / REVIEW")
    private String policyAction;
}
