// RiskTrendChart.jsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import styles from "../../pages/User/components/ReportAnalysis/ReportAnalysis.module.css";

const CustomRiskTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className={styles.riskTooltip}>
        <div className={styles.riskTooltipTitle}>{label}</div>
        <div className={styles.riskTooltipContent}>
          {/* 风险预警数行 */}
          <div className={styles.riskTooltipRow}>
            <div className={styles.tooltipLabelWithIcon}>
              <svg
                t="1774092891294"
                className={styles.tooltipWarningIcon}
                viewBox="0 0 1024 1024"
                version="1.1"
                xmlns="http://www.w3.org/2000/svg"
                p-id="16649"
                width="12"
                height="12"
              >
                <path
                  d="M454.741333 61.738667L19.968 931.413333A64 64 0 0 0 77.141333 1024h869.632a64 64 0 0 0 57.258667-92.586667L569.258667 61.696a64 64 0 0 0-114.517334 0zM512 138.069333L912.256 938.666667H111.701333L512 138.069333z"
                  fill="currentColor"
                  p-id="16650"
                ></path>
                <path
                  d="M554.666667 426.666667v213.333333a42.666667 42.666667 0 1 1-85.333334 0v-213.333333a42.666667 42.666667 0 1 1 85.333334 0zM512 725.333333a42.666667 42.666667 0 1 1 0 85.333334 42.666667 42.666667 0 0 1 0-85.333334z"
                  fill="currentColor"
                  p-id="16651"
                ></path>
              </svg>
              <span>风险预警数:</span>
            </div>
            <span className={styles.riskValue}>{data.alerts}</span>
          </div>

          {/* 高风险行 - 使用 riskDotHigh */}
          <div className={styles.riskTooltipRow}>
            <div className={styles.tooltipLabelWithDot}>
              <span className={styles.riskDotHigh}></span>
              <span>高风险:</span>
            </div>
            <span className={styles.riskHigh}>{data.highRisk || 0}</span>
          </div>

          {/* 中风险行 - 使用 riskDotMid */}
          <div className={styles.riskTooltipRow}>
            <div className={styles.tooltipLabelWithDot}>
              <span className={styles.riskDotMid}></span>
              <span>中风险:</span>
            </div>
            <span className={styles.riskMid}>{data.midRisk || 0}</span>
          </div>

          {/* 低风险行 - 使用 riskDotLow */}
          <div className={styles.riskTooltipRow}>
            <div className={styles.tooltipLabelWithDot}>
              <span className={styles.riskDotLow}></span>
              <span>低风险:</span>
            </div>
            <span className={styles.riskLow}>{data.lowRisk || 0}</span>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

const RiskTrendChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className={styles.chartPlaceholderSmall}>
        <p>暂无风险趋势数据</p>
      </div>
    );
  }

  return (
    <div className={styles.riskChartWrapper}>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 10 }}
        >
          <defs>
            <linearGradient id="purpleGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#8E76EF" />
              <stop offset="100%" stopColor="#3912D2" />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#2a2a2a"
            vertical={false}
            horizontal={true}
          />

          {/* X轴 */}
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#888", fontSize: 12 }}
          />

          {/* Y轴 */}
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#888", fontSize: 12 }}
            tickMargin={8}
            domain={[
              (dataMin) => Math.max(0, dataMin - 2),
              (dataMax) => dataMax + 2,
            ]}
          />

          {/* 自定义 Tooltip - 移除默认的白色边框 */}
          <Tooltip
            content={<CustomRiskTooltip />}
            cursor={false}
            wrapperStyle={{ outline: "none" }}
          />

          {/* 为每个日期添加垂直粗实线（去掉虚线，改为粗实线） */}
          {data.map((item, index) => (
            <ReferenceLine
              key={index}
              x={item.date}
              stroke="#3a3a3a"
              strokeWidth={6} // 粗线宽度
              // 不设置 strokeDasharray，默认就是实线
              ifOverflow="extendDomain"
            />
          ))}

          {/* 折线 */}
          <Line
            type="monotone"
            dataKey="alerts"
            stroke="url(#purpleGradient)"
            strokeWidth={3}
            dot={false}
            activeDot={{
              r: 6,
              stroke: "#fff",
              strokeWidth: 2,
              fill: "#6040DF",
            }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RiskTrendChart;
