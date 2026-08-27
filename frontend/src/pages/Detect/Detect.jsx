import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Nav from "../../layouts/Nav/Nav";
import AiChatPanel from "./AiChatPanel";
import styles from "./Detect.module.css";

const HISTORY_KEY = "veritide_detect_history";

const ProcessPanel = ({ process }) => {
  const phaseOrder = ["idle", "ready", "privacy", "uploading", "analysis", "audit", "synthesis", "complete"];
  const phaseIndex = phaseOrder.indexOf(process.phase);
  const stages = [
    { key: "privacy", title: "本地安全预检", detail: "OCR识别、字段掩码与EXIF清理" },
    { key: "uploading", title: "多模态材料解析", detail: "固定图像、音频、视频与链接对象" },
    { key: "analysis", title: "专项能力并行核验", detail: "鉴真、威胁与诱导分析同步执行" },
    { key: "audit", title: "证据约束审计", detail: "回指证据、处理冲突并标注边界" },
    { key: "synthesis", title: "生成可回溯回复", detail: "组织结论、依据、边界与处置建议" },
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
  const progressNumbers = phaseIndex >= 7
    ? { evidence: 18, tools: 7, conflicts: 1 }
    : phaseIndex >= 5
      ? { evidence: 18, tools: 7, conflicts: 1 }
      : phaseIndex >= 4
        ? { evidence: 11, tools: 6, conflicts: 0 }
        : phaseIndex >= 3
          ? { evidence: 4, tools: 2, conflicts: 0 }
          : phaseIndex >= 2
            ? { evidence: 1, tools: 1, conflicts: 0 }
            : { evidence: 0, tools: 0, conflicts: 0 };
  const resultReady = phaseIndex >= 4;
  const progressPercent = [0, 6, 15, 32, 61, 82, 94, 100][Math.max(0, phaseIndex)] || 0;
  const gateIndex = phaseIndex < 2 ? -1 : phaseIndex < 4 ? 0 : phaseIndex < 5 ? 1 : 2;
  const currentStage = stages.find((stage) => stage.key === process.phase);
  const agentState = (index) => {
    if (process.phase === "complete") return "完成";
    if (process.phase === "analysis" && index < 3) return "运行";
    if ((process.phase === "audit" || process.phase === "synthesis") && index === 3) return "运行";
    if (phaseIndex > 4 && index < 3) return "完成";
    return "待命";
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

      <section className={[styles.processMonitor, phaseIndex >= 2 && process.phase !== "complete" ? styles.monitorRunning : ""].filter(Boolean).join(" ")}>
        <div className={styles.progressDial} style={{ "--progress": `${progressPercent * 3.6}deg` }}>
          <div><strong>{progressPercent}</strong><span>%</span></div>
        </div>
        <div className={styles.monitorCopy}>
          <span>{process.phase === "complete" ? "本次任务已闭环" : currentStage?.title || "等待发起任务"}</span>
          <strong>{process.phase === "complete" ? "证据与报告均已归档" : currentStage?.detail || "提交材料后显示实时处理状态"}</strong>
          <div className={styles.signalBars}>{[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((item) => <i key={item} />)}</div>
        </div>
      </section>

      <section className={styles.gateCard}>
        <div className={styles.cardHeading}>
          <h3>深度分析路径</h3>
          <span className={phaseIndex >= 2 ? styles.deepPathOn : ""}>✦ {phaseIndex >= 2 ? "运行中" : "待启动"}</span>
        </div>
        <div className={styles.gateTrack}>
          {["快速检查", "工具核验", "深度研判"].map((item, index) => (
            <div
              className={[styles.gateStep, index === gateIndex ? styles.gateActive : "", index < gateIndex ? styles.gateDone : ""].filter(Boolean).join(" ")}
              key={item}
            >
              <span>{index + 1}</span>
              <strong>{item}</strong>
            </div>
          ))}
        </div>
        <div className={styles.materialStrip}>
          <span><i>图</i>资质证明<b>{process.materialCount ? "已识别" : "等待"}</b></span>
          <span><i>音</i>通话录音<b>{process.materialCount > 1 ? "已识别" : "等待"}</b></span>
          <span><i>视</i>案例视频<b>{process.materialCount > 2 ? "已识别" : "等待"}</b></span>
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

      <section className={styles.liveProducts}>
        <div className={styles.cardHeading}><h3>实时证据产物</h3><span>{resultReady ? "持续回写" : "等待核验"}</span></div>
        <div className={resultReady ? styles.productReady : ""}><i className={styles.violet} /><span><strong>图像局部定位</strong><small>人物边界 · 印章 · 编号</small></span><b>{resultReady ? "3 区域" : "—"}</b></div>
        <div className={resultReady ? styles.productReady : ""}><i className={styles.cyan} /><span><strong>音频异常区间</strong><small>谐波 · 相位 · 韵律</small></span><b>{resultReady ? "00:08—00:13" : "—"}</b></div>
        <div className={phaseIndex >= 5 ? styles.productReady : ""}><i className={styles.amber} /><span><strong>链接威胁对象</strong><small>主体不符 · 凭据表单</small></span><b>{phaseIndex >= 5 ? "高风险" : "—"}</b></div>
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
            const state = agentState(index);
            return (
              <div className={[styles.agentCard, state === "运行" ? styles.agentWorking : "", state === "完成" ? styles.agentDone : ""].filter(Boolean).join(" ")} key={agent.name}>
                <i className={styles[agent.tone]} />
                <span>{agent.name}</span>
                <b>{state}</b>
              </div>
            );
          })}
        </div>
      </section>

      <div className={styles.processFooter}>
        <div><span>证据</span><strong>{progressNumbers.evidence}</strong></div>
        <div><span>工具调用</span><strong>{progressNumbers.tools}</strong></div>
        <div><span>冲突</span><strong>{progressNumbers.conflicts}</strong></div>
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

  const handleDeleteHistory = (event, id) => {
    event.stopPropagation();
    setChatHistory((current) => current.filter((item) => item.id !== id));
    if (activeHistoryId === id) {
      setActiveHistoryId(null);
      setProcess({ phase: "idle", label: "等待材料", materialCount: 0 });
      chatRef.current?.reset();
    }
  };

  const handleSaveToHistory = useCallback((text, messages, materialCount = 0) => {
    if (activeHistoryId) {
      setChatHistory((current) => current.map((item) =>
        item.id === activeHistoryId
          ? { ...item, messages, materialCount, updatedAt: Date.now() }
          : item,
      ));
      return;
    }
    const id = "hist-" + Date.now();
    setActiveHistoryId(id);
    setChatHistory((current) => [{
      id,
      title: text.slice(0, 24) || "多模态材料研判",
      messages,
      materialCount,
      updatedAt: Date.now(),
    }, ...current]);
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
              <div className={styles.sessionItemWrap} key={item.id}>
                <button
                  type="button"
                  className={[styles.sessionItem, activeHistoryId === item.id ? styles.sessionActive : ""].filter(Boolean).join(" ")}
                  onClick={() => handleSelectHistory(item)}
                >
                  <span className={styles.sessionDot} />
                  <span className={styles.sessionName}>{item.title}</span>
                  <small>{formatTime(item.updatedAt)}</small>
                </button>
                <button type="button" className={styles.sessionDelete} onClick={(event) => handleDeleteHistory(event, item.id)} aria-label={`删除研判记录：${item.title}`} title="删除记录">×</button>
              </div>
            ))}
          </div>
          <section className={styles.sidebarSafety}>
            <div className={styles.safetyHeading}><i>盾</i><span><strong>本地隐私预检</strong></span><b>已开启</b></div>
            <div className={styles.safetyTech}><span>本地OCR</span><span>规则校验</span><span>字段脱敏</span><span>EXIF清理</span></div>
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
