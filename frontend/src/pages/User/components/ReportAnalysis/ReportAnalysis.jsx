import { useOutletContext } from "react-router-dom";
import { useState, useRef, useEffect, useMemo } from "react";
import styles from "./ReportAnalysis.module.css";
import RiskChart from "../../../../components/RiskChart/RiskChart";
import ScoreSvg from "../../../../components/ScoreSvg/ScoreSvg";
import TypeChart from "../../../../components/TypeChart/TypeChart";
import Icons from "../../../../data/pageIcons";
import MOCK_REPORT from "./mockReport";

const ReportAnalysis = () => {
  const { userData } = useOutletContext();
  const fileInputRef = useRef(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [riskTrendData, setRiskTrendData] = useState(null);
  const [showScoreExplain, setShowScoreExplain] = useState(false);
  const explainRef = useRef(null);
  const explainCardRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!showScoreExplain) return;

      const isClickInsideExplain = explainRef.current?.contains(event.target);
      const isClickInsideCard = explainCardRef.current?.contains(event.target);

      if (!isClickInsideExplain && !isClickInsideCard) {
        setShowScoreExplain(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showScoreExplain]);

  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        // 即使没登录或没数据，也展示 Mock 数据用于“展示效果”
        if (!token) {
          setReportData(MOCK_REPORT);
          setRiskTrendData(MOCK_REPORT.trendData); // 添加这行
          return;
        }

        const res = await fetch("/api/report/list", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const json = await res.json();
        if (json.code === 200 && json.data && json.data.length > 0) {
          const data = json.data[0];
          setReportData(data);
          setRiskTrendData(data.trendData || MOCK_REPORT.trendData); // 添加这行
        } else {
          setReportData(MOCK_REPORT);
          setRiskTrendData(MOCK_REPORT.trendData); // 添加这行
        }
      } catch (err) {
        setReportData(MOCK_REPORT);
        setRiskTrendData(MOCK_REPORT.trendData); // 添加这行
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith(".json")) {
      alert("请上传 JSON 格式的报告文件");
      event.target.value = "";
      return;
    }

    setUploadFile(file);
    setLoading(true);

    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const fileContent = e.target.result;
        const importedData = JSON.parse(fileContent);

        console.log("导入的JSON数据:", importedData);

        const reportDataFromFile = {
          ...MOCK_REPORT,
          ...importedData,
          id: "UPLOADED_" + Date.now(),
          name:
            importedData.name ||
            importedData.reportInfo?.name ||
            file.name.replace(".json", ""),
          sourceFile: file.name,
          importedAt: new Date().toISOString(),

          scamTypeStats:
            importedData.scamTypeStats || MOCK_REPORT.scamTypeStats,
        };

        setReportData(reportDataFromFile);

        setRiskTrendData(reportDataFromFile.trendData || MOCK_REPORT.trendData);

        console.log("文件导入成功");
      } catch (error) {
        console.error("JSON解析失败:", error);
        alert(`JSON文件解析失败: ${error.message}\n请确保文件格式正确。`);
      } finally {
        setLoading(false);
      }
    };

    reader.onerror = () => {
      console.error("文件读取失败");
      alert("文件读取失败，请重试");
      setLoading(false);
    };

    reader.readAsText(file, "UTF-8");

    event.target.value = "";
  };

  const handleImportClick = () => {
    fileInputRef.current.click();
  };

  const getScoreLevel = (score) => {
    if (score >= 80) return "优秀";
    if (score >= 60) return "良好";
    if (score >= 40) return "待改进";
    return "危险";
  };

  const getLevelClass = (score) => {
    if (score >= 80) return "levelExcellent";
    if (score >= 60) return "levelGood";
    if (score >= 40) return "levelWarning";
    return "levelDanger";
  };

  const getLevelText = (score) => {
    if (score >= 80) return "安全状况良好，继续保持！";
    if (score >= 60) return "存在一定风险，建议加强反诈教育。";
    if (score >= 40) return "风险较高，建议立即采取防护措施。";
    return "安全状况危急，高风险预警数量激增，需紧急介入处理。";
  };

  const handleExportReport = () => {
    if (!reportData) {
      console.warn("没有可导出的报告数据");
      return;
    }

    try {
      const mdLines = [
        `# 安全防护报告`,
        ``,
        `**报告ID:** ${reportData.id || "N/A"}`,
        `**时间范围:** ${reportData.startDate || ""} ~ ${reportData.endDate || ""}`,
        `**生成时间:** ${new Date().toLocaleString("zh-CN")}`,
        ``,
        `## 核心指标`,
        ``,
        `| 指标 | 数值 |`,
        `|------|------|`,
        `| 安全评分 | ${reportData?.securityScore || 0} |`,
        `| 累计防护量 | ${reportData.totalAlerts || 0} |`,
        `| 防护成功率 | ${reportData.successRate || 0}% |`,
        `| 高风险事件 | ${reportData.highSeverityCount || 0} |`,
        ``,
        `## 威胁类型分布`,
        ``,
        ...(reportData.scamTypeStats
          ? Object.entries(reportData.scamTypeStats).map(([k, v]) => `- ${k}: ${v}`)
          : ["暂无数据"]),
        ``,
        `## 总结`,
        ``,
        reportData.summary || "暂无总结",
      ];

      const mdStr = mdLines.join("\n");
      const dataBlob = new Blob([mdStr], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `security_report_${new Date().toISOString().slice(0, 10)}.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      console.log("报告导出成功");
    } catch (error) {
      console.error("导出报告失败:", error);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.info}>
          <h1 className={styles.title}>HELLO {userData?.nickname || "用户"}</h1>
        </div>
        <div className={styles.import}>
          <button className={styles.importBtn} onClick={handleImportClick}>
            <span className={styles.importText}>import report</span>
            <span className={styles.importIcon}>{Icons.dircSign}</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.doc,.docx,.txt,.json,.xlsx,.xls"
              style={{ display: "none" }}
              onChange={handleFileUpload}
            />
          </button>
        </div>
      </header>
      <div className={styles.content}>
        {/* 加载状态 */}
        {loading && (
          <div className={styles.card}>
            <div className={styles.loadingWrapper}>
              <p>正在分析报告...</p>
            </div>
          </div>
        )}

        {/* 无数据状态 */}
        {!loading && !reportData && (
          <>
            <div className={styles.card}>
              <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>
                  {Icons.noReport}
                  <span>暂无报告数据</span>
                </div>
                <p>点击右上角导入报告文件</p>
              </div>
            </div>
          </>
        )}

        {/* 有数据时显示内容 */}
        {!loading && reportData && (
          <>
            <div className={styles.stats}>
              <div className={`${styles.statsCard} ${styles.all}`}>
                <span className={styles.statsIcon}>
                  {Icons.totalInterceptions}
                </span>
                <div className={styles.statsInfo}>
                  <span className={styles.statsData}>
                    {reportData.totalAlerts || 0}
                  </span>
                  <span className={styles.statsClass}>累计防护量</span>
                </div>
                <div className={styles.statsAnalysis}>
                  <div className={styles.statsChange}>
                    <span className={styles.analyIcon}>{Icons.dataLabel}</span>
                    <span className={styles.changeData}>
                      {reportData?.changes?.totalAlertsChange || 20}
                    </span>
                  </div>
                  <span className={styles.analyTime}>last 1 month</span>
                </div>
              </div>

              <div className={`${styles.statsCard} ${styles.high}`}>
                <span className={styles.statsIcon}>{Icons.highRisk}</span>
                <div className={styles.statsInfo}>
                  <span className={styles.statsData}>
                    {reportData.highSeverityCount || 0}
                  </span>
                  <span className={styles.statsClass}>高风险预警</span>
                </div>
                <div className={styles.statsAnalysis}>
                  <div className={styles.statsChange}>
                    <span className={styles.analyIcon}>{Icons.dataLabel}</span>
                    <span className={styles.changeData}>
                      {reportData?.changes?.highRiskChange || 3}
                    </span>
                  </div>
                  <span className={styles.analyTime}>last 1 month</span>
                </div>
              </div>

              <div className={`${styles.statsCard} ${styles.protect}`}>
                <span className={styles.statsIcon}>{Icons.guardianCount}</span>
                <div className={styles.statsInfo}>
                  <span className={styles.statsData}>
                    {userData?.guardianCount || 128}
                  </span>
                  <span className={styles.statsClass}>守护天数</span>
                </div>
                <div className={styles.statsAnalysis}>
                  <div className={styles.statsChange}>
                    <span className={styles.analyIcon}>{Icons.dataLabel}</span>
                    <span className={styles.changeData}>
                      {reportData?.changes?.guardianCountChange || 3}
                    </span>
                  </div>
                  <span className={styles.analyTime}>last 1 month</span>
                </div>
              </div>

              <div className={`${styles.statsCard} ${styles.success}`}>
                <span className={styles.statsIcon}>{Icons.successRate}</span>
                <div className={styles.statsInfo}>
                  <span className={styles.statsData}>
                    {" "}
                    {reportData?.successRate || 97.2}%
                  </span>
                  <span className={styles.statsClass}>防护成功率</span>
                </div>
                <div className={styles.statsAnalysis}>
                  <div className={styles.statsChange}>
                    <span className={styles.analyIcon}>{Icons.dataLabel}</span>
                    <span className={styles.changeData}>
                      {reportData?.changes?.successRateChange || 3.3}%
                    </span>
                  </div>
                  <span className={styles.analyTime}>last 1 month</span>
                </div>
              </div>
            </div>
            <div className={`${styles.row}`}>
              <div className={`${styles.rowCard} ${styles.recent}`}>
                <div className={styles.cardHeader}>
                  <h1 className={styles.cardTitle}>近几天风险趋势</h1>
                  <div className={styles.riskStats}>
                    <div className={styles.riskStat}>
                      <span className={styles.riskDotHigh}></span>
                      <span>高风险</span>
                      <span className={styles.riskStatValue}>
                        {reportData.highSeverityCount || 0}
                      </span>
                    </div>
                    <div className={styles.riskStat}>
                      <span className={styles.riskDotMid}></span>
                      <span>中风险</span>
                      <span className={styles.riskStatValue}>
                        {reportData.midSeverityCount || 0}
                      </span>
                    </div>
                    <div className={styles.riskStat}>
                      <span className={styles.riskDotLow}></span>
                      <span>低风险</span>
                      <span className={styles.riskStatValue}>
                        {reportData.lowSeverityCount || 0}
                      </span>
                    </div>
                    <div className={styles.riskStat}>
                      {Icons.riskStatTotal}
                      <span>总计</span>
                      <span className={styles.riskStatValue}>
                        {reportData.totalAlerts || 0}
                      </span>
                    </div>
                  </div>
                </div>
                <RiskChart
                  data={
                    riskTrendData ||
                    reportData?.trendData ||
                    MOCK_REPORT.trendData
                  }
                />
              </div>
              <div className={`${styles.rowCard} ${styles.today}`}>
                <div className={styles.cardHeader}>
                  <h1 className={styles.cardTitle}>实时监控</h1>
                </div>
                <div className={styles.cardMain}>
                  <div className={styles.todayWarning}>
                    {reportData?.realtimeWarnings?.map((warning, idx) => (
                      <div key={warning.id} className={styles.warnItem}>
                        <div className={styles.itemLeft}>
                          <span className={styles.warnIndex}>{idx + 1}</span>
                          <span className={styles.warnClass}>
                            {warning.type}
                          </span>
                        </div>
                        <div className={styles.itemRight}>
                          <span
                            className={`${styles.warnRisk} ${styles[warning.risk]}`}
                          >
                            {warning.riskLevel}
                          </span>
                          <span className={styles.warnTime}>
                            {warning.time}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className={styles.todayTotal}>
                    <div
                      className={`${styles.todayAll} ${styles.todayTotalItem}`}
                    >
                      <span>
                        <span>今日防护:</span>
                        <span className={styles.todayAllNum}>
                          {" "}
                          {reportData?.todayStats?.todayIntercept || 20}
                        </span>
                      </span>
                      <span
                        className={`${styles.todayAllIcon} ${styles.todayIcon}`}
                      >
                        {Icons.todayRiskTotalUp}
                      </span>
                    </div>
                    <div
                      className={`${styles.todayHigh} ${styles.todayTotalItem}`}
                    >
                      <span>
                        <span>高危预警:</span>
                        <span className={styles.todayHighNum}>
                          {" "}
                          {reportData?.todayStats?.todayHighRisk || 3}
                        </span>
                      </span>
                      <span
                        className={`${styles.todayHighIcon} ${styles.todayIcon}`}
                      >
                        {Icons.todayRiskTotalDown}
                      </span>
                    </div>
                  </div>
                  <div className={styles.todayAnalys}>
                    <span>易犯风险：</span>
                    {reportData?.todayStats?.topRiskTypes?.map((type, idx) => (
                      <span key={idx}>
                        {type}
                        {idx < reportData.todayStats.topRiskTypes.length - 1 &&
                          " "}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className={`${styles.row}`}>
              <div className={`${styles.rowCard} ${styles.class}`}>
                <div className={styles.cardHeader}>
                  <h1 className={styles.cardTitle}>威胁类型</h1>
                </div>
                <div className={styles.cardMain}>
                  <TypeChart data={reportData.scamTypeStats} />
                </div>
              </div>
              <div className={`${styles.rowCard} ${styles.score}`}>
                <div className={styles.cardHeader}>
                  <h1 className={styles.cardTitle}>安全指数</h1>
                  <div
                    ref={explainRef}
                    className={styles.explain}
                    onClick={() => setShowScoreExplain(!showScoreExplain)}
                  >
                    ?
                  </div>
                  {showScoreExplain && (
                    <div
                      className={styles.scoreExplainCard}
                      ref={explainCardRef}
                    >
                      <div className={styles.explainContent}>
                        安全指数基于
                        <span className={styles.emphasis}>累计防护量</span>、
                        <span className={styles.emphasis}>
                          高/中/低风险预警数量
                        </span>
                        、<span className={styles.emphasis}>预警事件类型</span>
                        等核心数据综合计算得出。
                      </div>
                      <span
                        className={styles.closeBtn}
                        onClick={() => setShowScoreExplain(false)}
                      >
                        <svg
                          t="1774101101972"
                          class="icon"
                          viewBox="0 0 1024 1024"
                          version="1.1"
                          xmlns="http://www.w3.org/2000/svg"
                          p-id="26047"
                          width="16"
                          height="16"
                        >
                          <path
                            d="M548.992 503.744L885.44 167.328a31.968 31.968 0 1 0-45.248-45.248L503.744 458.496 167.328 122.08a31.968 31.968 0 1 0-45.248 45.248l336.416 336.416L122.08 840.16a31.968 31.968 0 1 0 45.248 45.248l336.416-336.416L840.16 885.44a31.968 31.968 0 1 0 45.248-45.248L548.992 503.744z"
                            fill="currentColor"
                            p-id="26048"
                          ></path>
                        </svg>
                      </span>
                    </div>
                  )}
                </div>
                <div className={styles.cardMain}>
                  <div className={styles.scoreSvgBox}>
                    <ScoreSvg
                      score={
                        reportData?.securityScore || MOCK_REPORT.securityScore
                      }
                      className={styles.scoreSvg}
                    />
                    <div className={styles.scoreDetail}>
                      <div className={styles.scoreLow}>0%</div>
                      <div className={styles.scoreMid}>
                        <div className={styles.scoreNum}>
                          {reportData?.securityScore ||
                            MOCK_REPORT.securityScore}
                          %
                        </div>
                        <div className={styles.numExplain}>
                          Based on Reports
                        </div>
                      </div>
                      <div className={styles.scoreHigh}>100%</div>
                    </div>
                  </div>
                  <div className={styles.scoreLine}></div>
                  <div className={styles.scoreAdvice}>
                    <div className={styles.scoreSummary}>
                      <span
                        className={`${styles.levelTag} ${styles[getLevelClass(reportData?.securityScore || MOCK_REPORT.securityScore)]}`}
                      >
                        {getScoreLevel(
                          reportData?.securityScore ||
                            MOCK_REPORT.securityScore,
                        )}
                      </span>
                      <div className={styles.summaryText}>
                        {getLevelText(
                          reportData?.securityScore ||
                            MOCK_REPORT.securityScore,
                        )}
                      </div>
                    </div>
                    <div className={styles.reportSummary}>
                      <div className={styles.summaryContent}>
                        <div className={styles.summaryLabel}>
                          <span className={styles.sumIcon}>
                            {Icons.summaryLabel}
                          </span>
                          <span>报告摘要：</span>
                        </div>
                        <div className={styles.summaryTextContent}>
                          {reportData?.summary || "暂无摘要信息"}
                        </div>
                      </div>

                      <div className={styles.exportBtnWrapper}>
                        <button
                          className={styles.exportBtn}
                          onClick={handleExportReport}
                        >
                          <span className={styles.exportText}>
                            export report
                          </span>
                          <span className={styles.exportIcon}>
                            {Icons.dircSign}
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportAnalysis;
