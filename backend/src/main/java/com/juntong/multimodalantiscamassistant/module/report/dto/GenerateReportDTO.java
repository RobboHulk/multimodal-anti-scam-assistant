package com.juntong.multimodalantiscamassistant.module.report.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

/**
 * 生成报告请求模型
 */
@Data
@Schema(description = "安全报告生成请求模型")
public class GenerateReportDTO {

    @Schema(description = "统计开始日期", example = "2024-03-01")
    @NotNull(message = "开始日期不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate startDate;

    @Schema(description = "统计结束日期", example = "2024-03-07")
    @NotNull(message = "结束日期不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate endDate;
}
