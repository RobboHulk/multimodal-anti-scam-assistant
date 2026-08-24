package com.juntong.multimodalantiscamassistant.common.ml;

import lombok.Builder;
import lombok.Data;

import java.util.Map;

/**
 * 发往 ML 服务的预测请求体
 */
@Data
@Builder
public class MlPredictRequest {

    /** 用户当前输入文本 */
    private String text;

    /** 会话 ID */
    private String session_id;

    /** 用户画像，影响个性化风险阈值 */
    private Map<String, Object> userProfile;

    /** 图片路径或可访问地址 */
    private String image_path;

    /** 音频路径或可访问地址 */
    private String audio_path;

    /** 视频路径或可访问地址 */
    private String video_path;
}
