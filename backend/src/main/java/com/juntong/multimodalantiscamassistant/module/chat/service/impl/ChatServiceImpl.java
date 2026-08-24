package com.juntong.multimodalantiscamassistant.module.chat.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.juntong.multimodalantiscamassistant.common.exception.BusinessException;
import com.juntong.multimodalantiscamassistant.common.ml.MlPredictRequest;
import com.juntong.multimodalantiscamassistant.common.ml.MlPredictResult;
import com.juntong.multimodalantiscamassistant.common.ml.MlServiceClient;
import com.juntong.multimodalantiscamassistant.module.chat.dto.SendMessageDTO;
import com.juntong.multimodalantiscamassistant.module.chat.entity.ChatMessage;
import com.juntong.multimodalantiscamassistant.module.chat.mapper.ChatMessageMapper;
import com.juntong.multimodalantiscamassistant.module.chat.vo.ChatMessageVO;
import com.juntong.multimodalantiscamassistant.module.chat.vo.ChatResponseVO;
import com.juntong.multimodalantiscamassistant.module.chat.vo.SessionVO;
import com.juntong.multimodalantiscamassistant.module.detect.entity.DetectionRecord;
import com.juntong.multimodalantiscamassistant.module.detect.mapper.DetectionRecordMapper;
import com.juntong.multimodalantiscamassistant.module.user.entity.User;
import com.juntong.multimodalantiscamassistant.module.user.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * 安全检测服务实现
 * 统一处理多模态安全检测请求，完整存储 ML 链路各阶段输出结果
 */
@Service
@RequiredArgsConstructor
public class ChatServiceImpl extends ServiceImpl<ChatMessageMapper, ChatMessage> {

    private final MlServiceClient mlServiceClient;
    private final UserMapper userMapper;
    private final DetectionRecordMapper detectionRecordMapper;
    private final ObjectMapper objectMapper;

    private static final Pattern URL_PATTERN = Pattern.compile("(?i)(http|https)://.*");

    /**
     * 统一安全检测入口：多模态输入 → ML 分析链路 → 存储完整结果
     */
    @SneakyThrows
    public ChatResponseVO send(Long userId, SendMessageDTO dto) {
        // 1. 参数清洗
        String content = dto.getText() == null ? ""
                : new String(dto.getText().trim().getBytes(StandardCharsets.UTF_8), StandardCharsets.UTF_8);
        String imagePath = normalizePath(dto.getImage_path());
        String audioPath = normalizePath(dto.getAudio_path());
        String videoPath = normalizePath(dto.getVideo_path());

        if (!StringUtils.hasText(content) && !StringUtils.hasText(imagePath)
                && !StringUtils.hasText(audioPath) && !StringUtils.hasText(videoPath)) {
            throw new BusinessException(400, "消息内容或多模态附件不能为空");
        }

        // 2. 加载用户信息，构建 userProfile
        User user = userMapper.selectById(userId);
        if (user == null) throw new BusinessException(404, "用户不存在");

        Map<String, Object> userProfile = buildUserProfile(user, dto);

        // 3. 调用 ML 服务
        MlPredictRequest request = MlPredictRequest.builder()
                .text(content)
                .session_id(StringUtils.hasText(dto.getSession_id()) ? dto.getSession_id() : "default")
                .userProfile(userProfile)
                .image_path(StringUtils.hasText(imagePath) ? imagePath : null)
                .audio_path(StringUtils.hasText(audioPath) ? audioPath : null)
                .video_path(StringUtils.hasText(videoPath) ? videoPath : null)
                .build();

        MlPredictResult result = mlServiceClient.predict(request);

        // 4. 存储用户消息
        String sessionId = dto.getSession_id();
        saveMessage(userId, sessionId, "user", content, firstNonBlank(imagePath, audioPath, videoPath));

        // 5. 只要进入安全分析链路就存储检测记录
        int chatType = result.getChatType() != null ? result.getChatType() : 0;
        if (chatType >= 1) {
            saveDetectionRecord(userId, result, dto, content);
        }

        // 6. 存储 AI 回复消息
        String chatReply = StringUtils.hasText(result.getChatResponse()) ? result.getChatResponse() : buildFallbackReply(result);
        saveMessage(userId, sessionId, "assistant", chatReply, null);

        // 7. 构造完整响应 VO
        return buildResponseVO(result, chatType, chatReply);
    }

    /** 获取检测历史消息 */
    public List<ChatMessageVO> history(Long userId, String sessionId) {
        var query = lambdaQuery().eq(ChatMessage::getUserId, userId);
        if (StringUtils.hasText(sessionId)) {
            query.eq(ChatMessage::getSessionId, sessionId);
        }
        return query.orderByAsc(ChatMessage::getCreatedAt)
                .list()
                .stream()
                .map(m -> {
                    ChatMessageVO vo = new ChatMessageVO();
                    BeanUtils.copyProperties(m, vo);
                    return vo;
                }).toList();
    }

    /** 获取会话列表 */
    public List<SessionVO> sessions(Long userId) {
        List<ChatMessage> allMessages = lambdaQuery()
                .eq(ChatMessage::getUserId, userId)
                .isNotNull(ChatMessage::getSessionId)
                .orderByAsc(ChatMessage::getCreatedAt)
                .list();

        Map<String, SessionVO> sessionMap = new java.util.LinkedHashMap<>();
        for (ChatMessage msg : allMessages) {
            String sid = msg.getSessionId();
            if (sid == null || sid.isBlank()) continue;
            SessionVO vo = sessionMap.computeIfAbsent(sid, k -> {
                SessionVO s = new SessionVO();
                s.setSessionId(k);
                s.setMsgCount(0);
                return s;
            });
            vo.setMsgCount(vo.getMsgCount() + 1);
            vo.setLastTime(msg.getCreatedAt());
            if (vo.getTitle() == null && "user".equals(msg.getRole())) {
                String title = msg.getContent();
                if (title != null && title.length() > 20) title = title.substring(0, 20) + "...";
                vo.setTitle(title);
            }
        }
        List<SessionVO> result = new java.util.ArrayList<>(sessionMap.values());
        result.sort((a, b) -> b.getLastTime().compareTo(a.getLastTime()));
        return result;
    }

    /** 删除会话 */
    public void deleteSession(Long userId, String sessionId) {
        lambdaUpdate()
                .eq(ChatMessage::getUserId, userId)
                .eq(ChatMessage::getSessionId, sessionId)
                .remove();
    }

    // ──────────────────── 私有辅助方法 ────────────────────────

    private Map<String, Object> buildUserProfile(User user, SendMessageDTO dto) {
        Map<String, Object> profile = new HashMap<>();
        profile.put("id", user.getId());
        profile.put("username", user.getUsername() != null ? user.getUsername() : "");
        profile.put("ageGroup", user.getAgeGroup() != null ? user.getAgeGroup() : 2);
        profile.put("gender", user.getGender() != null ? user.getGender() : 0);
        profile.put("occupation", user.getOccupation() != null ? user.getOccupation() : "");
        profile.put("riskPreference", user.getRiskPreference() != null ? user.getRiskPreference() : 2);
        profile.put("riskThreshold", user.getRiskThreshold() != null ? user.getRiskThreshold().doubleValue() : 0.7);
        profile.put("interventionStrategy", user.getInterventionStrategy() != null ? user.getInterventionStrategy() : 1);
        if (dto.getUserProfile() != null) {
            var up = dto.getUserProfile();
            if (up.getId() != null) profile.put("id", up.getId());
            if (StringUtils.hasText(up.getUsername())) profile.put("username", up.getUsername());
            if (up.getAgeGroup() != null) profile.put("ageGroup", up.getAgeGroup());
            if (up.getGender() != null) profile.put("gender", up.getGender());
            if (StringUtils.hasText(up.getOccupation())) profile.put("occupation", up.getOccupation());
            if (up.getRiskPreference() != null) profile.put("riskPreference", up.getRiskPreference());
            if (up.getRiskThreshold() != null) profile.put("riskThreshold", up.getRiskThreshold().doubleValue());
            if (up.getInterventionStrategy() != null) profile.put("interventionStrategy", up.getInterventionStrategy());
        }
        return profile;
    }

    @SneakyThrows
    private void saveDetectionRecord(Long userId, MlPredictResult result, SendMessageDTO dto, String content) {
        String tagsStr = result.getTags() != null ? String.join(",", result.getTags()) : null;
        String killChainTagsStr = result.getKillChainTags() != null ? String.join(",", result.getKillChainTags()) : null;

        // 序列化 JSON 字段
        String intentUnitsJson = result.getIntentUnits() != null
                ? objectMapper.writeValueAsString(result.getIntentUnits()) : null;
        String evidenceJson = result.getEvidenceNodes() != null
                ? objectMapper.writeValueAsString(result.getEvidenceNodes()) : null;
        String conformalJson = result.getConformalInterval() != null
                ? objectMapper.writeValueAsString(result.getConformalInterval()) : null;
        String dlpJson = result.getDlpStats() != null
                ? objectMapper.writeValueAsString(result.getDlpStats()) : null;

        // 计算报告 SM3 哈希（SM3Service 注入失败时降级为空）
        String reportContent = StringUtils.hasText(result.getReport()) ? result.getReport()
                : (StringUtils.hasText(result.getChatResponse()) ? result.getChatResponse() : "");
        String reportHash = computeSm3Hex(reportContent);
        long reportTimestamp = System.currentTimeMillis();

        DetectionRecord record = DetectionRecord.builder()
                .userId(userId)
                .fileUrl(firstNonBlank(dto.getImage_path(), dto.getAudio_path(), dto.getVideo_path()))
                .textContent(content)
                .riskScore(BigDecimal.valueOf(result.getRiskScore() != null ? result.getRiskScore() : 0.0))
                .scamType(StringUtils.hasText(result.getScamType()) ? result.getScamType() : "OTHER_UNKNOWN")
                .tags(tagsStr)
                .evidence(evidenceJson)
                .routeLevel(StringUtils.hasText(result.getRouteLevel()) ? result.getRouteLevel() : result.getRiskAction())
                .intentUnits(intentUnitsJson)
                .killChainTags(killChainTagsStr)
                .trustScore(result.getTrustScore() != null ? BigDecimal.valueOf(result.getTrustScore()) : null)
                .uncertaintyScore(result.getUncertaintyScore() != null ? BigDecimal.valueOf(result.getUncertaintyScore()) : null)
                .conformalInterval(conformalJson)
                .policyAction(StringUtils.hasText(result.getPolicyAction()) ? result.getPolicyAction() : result.getRiskAction())
                .dlpSummary(dlpJson)
                .summary(StringUtils.hasText(result.getChatResponse()) ? result.getChatResponse() : "")
                .reportHash(reportHash)
                .reportTimestamp(reportTimestamp)
                .createdAt(LocalDateTime.now())
                .build();
        detectionRecordMapper.insert(record);
    }

    private ChatResponseVO buildResponseVO(MlPredictResult result, int chatType, String chatReply) {
        ChatResponseVO vo = new ChatResponseVO();
        vo.setChatType(chatType);
        vo.setChatResponse(chatReply);
        vo.setReport(result.getReport() != null ? result.getReport() : "");
        vo.setRiskScore(result.getRiskScore());
        vo.setRiskLevel(result.getRiskLevel());
        vo.setScamType(result.getScamType());
        vo.setTags(result.getTags());
        vo.setConfidence(result.getConfidence());
        vo.setRiskAction(result.getRiskAction());
        // 新增字段透传给前端
        vo.setDlpStats(result.getDlpStats());
        vo.setDeepfakeImageScore(result.getDeepfakeImageScore());
        vo.setDeepfakeAudioScore(result.getDeepfakeAudioScore());
        vo.setDeepfakeVideoScore(result.getDeepfakeVideoScore());
        vo.setDeepfakeFusionScore(result.getDeepfakeFusionScore());
        vo.setIntentUnits(result.getIntentUnits());
        vo.setKillChainTags(result.getKillChainTags());
        vo.setIntentConfidence(result.getIntentConfidence());
        vo.setRouteLevel(result.getRouteLevel());
        vo.setRouteLatencyMs(result.getRouteLatencyMs());
        vo.setEvidenceNodes(result.getEvidenceNodes());
        vo.setHallucinatedRefs(result.getHallucinatedRefs());
        vo.setVeriCotSteps(result.getVeriCotSteps());
        vo.setTrustScore(result.getTrustScore());
        vo.setUncertaintyScore(result.getUncertaintyScore());
        vo.setConformalInterval(result.getConformalInterval());
        vo.setPolicyAction(result.getPolicyAction());
        return vo;
    }

    private void saveMessage(Long userId, String sessionId, String role, String content, String fileUrl) {
        save(ChatMessage.builder()
                .userId(userId)
                .sessionId(sessionId)
                .role(role)
                .content(content != null ? content : "")
                .fileUrl(fileUrl)
                .createdAt(LocalDateTime.now())
                .build());
    }

    private String buildFallbackReply(MlPredictResult result) {
        return StringUtils.hasText(result.getChatResponse()) ? result.getChatResponse() : "检测完成，请查看分析结果。";
    }

    private String normalizePath(String v) {
        if (v == null || v.isBlank()) return "";
        String path = v.trim().replace("\\", "/");
        if (path.startsWith("http") && path.contains("/uploads/")) {
            path = "." + path.substring(path.indexOf("/uploads/"));
        }
        return path;
    }

    private String firstNonBlank(String... values) {
        for (String v : values) if (StringUtils.hasText(v)) return v;
        return null;
    }

    /**
     * 计算 SM3 哈希（纯 Java 实现，无需第三方库）
     * SM3 是国密标准哈希算法，输出 256 位（32字节）
     */
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

    // ──────── SM3 国密哈希算法纯 Java 实现 ────────────────────

    private static final int[] T = new int[64];
    static {
        for (int i = 0; i < 16; i++) T[i] = 0x79cc4519;
        for (int i = 16; i < 64; i++) T[i] = 0x7a879d8a;
    }

    private byte[] sm3(byte[] msg) {
        // 1. 填充
        int len = msg.length;
        int bitLen = len * 8;
        int padLen = (len % 64 < 56) ? (56 - len % 64) : (120 - len % 64);
        byte[] padded = new byte[len + padLen + 8];
        System.arraycopy(msg, 0, padded, 0, len);
        padded[len] = (byte) 0x80;
        for (int i = 0; i < 8; i++) {
            padded[padded.length - 1 - i] = (byte) ((long) bitLen >> (i * 8));
        }
        // 2. 初始哈希值
        int[] v = {0x7380166f, 0x4914b2b9, 0x172442d7, (int) 0xda8a0600,
                   (int) 0xa96f30bc, 0x163138aa, (int) 0xe38dee4d, (int) 0xb0fb0e4e};
        // 3. 压缩
        for (int i = 0; i < padded.length / 64; i++) {
            int[] w = new int[68];
            int[] w1 = new int[64];
            for (int j = 0; j < 16; j++) {
                w[j] = ((padded[i * 64 + j * 4] & 0xff) << 24)
                      | ((padded[i * 64 + j * 4 + 1] & 0xff) << 16)
                      | ((padded[i * 64 + j * 4 + 2] & 0xff) << 8)
                      | (padded[i * 64 + j * 4 + 3] & 0xff);
            }
            for (int j = 16; j < 68; j++) {
                w[j] = p1(w[j - 16] ^ w[j - 9] ^ rol(w[j - 3], 15))
                        ^ rol(w[j - 13], 7) ^ w[j - 6];
            }
            for (int j = 0; j < 64; j++) w1[j] = w[j] ^ w[j + 4];
            int a = v[0], b = v[1], c = v[2], d = v[3];
            int e = v[4], f = v[5], g = v[6], h = v[7];
            for (int j = 0; j < 64; j++) {
                int ss1 = rol(rol(a, 12) + e + rol(T[j], j % 32), 7);
                int ss2 = ss1 ^ rol(a, 12);
                int tt1 = ff(a, b, c, j) + d + ss2 + w1[j];
                int tt2 = gg(e, f, g, j) + h + ss1 + w[j];
                d = c; c = rol(b, 9); b = a; a = tt1;
                h = g; g = rol(f, 19); f = e; e = p0(tt2);
            }
            v[0] ^= a; v[1] ^= b; v[2] ^= c; v[3] ^= d;
            v[4] ^= e; v[5] ^= f; v[6] ^= g; v[7] ^= h;
        }
        byte[] result = new byte[32];
        for (int i = 0; i < 8; i++) {
            result[i * 4] = (byte) (v[i] >>> 24);
            result[i * 4 + 1] = (byte) (v[i] >>> 16);
            result[i * 4 + 2] = (byte) (v[i] >>> 8);
            result[i * 4 + 3] = (byte) v[i];
        }
        return result;
    }

    private int rol(int x, int n) { return (x << n) | (x >>> (32 - n)); }
    private int ff(int x, int y, int z, int j) { return j < 16 ? x ^ y ^ z : (x & y) | (x & z) | (y & z); }
    private int gg(int x, int y, int z, int j) { return j < 16 ? x ^ y ^ z : (x & y) | (~x & z); }
    private int p0(int x) { return x ^ rol(x, 9) ^ rol(x, 17); }
    private int p1(int x) { return x ^ rol(x, 15) ^ rol(x, 23); }
}
