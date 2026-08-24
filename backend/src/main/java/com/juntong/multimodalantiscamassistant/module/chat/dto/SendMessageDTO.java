package com.juntong.multimodalantiscamassistant.module.chat.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 发送消息请求体
 */
@Data
@Schema(description = "发送对话消息模型")
public class SendMessageDTO {

    @Schema(description = "用户当前输入文本", example = "这张图片里的中奖信息是真的吗？")
    private String text;

    @Schema(description = "会话 ID", example = "sess-1001")
    private String session_id;

    @Schema(description = "用户画像信息")
    private UserProfilePayload userProfile;

    @Schema(description = "图片路径或可访问地址", example = "http://example.com/oss/a.jpg")
    private String image_path;

    @Schema(description = "音频路径或可访问地址", example = "http://example.com/oss/a.mp3")
    private String audio_path;

    @Schema(description = "视频路径或可访问地址", example = "http://example.com/oss/a.mp4")
    private String video_path;
}
