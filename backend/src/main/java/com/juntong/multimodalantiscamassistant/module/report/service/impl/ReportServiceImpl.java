package com.juntong.multimodalantiscamassistant.module.report.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.juntong.multimodalantiscamassistant.module.detect.entity.DetectionRecord;
import com.juntong.multimodalantiscamassistant.module.detect.mapper.DetectionRecordMapper;
import com.juntong.multimodalantiscamassistant.module.report.dto.GenerateReportDTO;
import com.juntong.multimodalantiscamassistant.module.report.entity.Report;
import com.juntong.multimodalantiscamassistant.module.report.mapper.ReportMapper;
import com.juntong.multimodalantiscamassistant.module.report.service.ReportService;
import com.juntong.multimodalantiscamassistant.module.report.vo.ReportVO;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 取证安全报告服务
 * 基于 detection_record 统计生成，不再依赖已删除的 alert 模块
 * 报告内容使用 SM3 国密哈希摘要，实现防篡改验证
 */
@Service
@RequiredArgsConstructor
public class ReportServiceImpl extends ServiceImpl<ReportMapper, Report> implements ReportService {

    private final DetectionRecordMapper detectionRecordMapper;
    private final ObjectMapper objectMapper;

    @Override
    @SneakyThrows
    public ReportVO generate(Long userId, GenerateReportDTO dto) {
        LocalDate start = dto.getStartDate();
        LocalDate end = dto.getEndDate();

        // 查询时间段内的检测记录
        List<DetectionRecord> records = detectionRecordMapper.selectList(
                new LambdaQueryWrapper<DetectionRecord>()
                        .eq(DetectionRecord::getUserId, userId)
                        .ge(DetectionRecord::getCreatedAt, LocalDateTime.of(start, LocalTime.MIN))
                        .le(DetectionRecord::getCreatedAt, LocalDateTime.of(end, LocalTime.MAX)));

        // 按 riskScore 分级统计
        int high = (int) records.stream().filter(r -> score(r) >= 0.7).count();
        int mid  = (int) records.stream().filter(r -> score(r) >= 0.4 && score(r) < 0.7).count();
        int low  = (int) records.stream().filter(r -> score(r) < 0.4).count();

        // 攻击类型分布
        Map<String, Integer> scamTypeStats = new HashMap<>();
        records.forEach(r -> {
            String type = StringUtils.hasText(r.getScamType()) ? r.getScamType() : "OTHER_UNKNOWN";
            scamTypeStats.merge(type, 1, Integer::sum);
        });

        // 路由策略分布
        Map<String, Integer> routeLevelStats = new HashMap<>();
        records.forEach(r -> {
            String route = StringUtils.hasText(r.getRouteLevel()) ? r.getRouteLevel() : "UNKNOWN";
            routeLevelStats.merge(route, 1, Integer::sum);
        });

        // killChain 标签 TOP 统计
        Map<String, Integer> killChainStats = new HashMap<>();
        records.forEach(r -> {
            if (StringUtils.hasText(r.getKillChainTags())) {
                for (String tag : r.getKillChainTags().split(",")) {
                    if (!tag.isBlank()) killChainStats.merge(tag.trim(), 1, Integer::sum);
                }
            }
        });
        // 取 TOP5
        Map<String, Integer> topKillChainTags = killChainStats.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(5)
                .collect(java.util.stream.Collectors.toMap(
                        Map.Entry::getKey, Map.Entry::getValue,
                        (a, b) -> a, java.util.LinkedHashMap::new));

        String summary = buildSummary(start, end, records.size(), high, scamTypeStats);

        // 序列化报告内容
        Map<String, Object> contentMap = new HashMap<>();
        contentMap.put("totalDetections", records.size());
        contentMap.put("highRiskCount", high);
        contentMap.put("midRiskCount", mid);
        contentMap.put("lowRiskCount", low);
        contentMap.put("scamTypeStats", scamTypeStats);
        contentMap.put("routeLevelStats", routeLevelStats);
        contentMap.put("topKillChainTags", topKillChainTags);
        contentMap.put("summary", summary);
        String contentJson = objectMapper.writeValueAsString(contentMap);

        // 计算 SM3 哈希
        String contentHash = computeSm3Hex(contentJson);
        long generatedTimestamp = System.currentTimeMillis();

        Report report = Report.builder()
                .userId(userId)
                .startDate(start)
                .endDate(end)
                .content(contentJson)
                .contentHash(contentHash)
                .generatedTimestamp(generatedTimestamp)
                .createdAt(LocalDateTime.now())
                .build();
        save(report);

        return toVO(report, records.size(), high, mid, low, scamTypeStats, routeLevelStats, topKillChainTags, summary, contentHash, generatedTimestamp);
    }

    @Override
    @SneakyThrows
    public List<ReportVO> listReports(Long userId) {
        return lambdaQuery()
                .eq(Report::getUserId, userId)
                .orderByDesc(Report::getCreatedAt)
                .list()
                .stream()
                .map(r -> {
                    ReportVO vo = new ReportVO();
                    vo.setId(r.getId());
                    vo.setStartDate(r.getStartDate());
                    vo.setEndDate(r.getEndDate());
                    vo.setCreatedAt(r.getCreatedAt());
                    vo.setContentHash(r.getContentHash());
                    vo.setGeneratedTimestamp(r.getGeneratedTimestamp());
                    try {
                        Map<String, Object> map = objectMapper.readValue(r.getContent(),
                                new TypeReference<Map<String, Object>>() {});
                        vo.setTotalDetections((Integer) map.get("totalDetections"));
                        vo.setSummary((String) map.get("summary"));
                    } catch (Exception ignored) {}
                    return vo;
                }).toList();
    }

    // ──────────────────── 私有辅助 ────────────────────────────

    private double score(DetectionRecord r) {
        return r.getRiskScore() != null ? r.getRiskScore().doubleValue() : 0.0;
    }

    private ReportVO toVO(Report r, int total, int high, int mid, int low,
            Map<String, Integer> scamStats, Map<String, Integer> routeStats,
            Map<String, Integer> topTags, String summary, String hash, long ts) {
        ReportVO vo = new ReportVO();
        vo.setId(r.getId());
        vo.setStartDate(r.getStartDate());
        vo.setEndDate(r.getEndDate());
        vo.setCreatedAt(r.getCreatedAt());
        vo.setTotalDetections(total);
        vo.setHighRiskCount(high);
        vo.setMidRiskCount(mid);
        vo.setLowRiskCount(low);
        vo.setScamTypeStats(scamStats);
        vo.setRouteLevelStats(routeStats);
        vo.setTopKillChainTags(topTags);
        vo.setSummary(summary);
        vo.setContentHash(hash);
        vo.setGeneratedTimestamp(ts);
        return vo;
    }

    private String buildSummary(LocalDate start, LocalDate end, int total, int high, Map<String, Integer> scamStats) {
        if (total == 0) {
            return String.format("%s 至 %s 期间未检测到任何安全威胁，请继续保持安全习惯。", start, end);
        }
        String topType = scamStats.entrySet().stream()
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey).orElse("未知类型");
        return String.format(
                "%s 至 %s 期间共执行 %d 次安全检测，其中高风险 %d 次。" +
                "最主要的攻击类型为【%s】，请重点防范。本报告经 SM3 国密算法签名，哈希已存档备查。",
                start, end, total, high, topType);
    }

    /** SM3 国密哈希（纯 Java 实现，与 ChatServiceImpl 保持一致） */
    private String computeSm3Hex(String content) {
        if (content == null || content.isEmpty()) return "";
        try {
            byte[] data = content.getBytes(StandardCharsets.UTF_8);
            byte[] hash = sm3(data);
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b & 0xff));
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }

    private static final int[] T_ARR = new int[64];
    static {
        for (int i = 0; i < 16; i++) T_ARR[i] = 0x79cc4519;
        for (int i = 16; i < 64; i++) T_ARR[i] = 0x7a879d8a;
    }

    private byte[] sm3(byte[] msg) {
        int len = msg.length, bitLen = len * 8;
        int padLen = (len % 64 < 56) ? (56 - len % 64) : (120 - len % 64);
        byte[] padded = new byte[len + padLen + 8];
        System.arraycopy(msg, 0, padded, 0, len);
        padded[len] = (byte) 0x80;
        for (int i = 0; i < 8; i++) padded[padded.length - 1 - i] = (byte) ((long) bitLen >> (i * 8));
        int[] v = {0x7380166f, 0x4914b2b9, 0x172442d7, (int) 0xda8a0600,
                   (int) 0xa96f30bc, 0x163138aa, (int) 0xe38dee4d, (int) 0xb0fb0e4e};
        for (int i = 0; i < padded.length / 64; i++) {
            int[] w = new int[68], w1 = new int[64];
            for (int j = 0; j < 16; j++)
                w[j] = ((padded[i*64+j*4]&0xff)<<24)|((padded[i*64+j*4+1]&0xff)<<16)
                      |((padded[i*64+j*4+2]&0xff)<<8)|(padded[i*64+j*4+3]&0xff);
            for (int j = 16; j < 68; j++)
                w[j] = p1(w[j-16]^w[j-9]^rol(w[j-3],15))^rol(w[j-13],7)^w[j-6];
            for (int j = 0; j < 64; j++) w1[j] = w[j]^w[j+4];
            int a=v[0],b=v[1],c=v[2],d=v[3],e=v[4],f=v[5],g=v[6],h=v[7];
            for (int j = 0; j < 64; j++) {
                int ss1=rol(rol(a,12)+e+rol(T_ARR[j],j%32),7), ss2=ss1^rol(a,12);
                int tt1=ff(a,b,c,j)+d+ss2+w1[j], tt2=gg(e,f,g,j)+h+ss1+w[j];
                d=c; c=rol(b,9); b=a; a=tt1; h=g; g=rol(f,19); f=e; e=p0(tt2);
            }
            v[0]^=a; v[1]^=b; v[2]^=c; v[3]^=d; v[4]^=e; v[5]^=f; v[6]^=g; v[7]^=h;
        }
        byte[] result = new byte[32];
        for (int i = 0; i < 8; i++) {
            result[i*4]=(byte)(v[i]>>>24); result[i*4+1]=(byte)(v[i]>>>16);
            result[i*4+2]=(byte)(v[i]>>>8); result[i*4+3]=(byte)v[i];
        }
        return result;
    }

    private int rol(int x, int n) { return (x<<n)|(x>>>(32-n)); }
    private int ff(int x, int y, int z, int j) { return j<16 ? x^y^z : (x&y)|(x&z)|(y&z); }
    private int gg(int x, int y, int z, int j) { return j<16 ? x^y^z : (x&y)|(~x&z); }
    private int p0(int x) { return x^rol(x,9)^rol(x,17); }
    private int p1(int x) { return x^rol(x,15)^rol(x,23); }
}
