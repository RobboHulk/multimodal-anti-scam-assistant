import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import styles from "./TypeChart.module.css";

const CustomTooltip = ({ active, payload, totalAlerts }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const percentage = totalAlerts
      ? ((data.value / totalAlerts) * 100).toFixed(1)
      : 0;
    return (
      <div className={styles.customTooltip}>
        <div className={styles.tooltipTitle}>{data.name}</div>
        <div className={styles.tooltipContent}>
          <span className={styles.tooltipLabel}>预警数量：</span>
          <span className={styles.tooltipValue}>{data.value} 次</span>
        </div>
        <div className={styles.tooltipPercentage}>占比：{percentage}%</div>
      </div>
    );
  }
  return null;
};

// 自定义 Bar 形状组件
const CustomBar = (props) => {
  const { x, y, width, height, payload } = props;
  return (
    <rect
      x={x}
      y={y}
      width={width}
      height={height}
      fill={payload.color}
      rx={4}
      ry={4}
    />
  );
};

const TypeChart = ({ data, totalAlerts }) => {
  // 颜色数组
  const colors = [
    "#ef4444",
    "#f59e0b",
    "#10b981",
    "#3b82f6",
    "#8b5cf6",
    "#ec489a",
    "#14b8a6",
    "#f97316",
  ];

  const chartData = Object.entries(data).map(([name, value], index) => ({
    name: name,
    value: value,
    color: colors[index % colors.length],
  }));

  const total =
    totalAlerts || chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className={styles.container}>
      <div className={styles.chartWrapper}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 30 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#2d2d2d"
              vertical={false}
            />
            <XAxis
              dataKey="name"
              stroke="#888"
              tick={{ fill: "#888", fontSize: 12 }}
              angle={-15}
              textAnchor="end"
              height={60}
            />
            <YAxis
              stroke="#888"
              tick={{ fill: "#888", fontSize: 12 }}
              unit="次"
            />
            <Tooltip
              content={<CustomTooltip totalAlerts={total} />}
              cursor={{ fill: "rgba(255, 255, 255, 0.05)" }}
            />
            <Bar dataKey="value" shape={<CustomBar />} barSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className={styles.legendWrapper}>
        {chartData.map((item) => {
          // const percentage = ((item.value / total) * 100).toFixed(1);
          return (
            <div key={item.name} className={styles.legendItem}>
              <span
                className={styles.legendDot}
                style={{ backgroundColor: item.color }}
              />
              <span className={styles.legendName}>{item.name}</span>
              <span className={styles.legendValue}>{item.value}</span>
              {/* <span className={styles.legendPercent}>({percentage}%)</span> */}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TypeChart;
