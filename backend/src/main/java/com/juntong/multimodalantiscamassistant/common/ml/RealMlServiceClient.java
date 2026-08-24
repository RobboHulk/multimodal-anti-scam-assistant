package com.juntong.multimodalantiscamassistant.common.ml;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Primary;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Primary
@Component
public class RealMlServiceClient implements MlServiceClient {

    @Value("${ml.service.url:http://anti-scam-ml:8000}")
    private String mlServiceUrl;

    private final RestTemplate restTemplate;

    public RealMlServiceClient() {
        var factory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(10_000);
        factory.setReadTimeout(120_000);
        this.restTemplate = new RestTemplate(factory);
    }

    @Override
    public MlPredictResult predict(MlPredictRequest request) {
        String url = mlServiceUrl + "/api/chat/send";
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<MlPredictRequest> entity = new HttpEntity<>(request, headers);
        
        try {
            log.info("Calling ML service at: {}, payload: {}", url, request);
            ResponseEntity<MlPredictResult> response = restTemplate.postForEntity(url, entity, MlPredictResult.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                log.info("ML service response: {}", response.getBody());
                return response.getBody();
            } else {
                log.error("ML service returned error status: {}, body: {}", response.getStatusCode(), response.getBody());
            }
        } catch (Exception e) {
            log.error("Failed to call ML service at " + url, e);
        }
        
        // Return a default low-risk result if ML service is down or error occurs
        MlPredictResult fallback = new MlPredictResult();
        fallback.setChatType(0);
        fallback.setRiskScore(0.0);
        fallback.setScamType("OTHER_UNKNOWN");
        fallback.setConfidence(0.0);
        fallback.setRiskAction("SAFE");
        fallback.setReport("");
        fallback.setChatResponse("ML 服务访问异常，已采取安全兜底逻辑。");
        return fallback;
    }

    @Override
    public void triggerVectorize(String filePath) {
        String url = mlServiceUrl + "/api/vectorize";
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        // As an example, sending JSON with the filePath
        String jsonPayload = "{\"file_path\":\"" + filePath.replace("\\", "\\\\") + "\"}";
        HttpEntity<String> entity = new HttpEntity<>(jsonPayload, headers);
        
        try {
            log.info("Triggering vectorization at ML service: {}, filePath: {}", url, filePath);
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("Vectorization triggered successfully.");
            } else {
                log.error("Vectorization trigger returned error status: {}, body: {}", response.getStatusCode(), response.getBody());
            }
        } catch (Exception e) {
            log.error("Failed to trigger vectorization at " + url, e);
        }
    }
}
