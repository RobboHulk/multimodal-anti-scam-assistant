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
import { streamChat, uploadFile } from "../../api/chatService";
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
          <div className={styles.assistantText} dangerouslySetInnerHTML={{ __html: safeMarkup(message.content) }} />
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
  const endRef = useRef(null);
  const fileInputRef = useRef(null);
  const textRef = useRef(null);
  const stableId = useId();
  const sessionId = useRef("sess-" + stableId.replace(/:/g, ""));
  const abortRef = useRef(null);
  const finishedRef = useRef(false);

  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [messages, streamingMessage]);
  useEffect(() => {
    if (!textRef.current) return;
    textRef.current.style.height = "28px";
    textRef.current.style.height = Math.min(textRef.current.scrollHeight, 132) + "px";
  }, [inputText]);

  useImperativeHandle(ref, () => ({
    reset() {
      abortRef.current?.abort();
      setMessages([]);
      setInputText("");
      setInputFiles([]);
      setStreamingMessage(null);
      setIsLoading(false);
      setUploadStatus("");
      sessionId.current = "sess-" + Date.now();
    },
    loadMessages(nextMessages) {
      setMessages(nextMessages || []);
      setInputText("");
      setInputFiles([]);
      setStreamingMessage(null);
      setIsLoading(false);
    },
  }));

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
    setMessages((current) => {
      const next = [...current, assistantMessage];
      onSaveHistory?.(originalText, next, materialCount);
      return next;
    });
    setStreamingMessage(null);
    setIsLoading(false);
    setUploadStatus("");
    onProcessChange?.({ phase: "complete", label: "研判完成", materialCount });
  }, [onProcessChange, onSaveHistory]);

  const send = useCallback(async () => {
    const text = inputText.trim();
    if ((!text && inputFiles.length === 0) || isLoading) return;
    const files = [...inputFiles];
    const materialCount = files.length;
    const userMessage = {
      id: makeId(),
      type: "user",
      content: text,
      files: files.map((file) => ({ name: file.name, type: file.type, size: file.size })),
    };
    setMessages((current) => [...current, userMessage]);
    setInputText("");
    setInputFiles([]);
    setIsLoading(true);
    finishedRef.current = false;
    onProcessChange?.({ phase: "privacy", label: "隐私预检", materialCount });

    let imagePath = "";
    let audioPath = "";
    let videoPath = "";
    if (files.length) {
      setUploadStatus("uploading");
      onProcessChange?.({ phase: "uploading", label: "材料解析", materialCount });
      for (const file of files) {
        try {
          const path = await uploadFile(file);
          if (file.type.startsWith("image/")) imagePath = path;
          if (file.type.startsWith("audio/")) audioPath = path;
          if (file.type.startsWith("video/")) videoPath = path;
        } catch {
          setUploadStatus("warning");
        }
      }
    }

    onProcessChange?.({ phase: "analysis", label: "协同核验", materialCount });
    let fullContent = "";
    let resultData = null;
    abortRef.current = streamChat({
      text,
      sessionId: sessionId.current,
      imagePath,
      audioPath,
      videoPath,
      dimensions: [],
      onContent(chunk) {
        fullContent += chunk;
        setStreamingMessage({ id: "streaming", type: "ai", content: fullContent });
      },
      onResult(data) {
        resultData = data;
        if (data.chatResponse) fullContent = data.chatResponse;
        onProcessChange?.({ phase: "audit", label: "结论审计", materialCount });
      },
      onError(error) {
        finish("分析服务暂不可用：" + error, resultData, text, materialCount);
      },
      onDone() {
        finish(fullContent, resultData, text, materialCount);
      },
    });
  }, [finish, inputFiles, inputText, isLoading, onProcessChange]);

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

      <div className={styles.chatMessages}>
        {messages.length === 0 && !streamingMessage ? (
          <div className={styles.welcome}>
            <div className={styles.welcomeSymbol}><span /><span /><span /></div>
            <h2>有什么可疑情况需要核验？</h2>
            <p>描述经过并提交相关材料，系统会分别核验内容、来源、链接、文件与诱导行为。</p>
            <div className={styles.capabilityGrid}>
              <button type="button" onClick={() => fileInputRef.current?.click()}><div className={[styles.capabilityVisual, styles.truthVisual].join(" ")}><span /><span /><span /></div><i>01</i><strong>音视频鉴真</strong><span>热力定位合成与篡改区域</span></button>
              <button type="button" onClick={() => fileInputRef.current?.click()}><div className={[styles.capabilityVisual, styles.linkVisual].join(" ")}><span /><span /><span /></div><i>02</i><strong>链接与文件</strong><span>核验跳转、域名和执行载荷</span></button>
              <button type="button" onClick={() => setInputText(quickPrompts[0])}><div className={[styles.capabilityVisual, styles.intentVisual].join(" ")}><span /><span /><span /></div><i>03</i><strong>诱导行为</strong><span>还原危险请求的推进过程</span></button>
              <button type="button" onClick={() => setInputText("请逐条说明结论依据和仍需确认的内容")}><div className={[styles.capabilityVisual, styles.auditVisual].join(" ")}><span /><span /><span /></div><i>04</i><strong>证据审计</strong><span>限制无依据的过度推断</span></button>
            </div>
            <div className={styles.quickPrompts}>
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
                <div className={styles.analysisPulse}><i /><i /><i /><span>正在组织核验任务</span></div>
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
            {uploadStatus === "warning" ? "部分材料暂未上传，已保留文字研判" : "材料正在进入安全解析区"}
          </div>
        )}
        <div className={styles.composer}>
          <div className={styles.composerSecurity}><i>✓</i><span>提交前将在本机执行敏感字段识别、遮蔽和元数据清理</span><b>原文不用于训练</b></div>
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
              <span>支持截图、音视频、二维码、链接与文件</span>
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
