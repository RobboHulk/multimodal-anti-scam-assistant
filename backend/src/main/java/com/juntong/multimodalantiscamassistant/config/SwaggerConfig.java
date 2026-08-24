package com.juntong.multimodalantiscamassistant.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Swagger / OpenAPI 文档配置
 * 访问地址：http://localhost:8080/swagger-ui/index.html
 */
@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI openAPI() {
        // 定义 Bearer Token 认证方案
        String schemeName = "BearerAuth";
        return new OpenAPI()
                .info(new Info()
                        .title("多模态反诈智能助手 API")
                        .description("后端接口文档，含用户、监护人、预警、报告等模块")
                        .version("1.0.0"))
                .addSecurityItem(new SecurityRequirement().addList(schemeName))
                .components(new Components()
                        .addSecuritySchemes(schemeName, new SecurityScheme()
                                .name(schemeName)
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")));
    }
}
