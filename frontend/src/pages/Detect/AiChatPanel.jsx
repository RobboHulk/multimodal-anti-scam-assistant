import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useId,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
import styles from "./Detect.module.css";

const makeId = () => "msg-" + Date.now() + "-" + Math.random().toString(36).slice(2, 7);

const safeMarkup = (text = "") => {
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, "<h4>$1</h4>")
    .replace(/^## (.+)$/gm, "<h3>$1</h3>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (items) => "<ul>" + items + "</ul>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/\n/g, "<br/>");
  return "<p>" + html + "</p>";
};

const materialIcon = (type = "", name = "") => {
  if (type.startsWith("image/")) return "图";
  if (type.startsWith("audio/")) return "音";
  if (type.startsWith("video/")) return "视";
  if (/apk|zip|rar|pdf|doc/i.test(name)) return "件";
  return "文";
};

const DEMO_PROMPT = `请对我提交的资质证明图片、通话录音和案例视频进行一次深度安全研判。

对方自称“海岳商业银行客户服务专员”，先发送工作人员资质证明，随后在通话中称我的账户触发异常风控，要求我立即打开其提供的“安全核验页面”：https://hyyh-security-check.example，并填写手机号、网银登录信息和短信验证码。我目前尚未打开链接，也没有提交任何信息或进行转账。

请核验图片、音频和链接，梳理攻击意图链，区分事实、风险判断与条件推演，并给出带证据编号的处置建议。`;

const DEMO_RESPONSE = `我已经把你提交的图片、通话录音和链接放在一起核验完了。

**先说结论：这不是正常的银行风控核验，建议按高风险事件处理。** 对方正在借助伪造的工作人员身份取得信任，再用“账户异常”的紧迫话术推动你进入仿冒页面，最终目标很可能是获取网银登录信息和短信验证码。

好消息是，你还没有打开链接、提交信息或转账。根据现有材料，攻击目前停在“凭据请求”阶段，尚未发现账户已被接管或资金受损的迹象，现在中断仍然来得及。

### 我为什么这样判断
- **资质图片存在伪造线索。** 人物边界、印章叠加和编号区域出现局部不一致，相关位置已标记为 IMG-01。
- **录音中存在合成异常。** AUDIO-02 在 00:08—00:13 检出谐波截断、相位跳变和韵律突变，但仅凭这一项不能直接认定说话者身份。
- **链接与银行官方域名不一致。** URL-03 指向一个索取密码和短信验证码的页面，这是本次判断中权重最高的直接风险证据。
- **三类材料指向同一攻击目标。** 图片负责建立身份可信度，通话负责制造紧迫感，链接负责收集凭据，组合后形成了完整的诱导链条。

### 建议你现在这样处理
- 不要访问该链接，也不要继续向对方提供任何验证码或账户信息。
- 通过银行官方 App 或银行卡背面的客服电话独立核验，不要使用对方提供的联系方式。
- 保留原始图片、录音、聊天记录与链接；如果误点过链接，立即修改网银密码并联系银行冻结高风险操作。

我已经为每项判断保留了证据编号。下方是本次研判摘要，你也可以进入“完整研判”查看异常区域、音频区间和攻击意图链。`;

const thinkingStages = [
  { title: "执行本地隐私预检", detail: "识别敏感字段并清理可泄露身份的元数据" },
  { title: "解析并固定材料", detail: "提取图像、音频与文本中的可核验对象" },
  { title: "并行调用专项能力", detail: "内容鉴真、语音取证与链接威胁同步核验" },
  { title: "交叉验证关键主张", detail: "合并证据、检查冲突并补充高影响结论" },
  { title: "组织可回溯回复", detail: "区分事实、风险判断与条件性推演" },
];

const stageArtifacts = [
  ["敏感字段 4 项", "元数据 7 项"],
  ["图像对象 1", "音频片段 26", "链接对象 1"],
  ["异常区域 3", "异常区间 1", "高危表单 1"],
  ["有效证据 18", "冲突主张 1", "边界声明 2"],
  ["引用已回指", "报告已归档"],
];

const DemoResult = () => (
  <div className={styles.demoResult}>
    <div className={styles.resultSummary}>
      <div><span>综合风险</span><strong>高风险</strong></div>
      <div><span>证据充分性</span><strong>88</strong></div>
      <div><span>已核验材料</span><strong>3 份</strong></div>
      <div><span>实际损害</span><strong className={styles.safeResult}>未发现</strong></div>
    </div>
    <div className={styles.resultEvidence}>
      <article><i>IMG-01</i><div><strong>资质图片存在局部异常</strong><span>人物边界、印章叠加和编号区域出现不一致线索</span></div><b>87</b></article>
      <article><i>AUDIO-02</i><div><strong>通话音频存在合成线索</strong><span>00:08—00:13 出现谐波截断、相位跳变与韵律异常</span></div><b>86</b></article>
      <article><i>URL-03</i><div><strong>页面请求指向凭据收集</strong><span>域名与声称主体不一致，并索取密码及短信验证码</span></div><b>95</b></article>
    </div>
    <div className={styles.resultChain}>
      <span>身份接触</span><i>→</i><span>资质塑造</span><i>→</i><span>紧迫施压</span><i>→</i><span className={styles.chainDanger}>凭据请求</span><i>→</i><span className={styles.chainForecast}>账户接管（推演）</span>
    </div>
    <div className={styles.resultBoundary}>
      <strong>现在怎么做</strong>
      <p>停止访问对方链接；不要提供密码或验证码；通过银行官方 App 或官方客服电话独立核验；保留原始图片、录音、视频和消息记录。</p>
      <span>边界：尚无凭据已泄露、账户已被接管或资金已经损失的证据。</span>
    </div>
    <div className={styles.resultActions}><Link to="/analysis">查看完整研判</Link><Link to="/reports">打开安全报告</Link></div>
  </div>
);

const Message = ({ message, streaming = false }) => {
  const isUser = message.type === "user";
  return (
    <div className={[styles.messageRow, isUser ? styles.messageUser : styles.messageAssistant].join(" ")}>
      {!isUser && <div className={styles.assistantMark}>澜</div>}
      <div className={styles.messageBody}>
        {message.files?.length > 0 && (
          <div className={styles.messageMaterials}>
            {message.files.map((file) => (
              <span key={file.name}><i>{materialIcon(file.type, file.name)}</i>{file.name}</span>
            ))}
          </div>
        )}
        {isUser ? (
          <div className={styles.userText}>{message.content}</div>
        ) : (
          <>
            <div className={styles.assistantText} dangerouslySetInnerHTML={{ __html: safeMarkup(message.content) }} />
            {message.resultData?.demo && <DemoResult />}
          </>
        )}
        {streaming && <span className={styles.streamingCursor} />}
      </div>
    </div>
  );
};

const quickPrompts = [
  "帮我判断这段对话是否在诱导我提交验证码",
  "检查这个二维码和跳转链接是否安全",
  "分析这段语音是否存在身份伪造风险",
];

const AiChatPanel = forwardRef(({ onSaveHistory, onProcessChange }, ref) => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [inputFiles, setInputFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [deepAnalysis, setDeepAnalysis] = useState(true);
  const [thinkingStep, setThinkingStep] = useState(-1);
  const [elapsed, setElapsed] = useState(0);
  const endRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const fileInputRef = useRef(null);
  const textRef = useRef(null);
  const messagesRef = useRef([]);
  const stableId = useId();
  const sessionId = useRef("sess-" + stableId.replace(/:/g, ""));
  const abortRef = useRef(null);
  const finishedRef = useRef(false);
  const timersRef = useRef([]);

  const clearDemoTimers = useCallback(() => {
    timersRef.current.forEach((timer) => {
      clearTimeout(timer);
      clearInterval(timer);
    });
    timersRef.current = [];
  }, []);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages, streamingMessage]);
  useEffect(() => {
    if (!textRef.current) return;
    textRef.current.style.height = "28px";
    textRef.current.style.height = Math.min(textRef.current.scrollHeight, 132) + "px";
  }, [inputText]);
  useEffect(() => clearDemoTimers, [clearDemoTimers]);

  useImperativeHandle(ref, () => ({
    reset() {
      abortRef.current?.abort?.();
      clearDemoTimers();
      messagesRef.current = [];
      setMessages([]);
      setInputText("");
      setInputFiles([]);
      setStreamingMessage(null);
      setIsLoading(false);
      setUploadStatus("");
      setThinkingStep(-1);
      setElapsed(0);
      sessionId.current = "sess-" + Date.now();
    },
    loadMessages(nextMessages) {
      messagesRef.current = nextMessages || [];
      setMessages(messagesRef.current);
      setInputText("");
      setInputFiles([]);
      setStreamingMessage(null);
      setIsLoading(false);
      setThinkingStep(-1);
      setElapsed(0);
    },
  }), [clearDemoTimers]);

  const selectFiles = (event) => {
    const files = Array.from(event.target.files || []).slice(0, 6);
    setInputFiles((current) => [...current, ...files].slice(0, 6));
    onProcessChange?.({
      phase: files.length ? "ready" : "idle",
      label: files.length ? "材料已就绪" : "等待材料",
      materialCount: Math.min(inputFiles.length + files.length, 6),
    });
    event.target.value = "";
  };

  const finish = useCallback((content, resultData, originalText, materialCount) => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    const assistantMessage = {
      id: makeId(),
      type: "ai",
      content: content || "当前服务暂未返回结果，请稍后重试。",
      resultData,
    };
    const next = [...messagesRef.current, assistantMessage];
    messagesRef.current = next;
    setMessages(next);
    onSaveHistory?.(originalText, next, materialCount);
    setStreamingMessage(null);
    setIsLoading(false);
    setUploadStatus("");
    setThinkingStep(-1);
    onProcessChange?.({ phase: "complete", label: "研判完成", materialCount });
  }, [onProcessChange, onSaveHistory]);

  const send = useCallback(() => {
    const text = inputText.trim();
    if ((!text && inputFiles.length === 0) || isLoading) return;
    clearDemoTimers();
    const files = [...inputFiles];
    const materialCount = files.length;
    const userMessage = {
      id: makeId(),
      type: "user",
      content: text,
      files: files.map((file) => ({ name: file.name, type: file.type, size: file.size })),
    };
    messagesRef.current = [...messagesRef.current, userMessage];
    setMessages(messagesRef.current);
    setInputText("");
    setInputFiles([]);
    setIsLoading(true);
    setUploadStatus("processing");
    setThinkingStep(0);
    setElapsed(0);
    finishedRef.current = false;
    onProcessChange?.({ phase: "privacy", label: "本地隐私预检", materialCount });

    const startedAt = Date.now();
    timersRef.current.push(setInterval(() => {
      setElapsed((Date.now() - startedAt) / 1000);
    }, 100));
    const schedule = deepAnalysis
      ? { upload: 1200, analysis: 3100, audit: 6500, synthesis: 8900 }
      : { upload: 650, analysis: 1500, audit: 2850, synthesis: 4100 };
    timersRef.current.push(setTimeout(() => {
      setThinkingStep(1);
      onProcessChange?.({ phase: "uploading", label: "解析并固定材料", materialCount });
    }, schedule.upload));
    timersRef.current.push(setTimeout(() => {
      setThinkingStep(2);
      onProcessChange?.({ phase: "analysis", label: "专项能力并行核验", materialCount });
    }, schedule.analysis));
    timersRef.current.push(setTimeout(() => {
      setThinkingStep(3);
      onProcessChange?.({ phase: "audit", label: "证据交叉审计", materialCount });
    }, schedule.audit));
    timersRef.current.push(setTimeout(() => {
      setThinkingStep(4);
      onProcessChange?.({ phase: "synthesis", label: "正在组织研判回复", materialCount });
      setStreamingMessage({ id: "streaming-response", type: "ai", content: "" });

      let cursor = 0;
      const streamTimer = setInterval(() => {
        const char = DEMO_RESPONSE[cursor] || "";
        const step = /[。！？\n]/.test(char) ? 4 : 10;
        cursor = Math.min(DEMO_RESPONSE.length, cursor + step);
        setStreamingMessage({ id: "streaming-response", type: "ai", content: DEMO_RESPONSE.slice(0, cursor) });
        if (cursor >= DEMO_RESPONSE.length) {
          clearInterval(streamTimer);
          const finishTimer = setTimeout(() => {
            clearDemoTimers();
            setElapsed((schedule.synthesis + 3600) / 1000);
            finish(DEMO_RESPONSE, { demo: true }, text, materialCount);
          }, 450);
          timersRef.current.push(finishTimer);
        }
      }, 58);
      timersRef.current.push(streamTimer);
    }, schedule.synthesis));
  }, [clearDemoTimers, deepAnalysis, finish, inputFiles, inputText, isLoading, onProcessChange]);

  const onKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };

  const removeFile = (index) => {
    setInputFiles((items) => {
      const next = items.filter((_, itemIndex) => itemIndex !== index);
      onProcessChange?.({
        phase: next.length ? "ready" : "idle",
        label: next.length ? "材料已就绪" : "等待材料",
        materialCount: next.length,
      });
      return next;
    });
  };

  return (
    <section className={styles.chatPanel}>
      <header className={styles.chatHeader}>
        <div>
          <h1>智能体研判</h1>
          <span>材料隔离处理 · 结论逐项回指</span>
        </div>
        <div className={styles.headerActions}>
          <span className={styles.privacyBadge}>本地预检 · 4项策略</span>
          <Link to="/analysis">打开研判详情</Link>
        </div>
      </header>

      <div className={styles.chatMessages} ref={messagesContainerRef}>
        {messages.length === 0 && !streamingMessage ? (
          <div className={styles.welcome}>
            <div className={styles.welcomeSymbol}><span /><span /><span /></div>
            <h2>有什么可疑情况需要核验？</h2>
            <div className={styles.capabilityGrid}>
              <button type="button" onClick={() => fileInputRef.current?.click()}><div className={[styles.capabilityVisual, styles.truthVisual].join(" ")}><span /><span /><span /></div><i>01</i><strong>音视频鉴真</strong><span>热力定位合成与篡改区域</span></button>
              <button type="button" onClick={() => fileInputRef.current?.click()}><div className={[styles.capabilityVisual, styles.linkVisual].join(" ")}><span /><span /><span /></div><i>02</i><strong>链接与文件</strong><span>核验跳转、域名和执行载荷</span></button>
              <button type="button" onClick={() => setInputText(quickPrompts[0])}><div className={[styles.capabilityVisual, styles.intentVisual].join(" ")}><span /><span /><span /></div><i>03</i><strong>诱导行为</strong><span>还原危险请求的推进过程</span></button>
              <button type="button" onClick={() => setInputText("请逐条说明结论依据和仍需确认的内容")}><div className={[styles.capabilityVisual, styles.auditVisual].join(" ")}><span /><span /><span /></div><i>04</i><strong>证据审计</strong><span>限制无依据的过度推断</span></button>
            </div>
            <div className={styles.quickPrompts}>
              <button type="button" className={styles.demoPromptButton} onClick={() => setInputText(DEMO_PROMPT)}>载入演示案例</button>
              {quickPrompts.map((prompt) => (
                <button type="button" key={prompt} onClick={() => setInputText(prompt)}>{prompt}</button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => <Message message={message} key={message.id} />)}
            {isLoading && !streamingMessage && (
              <div className={[styles.messageRow, styles.messageAssistant].join(" ")}>
                <div className={styles.assistantMark}>澜</div>
                <div className={styles.deepThinking}>
                  <div className={styles.thinkingHeader}><span><i />深度分析中</span><b>{elapsed.toFixed(1)}s</b></div>
                  <div className={styles.thinkingActivity}>
                    <span className={styles.activityWave}><i /><i /><i /><i /><i /><i /><i /><i /></span>
                    <div><strong>{thinkingStages[Math.max(0, thinkingStep)]?.title}</strong><small>智能体正在更新可验证证据</small></div>
                    <b>{[15, 32, 61, 82, 94][Math.max(0, thinkingStep)]}%</b>
                  </div>
                  <div className={styles.thinkingStages}>
                    {thinkingStages.map((stage, index) => {
                      const state = index < thinkingStep ? "done" : index === thinkingStep ? "active" : "pending";
                      return <div className={styles[state]} key={stage.title}><i>{state === "done" ? "✓" : index + 1}</i><span><strong>{stage.title}</strong><small>{stage.detail}</small></span><b>{state === "done" ? "完成" : state === "active" ? "处理中" : "等待"}</b></div>;
                    })}
                  </div>
                  <div className={styles.thinkingArtifacts}>
                    {(stageArtifacts[Math.max(0, thinkingStep)] || []).map((item) => <span key={item}>{item}</span>)}
                  </div>
                  <p>仅展示任务状态与证据产物；完成后将说明结论、依据、边界与处置建议</p>
                </div>
              </div>
            )}
            {streamingMessage && <Message message={streamingMessage} streaming />}
            <div ref={endRef} />
          </>
        )}
      </div>

      <div className={styles.composerArea}>
        {inputFiles.length > 0 && (
          <div className={styles.selectedFiles}>
            {inputFiles.map((file, index) => (
              <div className={styles.selectedFile} key={file.name + "-" + index}>
                <i>{materialIcon(file.type, file.name)}</i>
                <span>{file.name}</span>
                <button type="button" onClick={() => removeFile(index)}>×</button>
              </div>
            ))}
          </div>
        )}
        {uploadStatus && (
          <div className={[styles.uploadNotice, uploadStatus === "warning" ? styles.uploadWarning : ""].filter(Boolean).join(" ")}>
            {uploadStatus === "warning" ? "部分材料暂未上传，已保留文字研判" : "材料已进入隔离解析区，正在生成可回溯证据"}
          </div>
        )}
        <div className={styles.composer}>
          <div className={styles.composerSecurity}><i>✓</i><span>本地隐私预检已开启</span></div>
          <textarea
            ref={textRef}
            value={inputText}
            onChange={(event) => setInputText(event.target.value)}
            onKeyDown={onKeyDown}
            placeholder="描述可疑情况，或粘贴短信、链接和对话内容"
            rows={1}
          />
          <div className={styles.composerBottom}>
            <div className={styles.attachments}>
              <button type="button" onClick={() => fileInputRef.current?.click()}><span>＋</span>添加材料</button>
              <button type="button" className={[styles.deepAnalysisToggle, deepAnalysis ? styles.deepAnalysisOn : ""].filter(Boolean).join(" ")} aria-pressed={deepAnalysis} onClick={() => setDeepAnalysis((current) => !current)}><i>✦</i>深度分析<span>{deepAnalysis ? "已开启" : "已关闭"}</span></button>
            </div>
            <button className={styles.sendButton} type="button" onClick={send} disabled={isLoading || (!inputText.trim() && inputFiles.length === 0)}>
              {isLoading ? "分析中" : "开始研判"}<span>↗</span>
            </button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            hidden
            accept="image/*,audio/*,video/*,.pdf,.doc,.docx,.apk,.zip,.rar,.txt"
            onChange={selectFiles}
          />
        </div>
      </div>
    </section>
  );
});

AiChatPanel.displayName = "AiChatPanel";
export default AiChatPanel;
