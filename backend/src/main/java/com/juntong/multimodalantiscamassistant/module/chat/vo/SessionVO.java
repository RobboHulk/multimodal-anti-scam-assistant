package com.juntong.multimodalantiscamassistant.module.chat.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SessionVO {
    private String sessionId;
    private String title;
    private LocalDateTime lastTime;
    private Integer msgCount;
}
