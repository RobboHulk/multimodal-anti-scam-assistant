// 多模态捕获数据 - 优化版，新增可信证据环节，分数有升有降
export const MULTIMODAL_WAVES = [
  // 1. 初次接触 - 低风险
  {
    id: "text_1",
    type: "text",
    icon: "text",
    label: "文本模态",
    color: "#4361ee",
    timestamp: "2026/5/1 09:01:02",
    content:
      "客服小陈：您好，请问是张先生吗？我是京东白条的客服陈刚。这是我的工作证",
    images: [
      { type: "work_id", url: "/api/placeholder/400/300", label: "工作证图片" },
    ],
    steps: [
      "NLP 语义解析启动...",
      "分词完成 — 提取关键实体 12 个",
      "命中高危词组：「京东白条」「客服」「工作证」",
      "话术模式匹配 — 冒充电商客服 (置信度 0.92)",
      "情感倾向：中性话术，建立信任阶段",
    ],
    tags: ["冒充客服", "京东白条", "工作证诈骗"],
    risk: 18.4,
    analysis: "检测到来历不明的客服人员与工作证截图，请警惕诈骗",
    terminalLines: [
      "[INFO] Text NLP pipeline: RUNNING",
      "[WARN] Keyword hit: '京东白条' — fraud_score 0.87",
      "[WARN] Keyword hit: '客服' — fraud_score 0.76",
      "[INFO] Risk score updated: 0 → 18.4 (LOW_RISK)",
    ],
  },
  // 2. 图像分析 - 分数上升
  {
    id: "image_1",
    type: "image",
    icon: "image",
    label: "图像模态",
    color: "#f59e0b",
    timestamp: "2026/5/1 09:01:02",
    content: "[图片] 客服发送工作证图片 + 业务登记截图",
    images: [
      {
        type: "work_card",
        url: "/api/placeholder/400/300",
        label: "京东工作证",
        ocr_text: "姓名：陈刚 工号：JD1089 注销部",
      },
    ],
    steps: [
      "图像接收 — 分辨率 620×900，格式 JPG",
      "OCR 识别 — 提取姓名「陈刚」工号「JD1089」",
      "工号格式验证 — 与京东官方标准匹配",
      "PS 痕迹检测 — ELA 误差分析，编辑痕迹轻微",
      "综合判断 — 工作证真实，但存在被冒用可能",
    ],
    tags: ["工作证核实中", "信息泄露", "公章待复核"],
    risk: 42.8,
    analysis: "工作证初步判定为真实",
    terminalLines: [
      "[INFO] Incoming image detected",
      "[INFO] Work ID verification: format matches JD.com standard",
      "[WARN] Personal information leakage detected",
      "[INFO] Risk score updated: 18.4 → 42.8 (MEDIUM_RISK)",
    ],
  },
  // 3. 信息确认 - 分数微升
  {
    id: "text_2",
    type: "text",
    icon: "text",
    label: "文本模态",
    color: "#4361ee",
    timestamp: "2026/5/1 09:01:08",
    content: "客服小陈：您的支付宝账户是不是18844291045?",
    steps: [
      "NLP 语义解析启动...",
      "检测到个人敏感信息确认意图",
      "信息匹配 — 账户信息泄露风险",
      "话术特征：信息验证阶段",
    ],
    tags: ["信息确认", "隐私泄露"],
    risk: 46.2,
    analysis: "检测到个人账户信息泄露风险",
    terminalLines: ["[INFO] Risk score updated: 42.8 → 46.2 (MEDIUM_RISK)"],
  },
  // 4. 骗子提供"官方验证渠道" - 分数下降，但保持在中等风险
  {
    id: "credible_evidence_1",
    type: "text",
    icon: "text",
    label: "可信证据验证",
    color: "#10b981",
    timestamp: "2026/5/1 09:01:25",
    content:
      "客服小陈：您可以拨打京东官方客服热线 95118 核实我的工号 JD1089，也可以登录京东APP查看我的官方认证标识。",
    steps: [
      "NLP 语义解析启动...",
      "检测到引导用户通过官方渠道核实",
      "实时拨打 95118 验证 — 工号 JD1089 确为京东白条在职客服",
      "京东官方API查询 — 该工号状态为「正常在职」，认证标识匹配",
      "系统评估：对方提供了可验证的真实身份信息",
      "风险评分下调 — 诈骗可能性降低，但仍需警惕",
    ],
    tags: ["身份可验证", "官方工号", "信任建立"],
    risk: 36.1,
    analysis:
      "经官方渠道验证，对方工号真实有效，暂时降低风险评级，持续监控后续对话",
    terminalLines: [
      "[INFO] User instructed to verify via official channel",
      "[INFO] Dialing JD.com customer service 95118...",
      "[INFO] Verification result: Employee ID JD1089 — CONFIRMED",
      "[INFO] Official API query: status ACTIVE, certification MATCHED",
      "[INFO] Risk score adjusted: 46.2 → 36.1 (MEDIUM_RISK)",
      "[INFO] System status: MONITORING MODE — awaiting next interaction",
    ],
  },
  // 5. 语音威胁 - 分数飙升到高风险
  {
    id: "audio_1",
    type: "audio",
    icon: "audio",
    label: "语音模态",
    color: "#7c5cfc",
    timestamp: "2026/5/1 09:01:38",
    content:
      "「根据国家相关政策，现在需要将其注销关闭,否则将影响到个人征信，麻烦您配合工作！」",
    steps: [
      "音频流接入 — 采样率 44100Hz",
      "语音转写引擎启动 — ASR 模型 whisper-large-v3",
      "转写完成 — 识别置信度 0.97",
      "情绪分析 — 胁迫性语气特征显著 (指数 0.89)",
      "话术模式匹配 — 命中「注销校园贷」典型诈骗话术 (置信度 0.96)",
      "声纹分析 — 与已知诈骗样本相似度 78%",
    ],
    tags: ["注销校园贷", "征信威胁", "胁迫话术"],
    risk: 72.6,
    analysis:
      "检测到疑似注销校园贷诈骗的典型话术，声纹情绪有明显胁迫与威胁，注意防范！",
    terminalLines: [
      "[INFO] Audio stream captured",
      "[WARN] Keyword hit: '注销校园贷' — fraud_score 0.96",
      "[WARN] Keyword hit: '征信' — fraud_score 0.92",
      "[WARN] Emotional analysis: coercion detected — intensity 0.89",
      "[INFO] Risk score updated: 36.1 → 72.6 (HIGH_RISK)",
    ],
  },
  // 6. 诱导操作 - 分数上升
  {
    id: "text_3",
    type: "text",
    icon: "text",
    label: "文本模态",
    color: "#4361ee",
    timestamp: "2026/5/1 09:01:41",
    content:
      "客服小陈：为了验证您的征信目前是否受到影响，需要您先配合清空借贷平台的资金。",
    steps: [
      "NLP 语义解析启动...",
      "检测到危险操作引导",
      "命中高危关键词：「清空资金」「验证征信」",
      "话术模式 — 诱导资金操作 (置信度 0.98)",
      "风险升级 — 实质性资金风险",
      "结合此前验证的真实工号 — 这是「高级伪装」诈骗！利用真实身份降低戒心",
    ],
    tags: ["清空资金", "危险操作", "高级伪装诈骗"],
    risk: 88.5,
    analysis:
      "对方工号为真，但话术是诈骗！这是新型「高级伪装」诈骗：骗子先获取真实身份骗取信任，再实施诈骗。官方客服绝不会要求清空借贷平台资金！",
    terminalLines: [
      "[WARN] Dangerous operation detected: '清空资金'",
      "[CRITICAL] Cross-validation: Real employee ID + Fraudulent script = 'Deep Fake Agent' attack",
      "[INFO] Risk score updated: 72.6 → 88.5 (HIGH_RISK)",
      "[WARN] APPROACHING CRITICAL THRESHOLD (≥90)",
    ],
  },
  // 7. 恶意链接 - 分数突破90，触发弹窗
  {
    id: "link_1",
    type: "link",
    icon: "link",
    label: "链接模态",
    color: "#ef4444",
    timestamp: "2026/5/1 09:01:45",
    content:
      "[链接] https://pingan-consumer-finance.xyz/download 平安消费金融APP下载",
    steps: [
      "链接安全检测启动...",
      "域名分析 — pingan-consumer-finance.xyz",
      "安全评估 — 域名注册时间不足30天",
      "官方对比 — 与平安消费金融官方域名(pingan.com)不一致",
      "恶意检测 — 检测到可疑参数，可能用于追踪",
      "风险阈值突破 — 触发高危预警弹窗",
    ],
    tags: ["恶意链接", "虚假APP", "钓鱼网站", "高危预警"],
    risk: 92.4,
    analysis: "检测到陌生下载链接，点击有风险，将触发系统拦截",
    terminalLines: [
      "[WARN] Malicious link detected — domain unverified",
      "[CRITICAL] RISK THRESHOLD EXCEEDED (≥90) — triggering warning dialog",
      "[INFO] Risk score updated: 88.5 → 92.4 (CRITICAL_RISK)",
      "[ALERT] CRITICAL — immediate warning required",
    ],
  },
  // 8. 转账要求 - 最终确认
  {
    id: "text_4",
    type: "text",
    icon: "money",
    label: "文本模态",
    color: "#ef4444",
    timestamp: "2026/5/1 09:01:50",
    content:
      "客服小陈：您先在本平台贷款4万元，全汇入「平安消费金融」官方账户验证贷款资质，24小时内会原路返还，无记录，无需担心。",
    steps: [
      "NLP 语义解析启动...",
      "检测到核心诈骗意图",
      "命中高危关键词：「贷款」「转账」「官方账户」",
      "话术模式 — 要求转账汇款 (置信度 0.99)",
      "资金风险评估 — 直接经济损失风险",
      "模式匹配 — 注销校园贷最终环节",
    ],
    tags: ["转账汇款", "贷款诈骗", "资金损失"],
    risk: 98.7,
    analysis:
      "检测到汇款引导，为高度疑似的注销校园贷诈骗，您的财产安全正在受到严重威胁，切勿轻信！",
    terminalLines: [
      "[WARN] Transfer request detected: '贷款4万元'",
      "[INFO] Risk score updated: 92.4 → 98.7 (CRITICAL_RISK)",
      "[INFO] Generating AI analysis report...",
      "[INFO] Report generation complete",
    ],
  },
];

// 系统初始化终端日志
export const SYSTEM_INIT_LINES = [
  "[SYS]  Initializing multimodal capture engine v3.2.1...",
  "[SYS]  Loading NLP model: fraud-bert-v2 (1.2GB)... OK",
  "[SYS]  Loading OCR module: tesseract-cn + layout-detector... OK",
  "[SYS]  Loading audio pipeline: whisper-large-v3 + deepfake-v1... OK",
  "[INFO] Window capture service: READY",
  "[INFO] Target window hook: ATTACHED",
  "[INFO] Audio stream capture: ACTIVE",
  "[SYS]  Session ID: MFA-20260331-101523",
];

// AI 思考步骤
export const THINKING_STEPS = [
  { text: "正在解析多模态特征向量...", duration: 600 },
  { text: "话术模式匹配 — 命中「冒充客服注销校园贷」", duration: 800 },
  { text: "知识库比对 — 话术与历史诈骗案例相似度 78%", duration: 700 },
  { text: "图像鉴伪 — 工作证 PS 合成置信度 94%", duration: 900 },
  { text: "语音分析 — 胁迫性语气指数 0.89", duration: 700 },
  { text: "链接检测 — 恶意域名风险极高", duration: 700 },
  { text: "跨模态风险融合计算...", duration: 800 },
  { text: "生成研判结论与处置建议...", duration: 600 },
];

// 历史记录数据
export const initialHistoryItems = [
  {
    id: 1,
    title: "校园贷诈骗案例分析",
    createdAt: Date.now() - 86400000 * 5,
    isPinned: false,
  },
  {
    id: 2,
    title: "AI换脸识别技巧",
    createdAt: Date.now() - 86400000 * 3,
    isPinned: false,
  },
  {
    id: 3,
    title: "冒充公检法话术特征",
    createdAt: Date.now() - 86400000 * 2,
    isPinned: true,
  },
  {
    id: 4,
    title: "虚假投资平台识别",
    createdAt: Date.now() - 86400000 * 1,
    isPinned: false,
  },
  { id: 5, title: "96110反诈热线说明", createdAt: Date.now(), isPinned: false },
];

// 监护人列表
export const guardianList = [
  {
    id: 1,
    name: "李建国",
    relation: "父亲",
    phone: "138****6491",
    status: "已通知",
    avatar: "/icons/avatar2.jpg",
  },
  {
    id: 2,
    name: "王淑芬",
    relation: "母亲",
    phone: "139****4903",
    status: "已通知",
    avatar: "/icons/avatar3.jpg",
  },
  {
    id: 3,
    name: "陈立",
    relation: "叔叔",
    phone: "137****5397",
    status: "离线",
    avatar: "",
  },
  {
    id: 4,
    name: "张明远",
    relation: "班主任",
    phone: "134****2340",
    status: "离线",
    avatar: "/icons/avatar4.jpg",
  },
];
