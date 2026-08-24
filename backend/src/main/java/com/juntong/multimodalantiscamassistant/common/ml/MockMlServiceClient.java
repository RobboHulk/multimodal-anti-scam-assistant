package com.juntong.multimodalantiscamassistant.common.ml;

import org.springframework.stereotype.Component;

import java.util.Random;

/**
 * ML 服务 Mock 实现，ML 团队接口就绪前使用
 * 标注 @Primary 保证优先注入此实现
 * 替换时：删除此类，添加 RealMlServiceClient 即可
 */
@Component
public class MockMlServiceClient implements MlServiceClient {

        private static final String[] SCAM_TYPES = {
                        "IMPERSONATE_POLICE_GOV",
                        "INVESTMENT_SCAM",
                        "LOAN_SCAM",
                        "FAMILY_EMERGENCY",
                        "PHISHING_LINK_QRCODE"
        };

        private final Random random = new Random();

        @Override
        public MlPredictResult predict(MlPredictRequest request) {
                // 简单模拟：包含特定关键词则返回高风险
                String text = request.getText() != null ? request.getText() : "";
                boolean highRisk = text.contains("安全账户") || text.contains("公安") ||
                                text.contains("转账") || text.contains("贷款") ||
                                text.contains("中奖");

                MlPredictResult result = new MlPredictResult();
                result.setChatType(highRisk ? 1 : 0);
                result.setRiskScore(highRisk ? 0.85 + random.nextDouble() * 0.14 : 0.05 + random.nextDouble() * 0.20);
                result.setScamType(highRisk ? SCAM_TYPES[random.nextInt(SCAM_TYPES.length)] : "OTHER_UNKNOWN");
                result.setConfidence(highRisk ? 0.88 + random.nextDouble() * 0.10 : 0.30 + random.nextDouble() * 0.30);
                result.setRiskAction(highRisk ? "WARN" : "EDUCATE");
                result.setTags(highRisk ? java.util.List.of("high_risk_phrase", "manual_verify") : java.util.List.of());
                result.setReport(highRisk
                                ? "# 安全监测报告\n\n## 1. 风险结论\n- 风险分数：0.92\n- 诈骗类型：高风险诈骗话术\n- 处置建议：WARN\n\n## 4. 防御建议\n1. 停止转账并核验身份。"
                                : "");
                result.setChatResponse(highRisk
                                ? "检测到疑似诈骗内容，建议谨慎操作，不要轻易转账或提供个人信息。"
                                : "当前内容风险较低，请继续保持警惕。");

                return result;
        }

        @Override
        public void triggerVectorize(String filePath) {
                // Mock 实现：仅记录日志
                System.out.println("[Mock ML Service] Triggered vectorization for file: " + filePath);
        }
}
