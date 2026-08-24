package com.juntong.multimodalantiscamassistant.module.chat.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import com.juntong.multimodalantiscamassistant.common.exception.BusinessException;
import com.juntong.multimodalantiscamassistant.module.chat.dto.SendMessageDTO;
import com.juntong.multimodalantiscamassistant.module.chat.service.impl.ChatServiceImpl;
import com.juntong.multimodalantiscamassistant.module.chat.vo.ChatMessageVO;
import com.juntong.multimodalantiscamassistant.module.chat.vo.ChatResponseVO;
import com.juntong.multimodalantiscamassistant.module.chat.vo.SessionVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "4. 安全研判控制台", description = "多模态安全检测统一入口：支持文本、截图、音频、视频输入，返回完整安全分析链路结果")
@RestController
@RequestMapping("/api/detect")
@RequiredArgsConstructor
public class ChatController {

    private final ChatServiceImpl chatService;

    @Operation(
        summary = "提交安全检测请求",
        description = "统一多模态安全检测入口。支持文本/图片/音频/视频，" +
            "返回 DLP 脱敏统计、深伪检测分数、DSCP 意图分解、DepthGate 路由、" +
            "证据网络 [REF-N]、Conformal Prediction 置信区间及最终策略动作。"
    )
    @PostMapping("/analyze")
    public Result<ChatResponseVO> analyze(@RequestBody SendMessageDTO dto) {
        if ((dto.getText() == null || dto.getText().isBlank())
                && isBlank(dto.getImage_path())
                && isBlank(dto.getAudio_path())
                && isBlank(dto.getVideo_path())) {
            throw new BusinessException(400, "text、image_path、audio_path、video_path 至少填一个");
        }
        return Result.ok(chatService.send(currentId(), dto));
    }

    @Operation(summary = "获取检测历史记录", description = "获取当前用户的检测记录，可选按 sessionId 筛选")
    @GetMapping("/history")
    public Result<List<ChatMessageVO>> history(@RequestParam(required = false) String sessionId) {
        return Result.ok(chatService.history(currentId(), sessionId));
    }

    @Operation(summary = "获取检测会话列表", description = "获取当前用户的检测会话列表（按 session_id 分组）")
    @GetMapping("/sessions")
    public Result<List<SessionVO>> sessions() {
        return Result.ok(chatService.sessions(currentId()));
    }

    @Operation(summary = "删除检测会话", description = "删除指定会话及其所有检测记录")
    @DeleteMapping("/session/{sessionId}")
    public Result<String> deleteSession(@PathVariable String sessionId) {
        chatService.deleteSession(currentId(), sessionId);
        return Result.ok("删除成功");
    }

    private Long currentId() {
        return (Long) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }
}
