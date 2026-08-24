package com.juntong.multimodalantiscamassistant.module.detect.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 多模态检测请求模型
 */
@Data
@Schema(description = "多模态风险检测模型")
public class DetectDTO {

    @Schema(description = "待检测的文本内容 (如聊天记录、短信、网页正文)", example = "恭喜您中奖了，请点击链接领取：http://xxx.cn")
    private String text;

    @Schema(description = "待检测的文件地址 (如转账截图、诈骗语音等)", example = "http://example.com/oss/scam_call.mp3")
    private String fileUrl;
}
