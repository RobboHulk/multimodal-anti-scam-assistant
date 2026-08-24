package com.juntong.multimodalantiscamassistant.module.chat.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 历史消息条目模型
 */
@Data
@Schema(description = "历史对话消息模型")
public class ChatMessageVO {

    @Schema(description = "消息ID")
    private Long id;

    @Schema(description = "会话ID")
    private String sessionId;

    @Schema(description = "发送者角色: user=用户, assistant=AI助手", example = "user")
    private String role;

    @Schema(description = "消息文本内容")
    private String content;

    @Schema(description = "关联的文件/图片URL")
    private String fileUrl;

    @Schema(description = "发送时间")
    private LocalDateTime createdAt;
}
