const getPastDate = (days) => {
  const date = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${month}/${day}`;
};

const MOCK_REPORT = {
  id: "EXHIBITION_MODE_REPORT",
  startDate: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10),
  endDate: new Date().toISOString().slice(0, 10),
  createdAt: "2026-04-19T09:03:51:45.762Z",
  totalAlerts: 218,
  successRate: 97.2,
  highSeverityCount: 34,
  midSeverityCount: 92,
  lowSeverityCount: 92,
  trendData: [
    { date: getPastDate(8), alerts: 28, highRisk: 5, midRisk: 12, lowRisk: 11 },
    { date: getPastDate(7), alerts: 24, highRisk: 3, midRisk: 10, lowRisk: 11 },
    { date: getPastDate(6), alerts: 31, highRisk: 6, midRisk: 13, lowRisk: 12 },
    { date: getPastDate(5), alerts: 27, highRisk: 4, midRisk: 11, lowRisk: 12 },
    { date: getPastDate(4), alerts: 35, highRisk: 7, midRisk: 15, lowRisk: 13 },
    { date: getPastDate(3), alerts: 22, highRisk: 2, midRisk: 9, lowRisk: 11 },
    { date: getPastDate(2), alerts: 29, highRisk: 5, midRisk: 12, lowRisk: 12 },
    { date: getPastDate(1), alerts: 26, highRisk: 4, midRisk: 11, lowRisk: 11 },
  ],
  changes: {
    totalAlertsChange: 20,
    highRiskChange: 3,
    guardianCountChange: 5,
    successRateChange: 3.3,
  },
  realtimeWarnings: [
    { id: 1, type: "深伪语音攻击", risk: "high", time: "2分钟前", riskLevel: "高风险" },
    { id: 2, type: "AI换脸伪造", risk: "mid", time: "15分钟前", riskLevel: "中风险" },
    { id: 3, type: "钓鱼链接注入", risk: "mid", time: "1小时前", riskLevel: "中风险" },
    { id: 4, type: "社工话术诱导", risk: "low", time: "2小时前", riskLevel: "低风险" },
    { id: 5, type: "虚假信息传播", risk: "low", time: "3小时前", riskLevel: "低风险" },
    { id: 6, type: "隐私数据泄露", risk: "mid", time: "5小时前", riskLevel: "中风险" },
  ],
  todayStats: {
    todayIntercept: 20,
    todayHighRisk: 3,
    topRiskTypes: ["深伪语音攻击", "钓鱼链接注入"],
  },
  securityScore: 91.91,
  scamTypeStats: {
    深伪语音攻击: 56,
    社工话术诱导: 41,
    钓鱼链接注入: 38,
    AI换脸伪造: 35,
    隐私数据泄露: 48,
  },
  summary:
    "系统持续为您护航，本周共防护威胁尝试 218 次，其中高风险 34 次。当前需特别警惕深伪语音攻击及社工话术诱导，您的安全我们时刻守护。",
};

export default MOCK_REPORT;
