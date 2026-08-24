package com.juntong.multimodalantiscamassistant.config;

import com.juntong.multimodalantiscamassistant.filter.JwtAuthFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Spring Security 配置：无状态 JWT 模式
 */
@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtAuthFilter jwtAuthFilter;
    private final JsonAuthenticationEntryPoint jsonEntryPoint;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .exceptionHandling(ex -> ex.authenticationEntryPoint(jsonEntryPoint))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                    // 用户认证
                    "/api/user/register",
                    "/api/user/login",
                    "/api/user/captcha",
                    "/api/user/image-captcha",
                    "/api/user/exists",
                    "/api/user/forgot-password",
                    // 威胁情报库（公开读取）
                    "/api/knowledge/list",
                    "/api/knowledge/related",
                    "/api/knowledge/scam-types",
                    "/api/knowledge/*",
                    // 取证报告公开验证（无需登录）
                    "/api/verify/report/**",
                    "/api/verify/report/by-hash",
                    // 静态资源
                    "/uploads/**",
                    // API 文档
                    "/swagger-ui/**",
                    "/v3/api-docs/**"
                ).permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
