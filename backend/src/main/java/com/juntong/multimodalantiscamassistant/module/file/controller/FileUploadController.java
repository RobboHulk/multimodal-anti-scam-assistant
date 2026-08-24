package com.juntong.multimodalantiscamassistant.module.file.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import com.juntong.multimodalantiscamassistant.common.exception.BusinessException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import jakarta.servlet.http.HttpServletRequest;

import java.io.File;
import java.io.IOException;
import java.util.UUID;
import com.juntong.multimodalantiscamassistant.common.util.FileProcessUtil;

@Slf4j
@Tag(name = "4. 多模态文件存储核心", description = "统接收前端上传的照片、语音等多源异构媒体数据，落盘后返回内部网络或公网的访问 URL")
@RestController
@RequestMapping("/api/file")
public class FileUploadController {

    @Value("${file.upload-dir:./uploads/}")
    private String uploadDir;

    @Operation(summary = "上传多模态文件资源", description = "接收单文件输入，服务端动态生成全球唯一 ID 保障非碰撞，最后以 JSON 文本形式返回资源完整 URL")
    @PostMapping("/upload")
    public Result<String> upload(@RequestParam("file") MultipartFile file, HttpServletRequest request) {
        if (file.isEmpty()) {
            throw new BusinessException(400, "不安全上传：未检测到目标文件载荷");
        }

        try {
            File dir = new File(uploadDir);
            if (!dir.exists()) {
                dir.mkdirs();
            }

            // 获取原生名提取保留原生格式后缀（.jpg / .mp3 等）
            String originalFilename = file.getOriginalFilename();
            String suffix = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                suffix = originalFilename.substring(originalFilename.lastIndexOf("."));
            }

            // 1 & 2. 校验文件魔数、物理大小限流与鉴权分类
            FileProcessUtil.FileType fileType = FileProcessUtil.checkMagicAndType(file, suffix);

            // 安全覆盖重组与初始落盘
            String newFilename = UUID.randomUUID().toString().replace("-", "") + suffix;
            File dest = new File(dir.getAbsolutePath() + File.separator + newFilename);

            // 3. 基础清洗环节（如果是图像，进行分辨率过滤与 JPEG 转码归一化）
            if (fileType == FileProcessUtil.FileType.IMAGE) {
                dest = FileProcessUtil.processImageAndTranscode(file, dest);
            } else {
                // 音频等其他安全源文件直接写盘
                file.transferTo(dest);
            }

            // 更新最终落盘后的名字（如果被洗成了 .jpg）
            newFilename = dest.getName();

            // 基于当前宿主机/容器的 Request 请求体提取域名及端口并反签路径
            // 在前后端分离中，通常可给出 /uploads/... 由前端组装，为照顾 ML 等跨微服务组件也支持全协议栈抛出。
            String baseUrl = request.getScheme() + "://" + request.getServerName() + ":" + request.getServerPort();
            String fileUrl = baseUrl + "/uploads/" + newFilename;

            return Result.ok(fileUrl);

        } catch (IOException e) {
            log.error("多模态数据管道断裂，文件保存异常", e);
            throw new BusinessException(500, "文件落盘或系统IO错误: " + e.getMessage());
        }
    }
}
