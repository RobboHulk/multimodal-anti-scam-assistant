package com.juntong.multimodalantiscamassistant.module.detect.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@Schema(description = "批量测评数据项模型")
public class BatchDetectItemDTO extends DetectDTO {

    @Schema(description = "预期结果标签: 1=诈骗(黑样本), 0=正常(白样本)", example = "1")
    private Integer expectedIsScam;
}
