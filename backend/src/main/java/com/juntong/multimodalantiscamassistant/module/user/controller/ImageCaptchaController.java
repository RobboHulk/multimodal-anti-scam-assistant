package com.juntong.multimodalantiscamassistant.module.user.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

/**
 * 图片验证码控制器：生成干扰线+旋转字符的验证码图片，存入 Redis
 */
@Slf4j
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class ImageCaptchaController {

    private final StringRedisTemplate redisTemplate;

    private static final String CAPTCHA_PREFIX = "img_captcha:";
    private static final long CAPTCHA_TTL = 5; // 分钟
    private static final SecureRandom RANDOM = new SecureRandom();

    // 避免混淆的字符集
    private static final String CHAR_SET = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";

    @Operation(summary = "获取图片验证码",
            description = "返回 captchaKey + base64 图片。验证码 5 分钟内有效，校验后删除。")
    @GetMapping("/image-captcha")
    public Result<Map<String, String>> getImageCaptcha() {
        try {
            // 1. 生成 4 位随机验证码
            StringBuilder code = new StringBuilder(4);
            for (int i = 0; i < 4; i++) {
                code.append(CHAR_SET.charAt(RANDOM.nextInt(CHAR_SET.length())));
            }
            String captchaCode = code.toString();

            // 2. 生成唯一 key 并存入 Redis
            String captchaKey = UUID.randomUUID().toString().replace("-", "").substring(0, 16);
            redisTemplate.opsForValue().set(CAPTCHA_PREFIX + captchaKey, captchaCode, CAPTCHA_TTL, TimeUnit.MINUTES);

            // 3. 绘制验证码图片
            BufferedImage image = drawCaptchaImage(captchaCode);

            // 4. 转 base64
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, "png", baos);
            String base64 = "data:image/png;base64," + Base64.getEncoder().encodeToString(baos.toByteArray());

            log.info("图片验证码生成: key={}, code={}", captchaKey, captchaCode);

            return Result.ok(Map.of("captchaKey", captchaKey, "captchaImage", base64));
        } catch (Exception e) {
            log.error("验证码生成失败", e);
            return Result.fail("验证码生成失败");
        }
    }

    // ==================== 图片绘制 ====================

    private BufferedImage drawCaptchaImage(String code) {
        int width = 130, height = 48;
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g2d = image.createGraphics();

        // 抗锯齿
        g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

        // 背景填充（深色，匹配前端风格）
        g2d.setColor(new Color(0x1a1a2e));
        g2d.fillRect(0, 0, width, height);

        // 随机干扰线
        for (int i = 0; i < 5; i++) {
            g2d.setColor(randomColor(100, 180));
            int x1 = RANDOM.nextInt(width);
            int y1 = RANDOM.nextInt(height);
            int x2 = RANDOM.nextInt(width);
            int y2 = RANDOM.nextInt(height);
            g2d.setStroke(new BasicStroke(1.2f + RANDOM.nextFloat()));
            g2d.drawLine(x1, y1, x2, y2);
        }

        // 干扰点
        for (int i = 0; i < 60; i++) {
            g2d.setColor(randomColor(120, 200));
            int x = RANDOM.nextInt(width);
            int y = RANDOM.nextInt(height);
            g2d.fillOval(x, y, 2, 2);
        }

        // 逐一绘制字符（带旋转）
        Font[] fonts = {
                new Font("Arial", Font.BOLD, 28),
                new Font("Consolas", Font.BOLD, 28),
                new Font("Georgia", Font.ITALIC | Font.BOLD, 28),
        };

        int charWidth = width / (code.length() + 1);
        for (int i = 0; i < code.length(); i++) {
            g2d.setFont(fonts[RANDOM.nextInt(fonts.length)]);
            g2d.setColor(randomColor(180, 255));

            // 每个字符独立旋转
            AffineTransform oldAt = g2d.getTransform();
            int x = charWidth * (i + 1) - 5 + RANDOM.nextInt(8);
            int y = 32 + RANDOM.nextInt(8);
            double angle = (RANDOM.nextDouble() - 0.5) * 0.5; // ±0.25 rad ≈ ±15°
            g2d.rotate(angle, x, y);
            g2d.drawString(String.valueOf(code.charAt(i)), x, y);
            g2d.setTransform(oldAt);
        }

        g2d.dispose();
        return image;
    }

    private Color randomColor(int min, int max) {
        int r = min + RANDOM.nextInt(max - min);
        int g = min + RANDOM.nextInt(max - min);
        int b = min + RANDOM.nextInt(max - min);
        // 让字符偏向亮色（蓝紫调）
        if (max > 180) {
            b = Math.min(255, b + 30);
            r = Math.max(0, r - 20);
        }
        return new Color(r, g, b);
    }
}
