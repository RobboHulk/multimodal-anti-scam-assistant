package com.juntong.multimodalantiscamassistant.module.chat.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 对话消息实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("chat_message")
public class ChatMessage {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long userId;

    /** 会话ID，用于多轮对话分组 */
    private String sessionId;

    /** user / assistant */
    private String role;

    private String content;

    /** 附件文件 URL（可为空） */
    private String fileUrl;

    private LocalDateTime createdAt;
}
