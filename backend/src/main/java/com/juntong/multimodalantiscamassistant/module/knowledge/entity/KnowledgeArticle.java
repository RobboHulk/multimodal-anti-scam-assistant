package com.juntong.multimodalantiscamassistant.module.knowledge.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 威胁情报库文章实体
 * 在原知识库基础上增加结构化安全字段，支持 ATT&CK 标签和 IOC 指标
 */
@Data
@TableName("knowledge_article")
public class KnowledgeArticle {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 标题 */
    private String title;

    /** 攻击/诈骗类型，如 IMPERSONATE_POLICE_GOV */
    private String scamType;

    /** 正文内容（Markdown） */
    private String content;

    /** 标签，逗号分隔 */
    private String tags;

    /** 来源站点或作者 */
    private String source;

    /** 原文链接 */
    private String sourceUrl;

    /** 状态：1=已发布，0=草稿 */
    private Integer status;

    /**
     * MITRE ATT&CK 战术编号，逗号分隔
     * 如 "T1566,T1656" 对应钓鱼/身份冒充
     */
    private String attackTacticId;

    /**
     * ATT&CK 战术名称描述，逗号分隔
     * 如 "Phishing,Impersonation"
     */
    private String attackTacticName;

    /**
     * IOC 指标（Indicators of Compromise），JSON 数组
     * 每项含 type（domain/keyword/pattern）和 value
     * 如 [{"type":"keyword","value":"安全账户"},{"type":"pattern","value":".*验证码.*立刻.*"}]
     */
    private String iocPatterns;

    /**
     * 典型攻击话术时间线模板，JSON 数组
     * 描述该攻击手法的典型步骤顺序
     */
    private String attackTimeline;

    /**
     * 关联检测案例 ID，逗号分隔
     * 检测结论中 [REF-N] 引用来源之一
     */
    private String relatedCaseIds;

    /**
     * 威胁等级：1=低 2=中 3=高
     */
    private Integer threatLevel;

    private LocalDateTime createdAt;

    private LocalDateTime updatedAt;
}
