package com.juntong.multimodalantiscamassistant.module.user.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import com.juntong.multimodalantiscamassistant.common.util.JwtUtil;
import com.juntong.multimodalantiscamassistant.module.user.entity.User;
import com.juntong.multimodalantiscamassistant.module.user.dto.ForgotPasswordDTO;
import com.juntong.multimodalantiscamassistant.module.user.dto.LoginDTO;
import com.juntong.multimodalantiscamassistant.module.user.dto.RegisterDTO;
import com.juntong.multimodalantiscamassistant.module.user.dto.UpdateConfigDTO;
import com.juntong.multimodalantiscamassistant.module.user.dto.UpdateProfileDTO;
import com.juntong.multimodalantiscamassistant.module.user.mapper.UserMapper;
import com.juntong.multimodalantiscamassistant.module.user.service.UserService;
import com.juntong.multimodalantiscamassistant.module.user.vo.UserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import java.util.Map;
import jakarta.servlet.http.HttpServletRequest;

@Tag(name = "1. 用户与角色管理", description = "处理用户注册、登录、个人画像及风险配置")
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;
    private final UserMapper userMapper;
    private final JwtUtil jwtUtil;

    @Operation(summary = "用户注册", description = "网页端用户注册，注册成功后返回 Token")
    @PostMapping("/register")
    public Result<String> register(@RequestBody @Validated RegisterDTO dto) {
        return Result.ok(userService.register(dto));
    }

    @Operation(summary = "用户登录", description = "网页端用户名密码登录，成功后返回 Token")
    @PostMapping("/login")
    public Result<String> login(@RequestBody @Validated LoginDTO dto) {
        return Result.ok(userService.login(dto));
    }

    @Operation(summary = "检查用户名是否存在", description = "绕过逻辑删除，返回 true 表示用户名已被占用")
    @GetMapping("/exists")
    public Result<Boolean> exists(@RequestParam String username) {
        return Result.ok(userMapper.usernameExists(username));
    }

    @Operation(summary = "忘记密码", description = "校验图片验证码后返回该用户密码")
    @PostMapping("/forgot-password")
    public Result<String> forgotPassword(@RequestBody @Validated ForgotPasswordDTO dto) {
        return Result.ok(userService.forgotPassword(dto.getUsername(), dto.getCaptchaKey(), dto.getCaptchaCode()));
    }

    @Operation(summary = "用户退出", description = "将当前 Token 打入后端 Redis 黑名单废弃，实现安全登出")
    @PostMapping("/logout")
    public Result<Void> logout(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            jwtUtil.invalidateToken(header.substring(7));
        }
        return Result.ok();
    }

    @Operation(summary = "获取个人画像", description = "获取当前用户的角色属性（年龄、职业等）及已绑定的监护人列表")
    @GetMapping("/profile")
    public Result<UserVO> getProfile() {
        return Result.ok(userService.getProfile(currentUserId()));
    }

    @Operation(summary = "更新头像")
    @PutMapping("/avatar")
    public Result<Void> updateAvatar(@RequestBody Map<String, String> body) {
        userService.lambdaUpdate()
                .eq(User::getId, currentUserId())
                .set(User::getAvatar, body.get("avatar"))
                .update();
        return Result.ok();
    }

    @Operation(summary = "更新角色属性", description = "修改年龄段、性别、职业等非安全配置属性")
    @PutMapping("/profile")
    public Result<Void> updateProfile(@RequestBody @Validated UpdateProfileDTO dto) {
        userService.updateProfile(currentUserId(), dto);
        return Result.ok();
    }

    @Operation(summary = "更新风险配置", description = "手动调整风险灵敏度、判定阈值以及触发预警后的干预策略")
    @PutMapping("/config")
    public Result<Void> updateConfig(@RequestBody @Validated UpdateConfigDTO dto) {
        userService.updateConfig(currentUserId(), dto);
        return Result.ok();
    }

    @Operation(summary = "修改密码", description = "验证旧密码后修改为新密码")
    @PutMapping("/change-password")
    public Result<Void> changePassword(@RequestBody Map<String, String> body) {
        String oldPwd = body.get("oldPassword");
        String newPwd = body.get("newPassword");
        if (oldPwd == null || newPwd == null || newPwd.length() < 6) {
            return Result.fail(400, "密码至少6位");
        }
        userService.changePassword(currentUserId(), oldPwd, newPwd);
        return Result.ok();
    }

    @Operation(summary = "获取行为画像 (ML)", description = "供多模态 ML 服务拉取用户的长短期记忆画像，用于辅助判定")
    @GetMapping("/memory")
    public Result<UserVO> getMemory() {
        return Result.ok(userService.getMemory(currentUserId()));
    }

    /** 从 SecurityContext 取出当前登录用户 ID */
    private Long currentUserId() {
        return (Long) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }
}
