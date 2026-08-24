package com.juntong.multimodalantiscamassistant.common.ml;

/**
 * ML 服务调用接口
 * 真实实现：HTTP 调用 http://ml-service/api/chat/send
 * Mock 实现：返回固定测试数据（ML 接口未就绪时使用）
 */
public interface MlServiceClient {

    MlPredictResult predict(MlPredictRequest request);

    void triggerVectorize(String filePath);
}
