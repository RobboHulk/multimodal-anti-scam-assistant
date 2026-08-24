package com.juntong.multimodalantiscamassistant.common.ml;

import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * ML 服务返回的风险预测结果
 * 包含完整的多模态分析链路输出：预处理 → 深伪检测 → 意图分解 → 路由 → 证据网络 → 可信决策
 */
@Data
public class MlPredictResult {

    // ─── 基础字段（原有） ───────────────────────────────────────

    /** 聊天类型：0=日常聊天短路，1=进入安全分析链路 */
    private Integer chatType;

    /** 风险分值 0~1 */
    private Double riskScore;

    /** 攻击/诈骗类型枚举，如 IMPERSONATE_POLICE_GOV */
    private String scamType;

    /** 模型置信度 0~1 */
    private Double confidence;

    /** DepthGate 路由决策：FAST / EXPAND / DEEP / BLOCK */
    private String riskAction;

    /** 行为特征细分标签列表 */
    private List<String> tags;

    /** 自然语言分析回复（Markdown，含 [REF-N] 证据引用） */
    private String chatResponse;

    /** 完整 Markdown 分析报告 */
    private String report;

    // ─── DLP 预处理层 ─────────────────────────────────────────

    /**
     * DLP 脱敏统计，Map 结构
     * key: 字段类型（phone/bankCard/url/money），value: 替换数量
     */
    private Map<String, Integer> dlpStats;

    // ─── 深伪检测层（设计文档 2.4.2）─────────────────────────

    /** 图像深伪风险分 r_i，0~1 */
    private Double deepfakeImageScore;

    /** 音频深伪风险分 r_a（Wav2Vec2-XLSR），0~1 */
    private Double deepfakeAudioScore;

    /** 视频深伪风险分 r_v，0~1 */
    private Double deepfakeVideoScore;

    /** 多模态融合深伪综合分 r_f，0~1 */
    private Double deepfakeFusionScore;

    // ─── DSCP 意图分解层（设计文档 2.4.3）────────────────────

    /**
     * 意图单元列表，每项含：
     * intentType（如 authority_brand_claim）
     * sourceModal（text/audio/image/video）
     * snippet（原文片段）
     * confidence（0~1）
     */
    private List<Map<String, Object>> intentUnits;

    /**
     * 攻击链标签，如 ["authority_brand_claim","credential_theft_induction","secrecy_request"]
     * 对应设计文档 killChainTags
     */
    private List<String> killChainTags;

    /** 意图识别整体置信度 0~1 */
    private Double intentConfidence;

    // ─── DepthGate 路由层（设计文档 2.4.3 RACER）─────────────

    /**
     * 路由决策结果：FAST / EXPAND / DEEP / BLOCK
     * 对应设计文档四级分析链路
     */
    private String routeLevel;

    /** 各路由链路耗时（毫秒），Map：routeLevel -> ms */
    private Map<String, Long> routeLatencyMs;

    // ─── 证据网络层（设计文档 2.4.4 AgenticRAG）──────────────

    /**
     * 证据节点列表，每项含：
     * refId（如 REF-1）、source（来源库）、title、snippet、nodeType
     */
    private List<Map<String, Object>> evidenceNodes;

    /**
     * 幻觉引用 ID 列表（已被替换为 [UNVERIFIED]）
     */
    private List<String> hallucinatedRefs;

    // ─── 可信决策层（设计文档 2.4.5）─────────────────────────

    /**
     * VeriCoT 推理链验证步骤列表，每项含：
     * step（步骤描述）、status（VALID/CONTRADICTION/UNGROUNDED）、evidence
     */
    private List<Map<String, Object>> veriCotSteps;

    /**
     * 事实级归因列表，每项绑定到具体模态/时间/证据节点
     */
    private List<Map<String, Object>> factLevelClaims;

    /** 可信决策引擎信任分 trustScore 0~1 */
    private Double trustScore;

    /** 不确定性分数 uncertaintyScore 0~1 */
    private Double uncertaintyScore;

    /**
     * Conformal Prediction 置信区间，含：
     * predictionSet（候选策略动作集合）、coverageRate、alpha
     */
    private Map<String, Object> conformalInterval;

    /**
     * 最终策略动作：PASS / WARN / ESCALATE / BLOCK / REVIEW
     * 对应设计文档 policyAction
     */
    private String policyAction;

    // ─── 便捷方法 ──────────────────────────────────────────────

    /** 根据 riskScore 推导 riskLevel */
    public String getRiskLevel() {
        if (riskScore == null) return "LOW";
        if (riskScore >= 0.9) return "CRITICAL";
        if (riskScore >= 0.7) return "HIGH";
        if (riskScore >= 0.4) return "MEDIUM";
        return "LOW";
    }

    /** 根据 riskLevel 映射严重度（1/2/3） */
    public int getSeverity() {
        return switch (getRiskLevel()) {
            case "CRITICAL", "HIGH" -> 3;
            case "MEDIUM" -> 2;
            default -> 1;
        };
    }
}
