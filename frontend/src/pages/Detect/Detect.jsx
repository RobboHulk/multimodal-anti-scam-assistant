import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../../layouts/Nav/Nav";
import AiChatPanel from "./AiChatPanel";
import styles from "./Detect.module.css";

const HISTORY_KEY = "veritide_detect_history";

const ProcessPanel = ({ process }) => {
  const phaseOrder = ["idle", "ready", "privacy", "uploading", "analysis", "audit", "complete"];
  const phaseIndex = phaseOrder.indexOf(process.phase);
  const stages = [
    { key: "privacy", title: "隐私预检", detail: "本地OCR、规则校验与字段脱敏" },
    { key: "uploading", title: "材料解析", detail: "识别媒体、链接与文件对象" },
    { key: "analysis", title: "协同核验", detail: "专项模型与安全工具并行" },
    { key: "audit", title: "结论审计", detail: "逐项检查证据引用与边界" },
  ];
  const agents = [
    { name: "内容鉴真", tone: "violet" },
    { name: "网络威胁", tone: "cyan" },
    { name: "认知诱导", tone: "amber" },
    { name: "研判协调", tone: "blue" },
  ];
  const stageState = (key) => {
    const index = phaseOrder.indexOf(key);
    if (process.phase === "complete" || phaseIndex > index) return "done";
    if (process.phase === key || (key === "analysis" && process.phase === "audit")) return "running";
    return "pending";
  };

  return (
    <aside className={styles.processPanel}>
      <div className={styles.processHeader}>
        <div>
          <h2>智能体协同</h2>
          <span className={styles.processStatus}>
            <i className={process.phase === "idle" ? "" : styles.statusOn} />
            {process.label}
          </span>
        </div>
        <Link className={styles.detailLink} to="/analysis">查看详情</Link>
      </div>

      <section className={styles.gateCard}>
        <div className={styles.cardHeading}>
          <h3>研判路径</h3>
          <span>{process.materialCount || 0} 份材料</span>
        </div>
        <div className={styles.gateTrack}>
          {["快速检查", "工具核验", "深度研判"].map((item, index) => (
            <div
              className={[styles.gateStep, index === 1 && phaseIndex >= 2 ? styles.gateActive : ""].filter(Boolean).join(" ")}
              key={item}
            >
              <span>{index + 1}</span>
              <strong>{item}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.stageList}>
        {stages.map((stage) => {
          const state = stageState(stage.key);
          return (
            <div className={[styles.stageItem, styles[state]].join(" ")} key={stage.key}>
              <div className={styles.stageMarker}>{state === "done" ? "✓" : ""}</div>
              <div className={styles.stageText}>
                <strong>{stage.title}</strong>
                <span>{stage.detail}</span>
              </div>
              <span className={styles.stageTag}>
                {state === "done" ? "完成" : state === "running" ? "处理中" : "待处理"}
              </span>
            </div>
          );
        })}
      </section>

      <section className={styles.agentSection}>
        <div className={styles.cardHeading}>
          <h3>协同角色</h3>
          <span>受控调用</span>
        </div>
        <div className={[styles.agentOrbit, phaseIndex >= 4 ? styles.agentOrbitActive : ""].filter(Boolean).join(" ")}>
          <div className={styles.agentCore}><strong>证据门控</strong><span>{phaseIndex >= 4 ? "协调中" : "待命"}</span></div>
          <i className={styles.orbitOne}>真</i><i className={styles.orbitTwo}>网</i><i className={styles.orbitThree}>意</i>
        </div>
        <div className={styles.agentGrid}>
          {agents.map((agent, index) => {
            const working = phaseIndex >= 4 && process.phase !== "complete";
            const done = process.phase === "complete";
            return (
              <div className={styles.agentCard} key={agent.name}>
                <i className={styles[agent.tone]} />
                <span>{agent.name}</span>
                <b>{done ? "完成" : working && index < 3 ? "运行" : "待命"}</b>
              </div>
            );
          })}
        </div>
      </section>

      <div className={styles.processFooter}>
        <div><span>证据</span><strong>{process.phase === "complete" ? 18 : 0}</strong></div>
        <div><span>工具调用</span><strong>{process.phase === "complete" ? 7 : 0}</strong></div>
        <div><span>冲突</span><strong>{process.phase === "complete" ? 1 : 0}</strong></div>
      </div>
    </aside>
  );
};

const Detect = () => {
  const [chatHistory, setChatHistory] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
      return Array.isArray(saved) ? saved : [];
    } catch {
      return [];
    }
  });
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [process, setProcess] = useState({ phase: "idle", label: "等待材料", materialCount: 0 });
  const chatRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(chatHistory));
  }, [chatHistory]);

  const handleNewSession = () => {
    setActiveHistoryId(null);
    setProcess({ phase: "idle", label: "等待材料", materialCount: 0 });
    chatRef.current?.reset();
  };

  const handleSelectHistory = (item) => {
    setActiveHistoryId(item.id);
    chatRef.current?.loadMessages(item.messages || []);
    setProcess({
      phase: item.messages?.length ? "complete" : "idle",
      label: item.messages?.length ? "研判完成" : "等待材料",
      materialCount: item.materialCount || 0,
    });
  };

  const handleSaveToHistory = useCallback((text, messages, materialCount = 0) => {
    setChatHistory((current) => {
      if (activeHistoryId) {
        return current.map((item) =>
          item.id === activeHistoryId
            ? { ...item, messages, materialCount, updatedAt: Date.now() }
            : item,
        );
      }
      const id = "hist-" + Date.now();
      setActiveHistoryId(id);
      return [{
        id,
        title: text.slice(0, 24) || "多模态材料研判",
        messages,
        materialCount,
        updatedAt: Date.now(),
      }, ...current];
    });
  }, [activeHistoryId]);

  const sortedHistory = useMemo(
    () => [...chatHistory].sort((a, b) => b.updatedAt - a.updatedAt),
    [chatHistory],
  );

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleDateString("zh-CN", { month: "numeric", day: "numeric" });
  };

  return (
    <div className={styles.page}>
      <Nav />
      <div className={styles.workspace}>
        <aside className={[styles.sessionSidebar, sidebarOpen ? "" : styles.sidebarCollapsed].filter(Boolean).join(" ")}>
          <div className={styles.sessionTop}>
            <button type="button" className={styles.newSession} onClick={handleNewSession}>
              <span>＋</span>新建研判
            </button>
            <button type="button" className={styles.collapseButton} onClick={() => setSidebarOpen(false)} aria-label="收起会话">
              ‹
            </button>
          </div>
          <div className={styles.sessionLabel}>最近研判</div>
          <div className={styles.sessionList}>
            {sortedHistory.length === 0 ? (
              <div className={styles.sessionEmpty}>
                <div className={styles.emptyOrbit}><i /><i /><i /></div>
                <strong>暂无研判记录</strong>
                <span>提交文字或材料后，记录会保存在这里</span>
              </div>
            ) : sortedHistory.map((item) => (
              <button
                type="button"
                className={[styles.sessionItem, activeHistoryId === item.id ? styles.sessionActive : ""].filter(Boolean).join(" ")}
                key={item.id}
                onClick={() => handleSelectHistory(item)}
              >
                <span className={styles.sessionDot} />
                <span className={styles.sessionName}>{item.title}</span>
                <small>{formatTime(item.updatedAt)}</small>
              </button>
            ))}
          </div>
          <section className={styles.sidebarSafety}>
            <div className={styles.safetyHeading}><i>盾</i><span><strong>本地隐私预检</strong><small>材料离开设备前执行</small></span><b>已开启</b></div>
            <div className={styles.safetyTech}><span>本地OCR</span><span>规则校验</span><span>字段脱敏</span><span>EXIF清理</span></div>
            <p>手机号、身份证号和验证码默认遮蔽；URL与域名保留用于威胁核验。</p>
          </section>
        </aside>

        <main className={styles.chatWorkspace}>
          {!sidebarOpen && (
            <button type="button" className={styles.expandButton} onClick={() => setSidebarOpen(true)}>
              展开会话
            </button>
          )}
          <AiChatPanel
            ref={chatRef}
            onSaveHistory={handleSaveToHistory}
            onProcessChange={setProcess}
          />
        </main>

        <ProcessPanel process={process} />
      </div>
    </div>
  );
};

export default Detect;
