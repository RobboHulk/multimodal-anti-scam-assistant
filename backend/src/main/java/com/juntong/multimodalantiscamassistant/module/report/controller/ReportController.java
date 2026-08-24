package com.juntong.multimodalantiscamassistant.module.report.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import com.juntong.multimodalantiscamassistant.module.report.dto.GenerateReportDTO;
import com.juntong.multimodalantiscamassistant.module.report.service.ReportService;
import com.juntong.multimodalantiscamassistant.module.report.vo.ReportVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "7. 取证安全报告", description = "生成基于检测记录统计的取证报告，报告内容经 SM3 国密哈希签名，支持防篡改验证")
@RestController
@RequestMapping("/api/report")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    @Operation(
        summary = "生成取证安全报告",
        description = "指定时间范围，系统扫描该期间所有检测记录，生成含攻击类型分布、" +
            "路由策略统计、killChain 标签 TOP5 和风险趋势总结的取证报告。" +
            "报告内容使用 SM3 国密算法签名，哈希存档用于防篡改验证。"
    )
    @PostMapping("/generate")
    public Result<ReportVO> generate(@RequestBody @Validated GenerateReportDTO dto) {
        return Result.ok(reportService.generate(currentId(), dto));
    }

    @Operation(summary = "获取历史报告列表", description = "获取当前用户生成过的所有报告摘要（含 SM3 哈希，可用于验证）")
    @GetMapping("/list")
    public Result<List<ReportVO>> list() {
        return Result.ok(reportService.listReports(currentId()));
    }

    private Long currentId() {
        return (Long) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }
}
