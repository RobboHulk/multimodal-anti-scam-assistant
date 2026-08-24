package com.juntong.multimodalantiscamassistant.module.report.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.juntong.multimodalantiscamassistant.module.report.dto.GenerateReportDTO;
import com.juntong.multimodalantiscamassistant.module.report.entity.Report;
import com.juntong.multimodalantiscamassistant.module.report.vo.ReportVO;

import java.util.List;

public interface ReportService extends IService<Report> {

    /** 生成安全监测报告，返回完整报告内容 */
    ReportVO generate(Long userId, GenerateReportDTO dto);

    /** 获取用户历史报告列表（不含详细 content） */
    List<ReportVO> listReports(Long userId);
}
