package com.juntong.multimodalantiscamassistant.module.detect.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 多模态安全检测记录实体
 * 存储每次检测的完整分析结果，包含 ML 链路各阶段输出
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("detection_record")
public class DetectionRecord {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 上传文件的访问 URL（可为空） */
    private String fileUrl;

    /** 原始文本内容（DLP脱敏后存储） */
    private String textContent;

    /** ML 风险分值 0.000~1.000 */
    private BigDecimal riskScore;

    /** 攻击/诈骗类型枚举，如 IMPERSONATE_POLICE_GOV */
    private String scamType;

    /** 细分行为标签，逗号分隔，如 "credential_theft,urgency_pressure" */
    private String tags;

    /** 判定证据节点 JSON 数组，含 [REF-N] 引用链 */
    private String evidence;

    /**
     * DepthGate 路由决策：FAST / EXPAND / DEEP / BLOCK
     * 对应设计文档中的风险约束路由四级链路
     */
    private String routeLevel;

    /**
     * DSCP 意图分解结果，JSON 数组
     * 每项含 intentType / sourceModal / snippet / confidence
     */
    private String intentUnits;

    /**
     * 攻击链标签 JSON 数组，如 ["authority_brand_claim","credential_theft_induction"]
     * 对应设计文档 killChainTags
     */
    private String killChainTags;

    /**
     * 可信决策引擎输出的信任分 0~1
     * 对应设计文档 trustScore
     */
    private BigDecimal trustScore;

    /**
     * 不确定性分数 0~1，值越高说明证据不足
     * 对应设计文档 uncertaintyScore
     */
    private BigDecimal uncertaintyScore;

    /**
     * Conformal Prediction 置信区间描述，JSON 对象
     * 含 lower/upper/coverageRate/predictionSet
     */
    private String conformalInterval;

    /**
     * 策略动作：PASS / WARN / ESCALATE / BLOCK / REVIEW
     * 对应设计文档可信决策引擎的最终 policyAction
     */
    private String policyAction;

    /**
     * DLP 脱敏摘要，JSON 对象
     * 含各类敏感字段被替换的数量统计
     */
    private String dlpSummary;

    /** ML 分析摘要（含 [REF-N] 引用标注的完整 Markdown 报告） */
    private String summary;

    /**
     * 取证报告 SM3 哈希摘要（32字节十六进制）
     * 用于报告防篡改验证
     */
    private String reportHash;

    /** 报告生成时间戳（Unix 毫秒，用于 TSA 可信时间戳） */
    private Long reportTimestamp;

    private LocalDateTime createdAt;
}
