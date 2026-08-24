package com.juntong.multimodalantiscamassistant.module.knowledge.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.juntong.multimodalantiscamassistant.module.knowledge.entity.KnowledgeArticle;
import com.juntong.multimodalantiscamassistant.module.knowledge.mapper.KnowledgeArticleMapper;
import com.juntong.multimodalantiscamassistant.module.knowledge.service.IKnowledgeArticleService;
import org.springframework.stereotype.Service;

@Service
public class KnowledgeArticleServiceImpl extends ServiceImpl<KnowledgeArticleMapper, KnowledgeArticle> implements IKnowledgeArticleService {
}
