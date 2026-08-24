package com.juntong.multimodalantiscamassistant.module.chat.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.juntong.multimodalantiscamassistant.module.chat.entity.ChatMessage;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatMessageMapper extends BaseMapper<ChatMessage> {
}
