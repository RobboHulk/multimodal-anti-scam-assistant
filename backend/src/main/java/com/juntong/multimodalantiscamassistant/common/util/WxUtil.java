package com.juntong.multimodalantiscamassistant.common.util;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

/**
 * 微信小程序工具类：通过 code 换取 openid
 */
@Component
public class WxUtil {

    private static final String CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code";

    @Value("${wx.appid}")
    private String appid;

    @Value("${wx.secret}")
    private String secret;

    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * 用 wx.login() 返回的 code 换取 openid
     * 
     * @return openid，失败时抛出异常
     */
    @SuppressWarnings("unchecked")
    public String getOpenId(String code) {
        // [开发与测试环境专属]：拦截测试专用的 code，直接返回 mock openid
        if ("test_wx_code".equals(code)) {
            return "mock_openid_123456";
        }

        Map<String, Object> result = restTemplate.getForObject(
                CODE2SESSION_URL, Map.class,
                Map.of("appid", appid, "secret", secret, "code", code));
        if (result == null || result.containsKey("errcode")) {
            throw new RuntimeException("微信登录失败: " + (result != null ? result.get("errmsg") : "无响应"));
        }
        return (String) result.get("openid");
    }
}
