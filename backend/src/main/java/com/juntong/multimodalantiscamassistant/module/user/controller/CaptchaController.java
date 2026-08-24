package com.juntong.multimodalantiscamassistant.module.user.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;



@Slf4j
@RestController
@RequestMapping("/api/user")
public class CaptchaController {

    @Operation(summary = "获取手机验证码")
    @GetMapping("/captcha")
    public Result<String> getCaptcha(@RequestParam String phone) {
        // 硬编码验证码方案
        String captcha = "884812";
        log.info("验证码请求: phone={}, captcha={}", phone, captcha);
        
        // 模拟发送短信，直接返回成功并带上验证码
        return Result.ok(captcha);
    }
}
