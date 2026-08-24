package com.juntong.multimodalantiscamassistant.module.detect.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

@Data
@Schema(description = "批量自动化测评请求模型")
public class BatchDetectDTO {
    @Schema(description = "自动化测评数据集列表")
    private List<BatchDetectItemDTO> items;
}
