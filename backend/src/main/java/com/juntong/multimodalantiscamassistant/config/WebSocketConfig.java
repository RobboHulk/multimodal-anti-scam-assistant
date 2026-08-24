package com.juntong.multimodalantiscamassistant.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * WebSocket 配置（STOMP 协议）
 * 前端连接：ws://host/ws/alert
 * 订阅预警频道：/topic/alert/{userId}
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        // 内存消息代理，前端订阅 /topic/** 接收推送
        registry.enableSimpleBroker("/topic");
        // 客户端发消息前缀（本项目暂不用，预留）
        registry.setApplicationDestinationPrefixes("/app");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws/alert")
                .setAllowedOriginPatterns("*")
                .withSockJS(); // 兼容不支持原生 WebSocket 的浏览器
    }
}
