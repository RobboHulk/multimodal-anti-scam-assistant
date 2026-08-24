package com.juntong.multimodalantiscamassistant.module.detect.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.juntong.multimodalantiscamassistant.common.ml.MlPredictRequest;
import com.juntong.multimodalantiscamassistant.common.ml.MlPredictResult;
import com.juntong.multimodalantiscamassistant.common.ml.MlServiceClient;
import com.juntong.multimodalantiscamassistant.module.detect.dto.BatchDetectDTO;
import com.juntong.multimodalantiscamassistant.module.detect.dto.BatchDetectItemDTO;
import com.juntong.multimodalantiscamassistant.module.detect.dto.DetectDTO;
import com.juntong.multimodalantiscamassistant.module.detect.entity.DetectionRecord;
import com.juntong.multimodalantiscamassistant.module.detect.mapper.DetectionRecordMapper;
import com.juntong.multimodalantiscamassistant.module.detect.vo.BatchDetectResultVO;
import com.juntong.multimodalantiscamassistant.module.detect.vo.DetectResultVO;
import com.juntong.multimodalantiscamassistant.module.user.entity.User;
import com.juntong.multimodalantiscamassistant.module.user.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 多模态安全检测服务（批量检测/单次检测入口）
 * 已移除 AlertService 依赖（alert 模块已删除）
 */
@Service
@RequiredArgsConstructor
public class DetectionServiceImpl extends ServiceImpl<DetectionRecordMapper, DetectionRecord> {

    private final MlServiceClient mlServiceClient;
    private final UserMapper userMapper;
    private final ObjectMapper objectMapper;

    public DetectResultVO detect(Long userId, DetectDTO dto) {
        User user = userMapper.selectById(userId);
        if (user == null) {
            throw new com.juntong.multimodalantiscamassistant.common.exception.BusinessException(404, "用户不存在，ID: " + userId);
        }

        String imagePath = isImageUrl(dto.getFileUrl()) ? dto.getFileUrl() : null;
        String audioPath = isAudioUrl(dto.getFileUrl()) ? dto.getFileUrl() : null;
        String videoPath = isVideoUrl(dto.getFileUrl()) ? dto.getFileUrl() : null;

        MlPredictRequest request = MlPredictRequest.builder()
                .text(dto.getText())
                .session_id("detect-" + userId + "-" + System.currentTimeMillis())
                .userProfile(Map.of(
                        "id", user.getId(),
                        "username", user.getUsername() != null ? user.getUsername() : "",
                        "ageGroup", user.getAgeGroup() != null ? user.getAgeGroup() : 0,
                        "gender", user.getGender() != null ? user.getGender() : 0,
                        "occupation", user.getOccupation() != null ? user.getOccupation() : "",
                        "riskPreference", user.getRiskPreference() != null ? user.getRiskPreference() : 2,
                        "riskThreshold", user.getRiskThreshold() != null ? user.getRiskThreshold() : BigDecimal.valueOf(0.7),
                        "interventionStrategy", user.getInterventionStrategy() != null ? user.getInterventionStrategy() : 1))
                .image_path(imagePath)
                .audio_path(audioPath)
                .video_path(videoPath)
                .build();

        MlPredictResult result = mlServiceClient.predict(request);

        String tagsStr = result.getTags() != null ? String.join(",", result.getTags()) : null;
        String killChainStr = result.getKillChainTags() != null ? String.join(",", result.getKillChainTags()) : null;
        String summaryOrReport = StringUtils.hasText(result.getReport()) ? result.getReport()
                : (StringUtils.hasText(result.getChatResponse()) ? result.getChatResponse() : "");

        // 序列化 JSON 字段
        String intentUnitsJson = toJson(result.getIntentUnits());
        String evidenceJson = toJson(result.getEvidenceNodes());
        String conformalJson = toJson(result.getConformalInterval());
        String dlpJson = toJson(result.getDlpStats());

        String reportHash = computeSm3Hex(summaryOrReport);
        long reportTimestamp = System.currentTimeMillis();

        DetectionRecord record = DetectionRecord.builder()
                .userId(userId)
                .fileUrl(dto.getFileUrl())
                .textContent(dto.getText())
                .riskScore(BigDecimal.valueOf(result.getRiskScore() != null ? result.getRiskScore() : 0))
                .scamType(StringUtils.hasText(result.getScamType()) ? result.getScamType() : "OTHER_UNKNOWN")
                .tags(tagsStr)
                .evidence(evidenceJson)
                .routeLevel(StringUtils.hasText(result.getRouteLevel()) ? result.getRouteLevel() : result.getRiskAction())
                .intentUnits(intentUnitsJson)
                .killChainTags(killChainStr)
                .trustScore(result.getTrustScore() != null ? BigDecimal.valueOf(result.getTrustScore()) : null)
                .uncertaintyScore(result.getUncertaintyScore() != null ? BigDecimal.valueOf(result.getUncertaintyScore()) : null)
                .conformalInterval(conformalJson)
                .policyAction(StringUtils.hasText(result.getPolicyAction()) ? result.getPolicyAction() : result.getRiskAction())
                .dlpSummary(dlpJson)
                .summary(summaryOrReport)
                .reportHash(reportHash)
                .reportTimestamp(reportTimestamp)
                .createdAt(LocalDateTime.now())
                .build();
        save(record);

        DetectResultVO vo = new DetectResultVO();
        vo.setRecordId(record.getId());
        vo.setRiskScore(result.getRiskScore());
        vo.setRiskLevel(result.getRiskLevel());
        vo.setScamType(result.getScamType());
        vo.setTags(result.getTags() != null ? result.getTags() : new ArrayList<>());
        vo.setConfidence(result.getConfidence());
        vo.setRiskAction(result.getRiskAction());
        vo.setSummary(summaryOrReport);
        vo.setCreatedAt(record.getCreatedAt());
        return vo;
    }

    public BatchDetectResultVO detectBatch(Long userId, BatchDetectDTO dto) {
        int tp = 0, fp = 0, fn = 0, tn = 0;
        List<DetectResultVO> detailResults = new ArrayList<>();

        for (BatchDetectItemDTO item : dto.getItems()) {
            DetectResultVO resultVO = detect(userId, item);
            detailResults.add(resultVO);
            boolean modelIsScam = resultVO.getRiskScore() != null && resultVO.getRiskScore() >= 0.7;
            boolean expectedIsScam = item.getExpectedIsScam() != null && item.getExpectedIsScam() == 1;
            if (expectedIsScam && modelIsScam) tp++;
            else if (!expectedIsScam && modelIsScam) fp++;
            else if (expectedIsScam) fn++;
            else tn++;
        }

        BatchDetectResultVO batchVO = new BatchDetectResultVO();
        batchVO.setTotalCount(dto.getItems().size());
        batchVO.setTruePositive(tp);
        batchVO.setFalsePositive(fp);
        batchVO.setTrueNegative(tn);
        batchVO.setFalseNegative(fn);
        double precision = (tp + fp) == 0 ? 0 : (double) tp / (tp + fp);
        double recall = (tp + fn) == 0 ? 0 : (double) tp / (tp + fn);
        batchVO.setAccuracy(dto.getItems().isEmpty() ? 0 : (double) (tp + tn) / dto.getItems().size());
        batchVO.setPrecision(precision);
        batchVO.setRecall(recall);
        batchVO.setF1Score((precision + recall) == 0 ? 0 : 2 * precision * recall / (precision + recall));
        batchVO.setDetailResults(detailResults);
        return batchVO;
    }

    @SneakyThrows
    private String toJson(Object obj) {
        return obj != null ? objectMapper.writeValueAsString(obj) : null;
    }

    private boolean isAudioUrl(String u) {
        if (u == null) return false;
        String l = u.toLowerCase();
        return l.endsWith(".mp3") || l.endsWith(".wav") || l.endsWith(".flac") || l.endsWith(".m4a");
    }

    private boolean isImageUrl(String u) {
        if (u == null) return false;
        String l = u.toLowerCase();
        return l.endsWith(".jpg") || l.endsWith(".jpeg") || l.endsWith(".png") || l.endsWith(".gif") || l.endsWith(".webp");
    }

    private boolean isVideoUrl(String u) {
        if (u == null) return false;
        String l = u.toLowerCase();
        return l.endsWith(".mp4") || l.endsWith(".mov") || l.endsWith(".avi") || l.endsWith(".mkv") || l.endsWith(".webm");
    }

    private String computeSm3Hex(String content) {
        if (content == null || content.isEmpty()) return "";
        try {
            byte[] data = content.getBytes(StandardCharsets.UTF_8);
            byte[] hash = sm3(data);
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b & 0xff));
            return sb.toString();
        } catch (Exception e) { return ""; }
    }

    private static final int[] T_D = new int[64];
    static { for (int i = 0; i < 16; i++) T_D[i] = 0x79cc4519; for (int i = 16; i < 64; i++) T_D[i] = 0x7a879d8a; }

    private byte[] sm3(byte[] msg) {
        int len = msg.length, bitLen = len * 8;
        int padLen = (len % 64 < 56) ? (56 - len % 64) : (120 - len % 64);
        byte[] p = new byte[len + padLen + 8];
        System.arraycopy(msg, 0, p, 0, len); p[len] = (byte) 0x80;
        for (int i = 0; i < 8; i++) p[p.length-1-i] = (byte)((long)bitLen >> (i*8));
        int[] v = {0x7380166f,0x4914b2b9,0x172442d7,(int)0xda8a0600,(int)0xa96f30bc,0x163138aa,(int)0xe38dee4d,(int)0xb0fb0e4e};
        for (int i = 0; i < p.length/64; i++) {
            int[] w = new int[68], w1 = new int[64];
            for (int j=0;j<16;j++) w[j]=((p[i*64+j*4]&0xff)<<24)|((p[i*64+j*4+1]&0xff)<<16)|((p[i*64+j*4+2]&0xff)<<8)|(p[i*64+j*4+3]&0xff);
            for (int j=16;j<68;j++) w[j]=p1(w[j-16]^w[j-9]^rol(w[j-3],15))^rol(w[j-13],7)^w[j-6];
            for (int j=0;j<64;j++) w1[j]=w[j]^w[j+4];
            int a=v[0],b=v[1],c=v[2],d=v[3],e=v[4],f=v[5],g=v[6],h=v[7];
            for (int j=0;j<64;j++){int ss1=rol(rol(a,12)+e+rol(T_D[j],j%32),7),ss2=ss1^rol(a,12);int tt1=ff(a,b,c,j)+d+ss2+w1[j],tt2=gg(e,f,g,j)+h+ss1+w[j];d=c;c=rol(b,9);b=a;a=tt1;h=g;g=rol(f,19);f=e;e=p0(tt2);}
            v[0]^=a;v[1]^=b;v[2]^=c;v[3]^=d;v[4]^=e;v[5]^=f;v[6]^=g;v[7]^=h;
        }
        byte[] r = new byte[32]; for (int i=0;i<8;i++){r[i*4]=(byte)(v[i]>>>24);r[i*4+1]=(byte)(v[i]>>>16);r[i*4+2]=(byte)(v[i]>>>8);r[i*4+3]=(byte)v[i];} return r;
    }
    private int rol(int x,int n){return(x<<n)|(x>>>(32-n));} private int ff(int x,int y,int z,int j){return j<16?x^y^z:(x&y)|(x&z)|(y&z);} private int gg(int x,int y,int z,int j){return j<16?x^y^z:(x&y)|(~x&z);} private int p0(int x){return x^rol(x,9)^rol(x,17);} private int p1(int x){return x^rol(x,15)^rol(x,23);}
}
