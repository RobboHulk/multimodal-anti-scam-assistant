import { useRef, useCallback, useEffect } from "react";
import Icons from "../../data/detectIcons";
import styles from "./Detect.module.css";
const now = () => new Date().toLocaleString("zh-CN", { hour12: false });
// 捕获面板组件
export function CapturePanel({
  running,
  waves,
  riskValue,
  riskColor,
  termLines,
}) {
  const eventsRef = useRef(null);
  const termRef = useRef(null);
  const autoScrollEnabledRef = useRef(true);
  const scrollTimeoutRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    if (eventsRef.current && autoScrollEnabledRef.current) {
      eventsRef.current.scrollTop = eventsRef.current.scrollHeight;
    }
    if (termRef.current && autoScrollEnabledRef.current) {
      termRef.current.scrollTop = termRef.current.scrollHeight;
    }
  }, []);

  useEffect(() => {
    const handleScroll = (e) => {
      const target = e.target;
      const isAtBottom =
        target.scrollHeight - target.scrollTop - target.clientHeight < 50;

      if (isAtBottom) {
        autoScrollEnabledRef.current = true;
      } else {
        autoScrollEnabledRef.current = false;
        if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = setTimeout(() => {
          autoScrollEnabledRef.current = true;
          scrollToBottom();
        }, 5000);
      }
    };

    const eventsEl = eventsRef.current;
    const termEl = termRef.current;

    if (eventsEl) {
      eventsEl.addEventListener("scroll", handleScroll);
    }
    if (termEl) {
      termEl.addEventListener("scroll", handleScroll);
    }

    return () => {
      if (eventsEl) eventsEl.removeEventListener("scroll", handleScroll);
      if (termEl) termEl.removeEventListener("scroll", handleScroll);
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    };
  }, [scrollToBottom]);

  useEffect(() => {
    if (autoScrollEnabledRef.current) {
      scrollToBottom();
    }
  }, [waves, scrollToBottom]);

  useEffect(() => {
    if (autoScrollEnabledRef.current) {
      scrollToBottom();
    }
  }, [termLines, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    };
  }, []);

  const getRiskLevelText = (risk) => {
    if (risk <= 35) return "低风险";
    if (risk <= 60) return "中风险";
    if (risk <= 85) return "高风险";
    return "极高风险";
  };

  return (
    <div className={styles.capturePanel}>
      <div className={styles.captureTitleBar}>
        <span
          className={`${styles.radarDot} ${running ? styles.active : ""}`}
        />
        <span className={styles.captureTitleText}>多模态数据实时捕获引擎</span>
        <span
          className={`${styles.captureStatus} ${running ? styles.statusActive : ""}`}
        >
          {running ? "ACTIVE" : "IDLE"}
        </span>
        {riskValue > 0 && (
          <span
            className={styles.riskInline}
            style={{ color: riskColor, borderColor: riskColor }}
          >
            RISK {riskValue}
          </span>
        )}
      </div>

      <div className={styles.captureEvents} ref={eventsRef}>
        {waves.length === 0 && !running && (
          <div className={styles.captureIdle}>等待分析任务启动...</div>
        )}
        {waves.length === 0 && running && (
          <div className={styles.captureIdle}>
            <span className={styles.spinnerSmall} />
            正在接入数据流，等待捕获...
          </div>
        )}
        {waves.map((wave, idx) => (
          <div key={wave.id} className={styles.waveBlock}>
            {idx > 0 && <div className={styles.waveDivider} />}
            <div
              className={styles.waveCapture}
              style={{ borderLeftColor: wave.color }}
            >
              <div className={styles.waveCaptureHeader}>
                <span
                  className={styles.waveCaptureIcon}
                  style={{ color: wave.color }}
                >
                  {Icons[wave.icon]}
                </span>
                <span
                  className={styles.waveCaptureLabel}
                  style={{ color: wave.color }}
                >
                  {wave.label} · 捕获成功
                </span>
                <span className={styles.waveCaptureTime}>
                  {wave.timestamp || now()}
                </span>
              </div>
              <div className={styles.waveCaptureContent}>
                {wave.displayContent !== undefined
                  ? wave.displayContent
                  : wave.content}
                {wave.isTypingContent && (
                  <span className={styles.blinkCursor}>|</span>
                )}
              </div>
              {wave.images && wave.images.length > 0 && (
                <div className={styles.waveImages}>
                  {wave.images.map((img, i) => (
                    <div key={i} className={styles.waveImageItem}>
                      <div className={styles.waveImagePreview}>
                        <span className={styles.imageIcon}>
                          {Icons.imageIcon}
                        </span>
                        <span className={styles.imageLabel}>{img.label}</span>
                      </div>
                      {img.ocr_text && (
                        <div className={styles.waveOcrText}>
                          {wave.displayOcr?.[i] !== undefined
                            ? wave.displayOcr[i]
                            : `OCR: ${img.ocr_text.slice(0, 60)}...`}
                          {wave.isTypingOcr?.[i] && (
                            <span className={styles.blinkCursor}>|</span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
            {wave.steps && wave.steps.length > 0 && (
              <div className={styles.waveSteps}>
                {wave.steps.map((step, si) => (
                  <div
                    key={si}
                    className={`${styles.waveStep} ${wave.showedSteps?.[si] ? styles.visible : styles.hidden}`}
                  >
                    <span
                      className={styles.waveStepDot}
                      style={{
                        borderColor: wave.color,
                        background: wave.color,
                      }}
                    >
                      {wave.showedSteps?.[si] ? (
                        Icons.check
                      ) : (
                        <span className={styles.stepDot}></span>
                      )}
                    </span>
                    <span className={styles.waveStepText}>
                      {wave.displaySteps?.[si] !== undefined
                        ? wave.displaySteps[si]
                        : step}
                      {wave.isTypingSteps?.[si] && (
                        <span className={styles.blinkCursor}>|</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {wave.showConclusion && (
              <div className={styles.waveConclusion}>
                <div className={styles.waveConclusionRow}>
                  <span className={styles.waveConclusionLabel}>风险标签</span>
                  <div className={styles.waveConclusionTags}>
                    {wave.tags.map((tag) => (
                      <span key={tag} className={styles.waveTag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
                <div className={styles.waveConclusionRow}>
                  <span className={styles.waveConclusionLabel}>风险评估</span>
                  <span
                    className={styles.waveConclusionRisk}
                    style={{
                      color:
                        wave.risk <= 35
                          ? "#eab308"
                          : wave.risk <= 60
                            ? "#f97316"
                            : "#ef4444",
                    }}
                  >
                    {wave.displayRisk !== undefined
                      ? wave.displayRisk
                      : `${wave.risk}/100 · ${getRiskLevelText(wave.risk)}`}
                    {wave.isTypingRisk && (
                      <span className={styles.blinkCursor}>|</span>
                    )}
                  </span>
                </div>
                <div className={styles.waveConclusionRow}>
                  <span className={styles.waveConclusionLabel}>分析结果</span>
                  <span className={styles.waveConclusionValue}>
                    {wave.displayAnalysis !== undefined
                      ? wave.displayAnalysis
                      : wave.analysis}
                    {wave.isTypingAnalysis && (
                      <span className={styles.blinkCursor}>|</span>
                    )}
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className={styles.terminal} ref={termRef}>
        {termLines.map((line, i) => (
          <div key={i} className={styles.termLine}>
            {line}
          </div>
        ))}
        {running && <span className={styles.cursor}>_</span>}
      </div>
    </div>
  );
}
