package com.juntong.multimodalantiscamassistant.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.io.File;

/**
 * WebMVC 配置：将 HTTP url 路由至本地存储存放路径，使其可作为静态资源被公开访问
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Value("${file.upload-dir:./uploads/}")
    private String uploadDir;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 获取本地文件夹绝对路径
        File dir = new File(uploadDir);
        if (!dir.exists()) {
            dir.mkdirs();
        }
        String path = dir.getAbsolutePath();
        if (!path.endsWith(File.separator)) {
            path += File.separator;
        }

        // 当访问 /uploads/** 时，实际去本地磁盘提取文件
        // 支持类似 http://localhost:8888/uploads/a.png -> ./uploads/a.png
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations("file:" + path);
    }
}
