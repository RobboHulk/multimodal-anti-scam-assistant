package com.juntong.multimodalantiscamassistant.module.report.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 取证安全报告实体
 * 基于 detection_record 统计生成，内含 SM3 哈希用于防篡改验证
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("report")
public class Report {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;
    private LocalDate startDate;
    private LocalDate endDate;

    /** 报告统计数据（JSON） */
    private String content;

    /**
     * 报告内容 SM3 国密哈希摘要（64位十六进制）
     * 用于防篡改验证，对应设计文档"商用密码应用"方向
     */
    private String contentHash;

    /**
     * 报告生成时间戳（Unix 毫秒）
     * 用于可信时间戳（TSA）核验
     */
    private Long generatedTimestamp;

    private LocalDateTime createdAt;
}
