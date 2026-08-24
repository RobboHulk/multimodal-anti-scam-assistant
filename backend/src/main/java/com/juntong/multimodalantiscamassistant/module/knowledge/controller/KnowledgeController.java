package com.juntong.multimodalantiscamassistant.module.knowledge.controller;

import com.juntong.multimodalantiscamassistant.common.Result;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.juntong.multimodalantiscamassistant.module.knowledge.entity.KnowledgeArticle;
import com.juntong.multimodalantiscamassistant.module.knowledge.service.IKnowledgeArticleService;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.UUID;

@Tag(name = "6. 威胁情报库", description = "结构化威胁情报管理：支持 ATT&CK 战术标签、IOC 指标、攻击时间线，检测时自动引用 [REF-N]")
@RestController
@RequestMapping("/api/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final IKnowledgeArticleService knowledgeArticleService;
    private final com.juntong.multimodalantiscamassistant.common.ml.MlServiceClient mlServiceClient;

    private static final String UPLOAD_DIR = System.getProperty("user.home") + "/anti-scam-uploads/knowledge/";

    @Operation(summary = "上传新威胁情报样本", description = "上传包含最新攻击手法的文件，系统异步触发特征提取与向量化入库，丰富 [REF-N] 证据引用库。")
    @PostMapping(value = "/upload", consumes = "multipart/form-data")
    public Result<String> upload(
            @Parameter(description = "威胁情报文件", content = @Content(mediaType = "multipart/form-data"))
            @RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) return Result.fail(400, "文件不能为空");
        String filename = UUID.randomUUID() + "_" + file.getOriginalFilename();
        File dest = new File(UPLOAD_DIR + filename);
        dest.getParentFile().mkdirs();
        try {
            file.transferTo(dest);
        } catch (IOException e) {
            return Result.fail("文件保存失败: " + e.getMessage());
        }
        mlServiceClient.triggerVectorize(dest.getAbsolutePath());
        return Result.ok("上传成功，路径: " + dest.getAbsolutePath());
    }

    @Operation(summary = "获取威胁情报列表", description = "分页查询威胁情报，支持按关键词、诈骗类型、ATT&CK 战术 ID 过滤")
    @GetMapping("/list")
    public Result<Page<KnowledgeArticle>> list(
            @RequestParam(defaultValue = "1") Integer current,
            @RequestParam(defaultValue = "12") Integer size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String scamType,
            @RequestParam(required = false) String attackTacticId,
            @RequestParam(required = false) Integer threatLevel) {

        Page<KnowledgeArticle> page = new Page<>(current, size);
        LambdaQueryWrapper<KnowledgeArticle> qw = new LambdaQueryWrapper<>();
        qw.eq(KnowledgeArticle::getStatus, 1);

        if (keyword != null && !keyword.trim().isEmpty()) {
            qw.and(w -> w.like(KnowledgeArticle::getTitle, keyword)
                         .or().like(KnowledgeArticle::getScamType, keyword)
                         .or().like(KnowledgeArticle::getTags, keyword)
                         .or().like(KnowledgeArticle::getContent, keyword));
        }
        if (scamType != null && !scamType.trim().isEmpty()) {
            qw.eq(KnowledgeArticle::getScamType, scamType);
        }
        // 支持按 ATT&CK 战术 ID 过滤，如 T1566
        if (attackTacticId != null && !attackTacticId.trim().isEmpty()) {
            qw.like(KnowledgeArticle::getAttackTacticId, attackTacticId);
        }
        // 支持按威胁等级过滤
        if (threatLevel != null) {
            qw.eq(KnowledgeArticle::getThreatLevel, threatLevel);
        }

        qw.orderByDesc(KnowledgeArticle::getThreatLevel)
          .orderByDesc(KnowledgeArticle::getCreatedAt);
        knowledgeArticleService.page(page, qw);
        return Result.ok(page);
    }

    @Operation(summary = "获取单条威胁情报详情", description = "返回完整情报内容，含 IOC 指标、ATT&CK 标签、攻击时间线")
    @GetMapping("/{id}")
    public Result<KnowledgeArticle> getById(@PathVariable Long id) {
        KnowledgeArticle article = knowledgeArticleService.getById(id);
        if (article == null || article.getStatus() != 1) {
            return Result.fail(404, "情报不存在或已下架");
        }
        return Result.ok(article);
    }

    @Operation(summary = "获取相关威胁情报推荐", description = "根据当前情报的诈骗类型推荐同类情报，用于知识闭环")
    @GetMapping("/related")
    public Result<List<KnowledgeArticle>> getRelated(
            @RequestParam Long id,
            @RequestParam(defaultValue = "4") Integer limit) {
        KnowledgeArticle current = knowledgeArticleService.getById(id);
        if (current == null) return Result.ok(List.of());

        LambdaQueryWrapper<KnowledgeArticle> qw = new LambdaQueryWrapper<>();
        qw.eq(KnowledgeArticle::getStatus, 1)
          .ne(KnowledgeArticle::getId, id);

        if (current.getScamType() != null && !current.getScamType().isEmpty()) {
            qw.eq(KnowledgeArticle::getScamType, current.getScamType());
        }
        qw.orderByDesc(KnowledgeArticle::getThreatLevel)
          .orderByDesc(KnowledgeArticle::getCreatedAt)
          .last("LIMIT " + limit);

        return Result.ok(knowledgeArticleService.list(qw));
    }

    @Operation(summary = "获取所有攻击类型枚举", description = "返回情报库中所有已有的 scamType 值，用于前端筛选器")
    @GetMapping("/scam-types")
    public Result<List<String>> scamTypes() {
        List<KnowledgeArticle> all = knowledgeArticleService.list(
                new LambdaQueryWrapper<KnowledgeArticle>()
                        .eq(KnowledgeArticle::getStatus, 1)
                        .select(KnowledgeArticle::getScamType));
        List<String> types = all.stream()
                .map(KnowledgeArticle::getScamType)
                .filter(s -> s != null && !s.isBlank())
                .distinct()
                .sorted()
                .toList();
        return Result.ok(types);
    }
}
