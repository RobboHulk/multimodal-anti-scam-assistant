package com.juntong.multimodalantiscamassistant.module.detect.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.juntong.multimodalantiscamassistant.common.Result;
import com.juntong.multimodalantiscamassistant.module.detect.entity.DetectionRecord;
import com.juntong.multimodalantiscamassistant.module.detect.mapper.DetectionRecordMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.HashMap;
import java.util.Map;

/**
 * 取证报告公开验证接口
 * 无需登录，任何人可通过报告 ID + SM3 哈希验证报告完整性
 * 对应设计文档"商用密码应用"与"可信时间戳"方向
 */
@Tag(name = "8. 取证报告验证", description = "公开的报告防篡改验证接口，基于 SM3 国密哈希算法")
@RestController
@RequestMapping("/api/verify")
@RequiredArgsConstructor
public class ReportVerifyController {

    private final DetectionRecordMapper detectionRecordMapper;

    @Operation(
        summary = "验证取证报告完整性",
        description = "输入检测记录 ID 和待验证的 SM3 哈希值，" +
            "系统比对数据库中存储的原始哈希，判断报告是否被篡改。" +
            "同时返回报告生成时间戳，可用于可信时间戳（TSA）核验。"
    )
    @GetMapping("/report/{id}")
    public Result<Map<String, Object>> verifyReport(
            @PathVariable Long id,
            @RequestParam String hash) {

        DetectionRecord record = detectionRecordMapper.selectOne(
                new LambdaQueryWrapper<DetectionRecord>()
                        .eq(DetectionRecord::getId, id)
                        .select(DetectionRecord::getId,
                                DetectionRecord::getReportHash,
                                DetectionRecord::getReportTimestamp,
                                DetectionRecord::getScamType,
                                DetectionRecord::getRiskScore,
                                DetectionRecord::getCreatedAt));

        Map<String, Object> result = new HashMap<>();

        if (record == null) {
            result.put("valid", false);
            result.put("reason", "报告不存在");
            return Result.ok(result);
        }

        boolean hashMatch = hash != null && hash.equalsIgnoreCase(record.getReportHash());
        result.put("valid", hashMatch);
        result.put("reportId", id);
        result.put("algorithm", "SM3");
        result.put("storedHash", record.getReportHash());
        result.put("providedHash", hash);
        result.put("scamType", record.getScamType());
        result.put("riskScore", record.getRiskScore());

        if (record.getReportTimestamp() != null) {
            LocalDateTime ts = LocalDateTime.ofInstant(
                    Instant.ofEpochMilli(record.getReportTimestamp()),
                    ZoneId.of("Asia/Shanghai"));
            result.put("reportGeneratedAt", ts.toString());
            result.put("reportTimestampMs", record.getReportTimestamp());
        }

        if (record.getCreatedAt() != null) {
            result.put("detectionTime", record.getCreatedAt().toString());
        }

        result.put("reason", hashMatch ? "报告完整，未经篡改" : "哈希不匹配，报告可能已被篡改");
        return Result.ok(result);
    }

    @Operation(
        summary = "通过 SM3 哈希查询报告",
        description = "直接用 SM3 哈希值查询对应的检测记录，无需提供 ID"
    )
    @GetMapping("/report/by-hash")
    public Result<Map<String, Object>> findByHash(@RequestParam String hash) {
        DetectionRecord record = detectionRecordMapper.selectOne(
                new LambdaQueryWrapper<DetectionRecord>()
                        .eq(DetectionRecord::getReportHash, hash.toLowerCase())
                        .select(DetectionRecord::getId,
                                DetectionRecord::getReportHash,
                                DetectionRecord::getReportTimestamp,
                                DetectionRecord::getScamType,
                                DetectionRecord::getPolicyAction,
                                DetectionRecord::getCreatedAt));

        Map<String, Object> result = new HashMap<>();
        if (record == null) {
            result.put("found", false);
            result.put("reason", "未找到对应哈希的报告");
            return Result.ok(result);
        }
        result.put("found", true);
        result.put("reportId", record.getId());
        result.put("algorithm", "SM3");
        result.put("hash", record.getReportHash());
        result.put("scamType", record.getScamType());
        result.put("policyAction", record.getPolicyAction());
        result.put("detectionTime", record.getCreatedAt() != null ? record.getCreatedAt().toString() : null);
        return Result.ok(result);
    }
}
