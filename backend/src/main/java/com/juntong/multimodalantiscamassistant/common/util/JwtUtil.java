package com.juntong.multimodalantiscamassistant.common.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.concurrent.TimeUnit;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.beans.factory.annotation.Autowired;

/**
 * JWT 工具类：生成 / 解析 / 校验 Token
 */
@Component
public class JwtUtil {

    @Value("${jwt.secret}")
    private String secret;

    @Value("${jwt.expiration}")
    private Long expiration;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private static final String BLACKLIST_PREFIX = "jwt:blacklist:";

    /** 生成 Token（默认角色 USER） */
    public String generateToken(Long id) {
        return generateToken(id, "USER");
    }

    /** 生成 Token，role 传入 "USER" 或 "GUARDIAN" */
    public String generateToken(Long id, String role) {
        return Jwts.builder()
                .subject(String.valueOf(id))
                .claim("role", role)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expiration))
                .signWith(getKey())
                .compact();
    }

    /** 从 Token 中解析 ID */
    public Long parseId(String token) {
        return Long.parseLong(getClaims(token).getSubject());
    }

    /** 从 Token 中解析角色 */
    public String parseRole(String token) {
        return getClaims(token).get("role", String.class);
    }

    /** 校验 Token 是否有效 */
    public boolean isValid(String token) {
        try {
            // 检查是否在黑名单中
            if (Boolean.TRUE.equals(redisTemplate.hasKey(BLACKLIST_PREFIX + token))) {
                return false;
            }
            getClaims(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /** 将 Token 加入黑名单（登出时调用） */
    public void invalidateToken(String token) {
        try {
            Claims claims = getClaims(token);
            Date expirationDate = claims.getExpiration();
            long remainTime = expirationDate.getTime() - System.currentTimeMillis();
            if (remainTime > 0) {
                // 将 token 放入 Redis 黑名单，过期时间与 token 的剩余存活时间一致
                redisTemplate.opsForValue().set(BLACKLIST_PREFIX + token, "invalid", remainTime, TimeUnit.MILLISECONDS);
            }
        } catch (Exception e) {
            // 解析失败（可能已过期等）说明无需再操作黑名单
        }
    }

    private Claims getClaims(String token) {
        return Jwts.parser()
                .verifyWith(getKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private SecretKey getKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
}
