// src/components/WindowSelector/WindowSelector.jsx
import { useState, useEffect } from "react";
import styles from "./WindowSelect.module.css";
import Icons from "../../../data/detectIcons";

const WindowSelect = ({ onSelect, onCancel }) => {
  const [windows, setWindows] = useState([]);
  const [selectedWindow, setSelectedWindow] = useState(null);
  const [loading, setLoading] = useState(true);

  // 模拟获取系统窗口列表
  useEffect(() => {
    // 模拟异步获取窗口列表
    const timer = setTimeout(() => {
      setWindows([
        {
          id: "wechat",
          name: "微信",
          icon: Icons.weixin,
          process: "WeChat.exe",
          status: "running",
        },
        {
          id: "qq",
          name: "QQ",
          icon: Icons.qq,
          process: "QQ.exe",
          status: "running",
        },
        {
          id: "chrome",
          name: "Chrome浏览器",
          icon: Icons.chrome,
          process: "chrome.exe",
          status: "running",
        },
        {
          id: "dingtalk",
          name: "钉钉",
          icon: Icons.dindin,
          process: "DingTalk.exe",
          status: "idle",
        },
        {
          id: "feishu",
          name: "飞书",
          icon: Icons.feishu,
          process: "Feishu.exe",
          status: "idle",
        },
      ]);
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  const handleSelect = () => {
    if (selectedWindow) {
      onSelect(selectedWindow);
    }
  };

  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        <div className={styles.header}>
          <span className={styles.icon}>{Icons.select}</span>
          <h3>选择捕获窗口</h3>
        </div>
        <div className={styles.content}>
          <p>请选择要监控的应用程序窗口，系统将实时分析其中的通信内容：</p>
          {loading ? (
            <div className={styles.loading}>
              <span className={styles.spinner}></span>
              正在扫描运行中的窗口...
            </div>
          ) : (
            <div className={styles.windowList}>
              {windows.map((win) => (
                <div
                  key={win.id}
                  className={`${styles.windowItem} ${selectedWindow?.id === win.id ? styles.selected : ""}`}
                  onClick={() => setSelectedWindow(win)}
                >
                  <span className={styles.windowIcon}>{win.icon}</span>
                  <div className={styles.windowInfo}>
                    <div className={styles.windowName}>{win.name}</div>
                    <div className={styles.windowProcess}>{win.process}</div>
                  </div>
                  <span
                    className={`${styles.windowStatus} ${styles[win.status]}`}
                  >
                    {win.status === "running" ? "运行中" : "空闲"}
                  </span>
                </div>
              ))}
            </div>
          )}
          <p className={styles.tip}>
            提示：系统将仅监控您选择的窗口，不会收集其他个人信息
          </p>
        </div>
        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={onCancel}>
            取消
          </button>
          <button
            className={`${styles.confirmBtn} ${!selectedWindow ? styles.disabled : ""}`}
            onClick={handleSelect}
            disabled={!selectedWindow}
          >
            开始监控
          </button>
        </div>
      </div>
    </div>
  );
};

export default WindowSelect;
