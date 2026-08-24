package com.juntong.multimodalantiscamassistant;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import(com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration.class)
@MapperScan("com.juntong.multimodalantiscamassistant.module.*.mapper")
public class MultimodalAntiScamAssistantApplication {

    public static void main(String[] args) {
        SpringApplication.run(MultimodalAntiScamAssistantApplication.class, args);
    }

}
