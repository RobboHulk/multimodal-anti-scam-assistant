import { useState, useEffect, useRef, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Nav from "../../layouts/Nav/Nav";
import BackBtn from "../../components/BackBtn/BackBtn";
import styles from "./CaseDetail.module.css";

// ── SVG 图标（仅用于新增部分） ──
const SourceIcon = () => (
  <svg
    width="13"
    height="13"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
  >
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
);
const EyeIcon = () => (
  <svg
    width="13"
    height="13"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
  >
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);
const ListIcon = () => (
  <svg
    width="13"
    height="13"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
  >
    <line x1="8" y1="6" x2="21" y2="6" />
    <line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" />
    <line x1="3" y1="6" x2="3.01" y2="6" />
    <line x1="3" y1="12" x2="3.01" y2="12" />
    <line x1="3" y1="18" x2="3.01" y2="18" />
  </svg>
);

// ── 假案例数据（后端无数据时 fallback） ──
const MOCK_CASE = {
  id: 2001,
  title: "AI语音合成冒充老板，财务人员被骗15万",
  scamType: "AI诈骗",
  author: "央视新闻",
  createdAt: "2026-03-27T10:00:00",
  coverImage: "/icons/公司.png",
  confidence: "95%",
  content: `<p>2026年3月，某公司财务人员小王接到"总经理"的微信语音电话。电话那头的声音和总经理一模一样，语气也很急切："小王，我正在和客户谈一个紧急项目，需要马上转15万定金到对方账户，稍后补流程。"</p>

<p>小王听声音确实是总经理，没有多想就转了15万。转账后，小王遇到总经理本人，才发现总经理根本没打过电话。</p>

<h2>一、案件经过</h2>

<p>小王是某科技公司的财务人员，负责公司日常资金往来。2026年3月27日下午2点，他正在整理财务报表时，突然接到"张总经理"的微信语音电话。</p>

<p>"小王，我现在在外面见一个重要客户，项目谈得很顺利，但对方要求马上付15万定金才能锁定合同。你赶紧从公司账户转15万到这个账号，我稍后补流程。"电话那头的声音急切而熟悉。</p>

<p>小王听出确实是张总的声音，而且张总平时确实经常用微信语音安排工作。他没有多想，立即按照对方提供的账户信息，通过公司网银转了15万元。</p>

<p>转账成功后，小王给张总发微信确认："张总，15万已转，请查收。"没想到张总回复："什么15万？我没让你转账啊！"</p>

<p>小王顿时慌了神，立即拨打张总电话。张总表示自己一直在办公室开会，从未离开过公司，更没有通过微信语音要求转账。小王这才意识到自己遭遇了AI语音诈骗，立即报警。</p>

<div class="warningBox">
  <div class="warningTitle">
    <span>⚠️</span> 案件警示
  </div>
  <div class="warningText">
    财务人员要严格执行财务制度！大额转账必须当面或视频确认！AI语音合成技术已经能够完美模仿任何人声，仅凭声音不可信！
  </div>
</div>

<h2>二、诈骗手法分析</h2>

<p>本案中，诈骗分子采用了"语音获取+AI合成+精准诈骗"的组合手法：</p>

<p><strong>第一步：获取语音样本</strong><br/>
诈骗分子通过公司官网、微信公众号、抖音等渠道，搜索到张总在公开场合的演讲、采访视频，以及他在社交媒体上发布的语音消息，提取了足够的语音素材。</p>

<p><strong>第二步：AI语音合成</strong><br/>
利用开源的AI语音合成技术（如VALL-E、Bark等），将张总的语音样本输入模型，训练生成高度逼真的声音克隆模型。仅需3-10秒的语音样本，就能合成出以假乱真的声音。</p>

<p><strong>第三步：信息收集与目标锁定</strong><br/>
诈骗分子通过企查查、天眼查等平台获取公司组织架构和联系方式，锁定财务人员小王为目标，并通过公司官网找到张总的照片和个人简介。</p>

<p><strong>第四步：实施精准诈骗</strong><br/>
诈骗分子使用改号软件或虚拟号码，通过微信语音电话联系小王，利用AI合成的张总声音下达转账指令。他们还会制造紧急氛围，让受害人没有时间思考和核实。</p>

<h2>三、AI语音诈骗的识别要点</h2>

<p><strong>1. 声音细节可能存在瑕疵</strong><br/>
虽然AI合成的声音已经很逼真，但仍可能存在一些细微问题：语气不够自然、停顿位置异常、情绪表达生硬、缺乏背景噪音等。在嘈杂环境下，这些瑕疵更容易暴露。</p>

<p><strong>2. 要求做特定动作或回答私密问题</strong><br/>
如果对方自称是熟人，可以要求他说出只有你们知道的暗号、回忆共同经历的事情，或者要求对方做特定动作（如转头、摸鼻子等）。AI无法实时模拟这些互动。</p>

<p><strong>3. 警惕"紧急转账"话术</strong><br/>
任何以"紧急""保密""不要告诉别人"为由要求立即转账的，都应高度警惕。诈骗分子通常会制造时间压力，让你没有机会核实。</p>

<p><strong>4. 通过其他渠道二次确认</strong><br/>
接到转账指令后，无论对方多么着急，都应该通过其他方式（如拨打本人电话、当面确认、找第三方核实）进行二次确认。</p>

<h2>四、防范建议</h2>

<p><strong>1. 严格执行财务制度</strong><br/>
企业应建立严格的财务审批流程：大额转账必须经过书面审批或至少两种以上方式确认（如电话+当面确认）。财务人员要养成"先核实后转账"的习惯。</p>

<p><strong>2. 设置转账"双重确认"机制</strong><br/>
建议企业设置转账"双重确认"机制：单笔超过一定金额的转账，需要财务主管或总经理本人二次确认才能完成。</p>

<p><strong>3. 保护个人语音信息</strong><br/>
建议不要在公开场合（如抖音、视频号、公开演讲）过多暴露自己的语音信息。家人之间可以约定一个"转账暗号"，用于紧急情况下的身份确认。</p>

<p><strong>4. 定期进行反诈培训</strong><br/>
企业应定期组织员工参加反诈培训，特别是财务人员。培训内容应包括：最新诈骗手法、识别技巧、应急处置流程等。</p>

<p><strong>5. 下载国家反诈中心APP</strong><br/>
建议所有手机用户安装"国家反诈中心"APP并开启来电预警功能。该APP可以识别标记为诈骗的电话和短信，有效降低被骗风险。</p>

<h2>五、受骗后怎么办</h2>

<p><strong>第一步：立即报警</strong><br/>
拨打110报警，同时拨打96110反诈专线。提供诈骗分子的电话号码、微信账号、转账账户等关键信息。</p>

<p><strong>第二步：联系银行止付</strong><br/>
立即联系转账银行，申请对涉案账户进行紧急止付。越快行动，追回资金的可能性越大。</p>

<p><strong>第三步：保留证据</strong><br/>
保存所有相关证据：通话录音、聊天记录、转账凭证、对方账号信息等，这些证据对警方破案至关重要。</p>

<p><strong>第四步：通知相关方</strong><br/>
如果是公司资金被骗，应立即通知公司管理层和相关同事，防止诈骗分子利用同样手法继续行骗。</p>`,
};

const MOCK_RELATED = [
  {
    id: 2002,
    title: "AI换脸冒充表哥借钱，小伙险被骗5万元",
    scamType: "AI换脸诈骗",
    createdAt: "2026-03-27",
  },
  {
    id: 2003,
    title: "AI拟声冒充孙子，七旬老人被骗2万元养老金",
    scamType: "AI语音诈骗",
    createdAt: "2026-03-28",
  },
  {
    id: 2004,
    title: "网恋'高富帅'诱导投资，系统及时预警挽损",
    scamType: "杀猪盘",
    createdAt: "2026-03-26",
  },
  {
    id: 2005,
    title: "追星女孩遭遇'假警察'，奶奶10万积蓄被骗光",
    scamType: "追星诈骗",
    createdAt: "2026-03-28",
  },
];

const CaseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [relatedArticles, setRelatedArticles] = useState([]);
  const [toc, setToc] = useState([]);
  const [activeTocId, setActiveTocId] = useState("");
  const contentRef = useRef(null);
  const isScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef(null);
  const layoutRef = useRef(null);

  // 从顶端阅读时，重置页面滚动
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [id]);

  // 获取案例详情
  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const response = await fetch(`/api/cases/list?current=1&size=200`);
        const result = await response.json();
        if (
          result.code === 200 &&
          result.data &&
          result.data.records &&
          result.data.records.length > 0
        ) {
          const found = result.data.records.find(
            (item) => String(item.id) === String(id),
          );
          if (found) {
            setArticle(found);
            const related = result.data.records
              .filter((item) => item.id !== found.id)
              .slice(0, 4);
            setRelatedArticles(related);
            setLoading(false);
            return;
          }
        }
      } catch (e) {
        // fallback to mock
      }
      // Mock fallback — 使用案例数据
      setArticle(MOCK_CASE);
      setRelatedArticles(MOCK_RELATED);
      setLoading(false);
    };
    fetchDetail();
  }, [id]);

  // 提取 TOC - 为每个标题生成唯一且稳定的ID
  useEffect(() => {
    if (!contentRef.current || loading) return;

    const extractTOC = () => {
      const headings = contentRef.current.querySelectorAll("h2, h3, h4");
      if (headings.length === 0) return;

      const items = Array.from(headings).map((h, i) => {
        // 生成基于文本内容的唯一ID
        const textId = h.textContent
          .toLowerCase()
          .replace(/[^\u4e00-\u9fa5a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
        const tocId = `${textId}-${i}`;
        h.id = tocId;
        return { id: tocId, text: h.textContent, level: h.tagName };
      });
      setToc(items);
    };

    const timer = setTimeout(extractTOC, 100);
    return () => clearTimeout(timer);
  }, [article, loading]);

  // 滚动高亮 TOC（优化版）
  useEffect(() => {
    if (toc.length === 0) return;

    const handleScroll = () => {
      // 如果正在程序化滚动，暂时不更新高亮
      if (isScrollingRef.current) return;

      // 获取所有标题元素
      const headings = toc
        .map((item) => document.getElementById(item.id))
        .filter(Boolean);

      if (headings.length === 0) return;

      // 获取滚动位置
      const scrollY = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = document.documentElement.scrollHeight;

      // 检查是否滚动到底部（距离底部100px内）
      if (scrollY + windowHeight >= documentHeight - 100) {
        const lastId = toc[toc.length - 1]?.id;
        if (lastId && activeTocId !== lastId) {
          setActiveTocId(lastId);
        }
        return;
      }

      // 找到当前滚动位置对应的标题
      let currentActiveId = "";

      // 从后往前找，找到第一个在视口上方的标题
      for (let i = headings.length - 1; i >= 0; i--) {
        const heading = headings[i];
        const rect = heading.getBoundingClientRect();
        // 如果标题顶部在视口上方或刚好在顶部附近（偏移80px导航栏高度）
        if (rect.top <= 120) {
          currentActiveId = toc[i].id;
          break;
        }
      }

      // 如果没有找到，使用第一个标题
      if (!currentActiveId && headings.length > 0) {
        currentActiveId = toc[0].id;
      }

      if (currentActiveId && activeTocId !== currentActiveId) {
        setActiveTocId(currentActiveId);
      }
    };

    // 使用 requestAnimationFrame 节流
    let ticking = false;
    const throttledScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener("scroll", throttledScroll);
    handleScroll(); // 初始调用

    return () => window.removeEventListener("scroll", throttledScroll);
  }, [toc, activeTocId]);

  // 平滑滚动到指定元素（优化版）
  const scrollToElement = (elementId) => {
    const element = document.getElementById(elementId);
    if (!element) return;

    // 设置滚动标志，防止滚动时频繁更新高亮
    isScrollingRef.current = true;

    // 清除之前的定时器
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - 80; // 80px 导航栏高度

    window.scrollTo({
      top: offsetPosition,
      behavior: "smooth",
    });

    // 立即更新激活状态
    setActiveTocId(elementId);

    // 滚动结束后恢复高亮更新
    scrollTimeoutRef.current = setTimeout(() => {
      isScrollingRef.current = false;
    }, 500);
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  // 排版算法
  const renderFormattedContent = (htmlContent) => {
    if (!htmlContent) return null;

    let processedHtml = htmlContent;
    processedHtml = processedHtml.replace(
      /<(h2|h3|h4)>([\s\S]*?)<\/\1>/gi,
      (match, tag, content) => {
        // 生成基于文本内容的 ID
        const textId = content
          .toLowerCase()
          .replace(/[^\u4e00-\u9fa5a-z0-9]+/g, "-")
          .replace(/^-|-$/g, "");
        // 使用更简单的 ID 格式，不依赖索引
        const id = textId;
        return `<${tag} id="${id}">${content}</${tag}>`;
      },
    );

    const insertImages = [
      {
        src: "/icons/语音合成.png",
        caption: "AI语音合成技术原理示意图——仅需少量语音样本即可克隆声音",
        className: styles.fullWidthImg,
      },
      {
        src: "/icons/语音诈骗.png",
        caption: "财务人员遭遇AI语音诈骗流程解析——从语音获取到紧急转账",
        className: styles.fullWidthImg,
      },
      {
        src: "https://assets.codepen.io/467/2020-08-26+-+10-00-36_00025.jpg",
        caption: "平台实时风控监控中心",
        className: styles.fullWidthImg,
      },
    ];

    let pCount = 0;
    let imgIndex = 0;
    let firstPMatched = false;

    processedHtml = processedHtml.replace(
      /<p(.*?)>([\s\S]*?)<\/p>/gi,
      (match, prefix, content) => {
        let replacementHtml = match;
        if (!firstPMatched) {
          firstPMatched = true;
          replacementHtml = `<p${prefix} class="introText">${content}</p>`;
        } else {
          pCount++;
          if (
            (pCount === 2 || pCount === 4) &&
            imgIndex < insertImages.length
          ) {
            const imgData = insertImages[imgIndex];
            imgIndex++;
            const figureClass = imgData.className
              ? `class="${imgData.className}"`
              : "";
            const figureHtml = `
            <figure ${figureClass} style="margin: 0; padding: 0;">
                <img src="${imgData.src}" alt="illustration" />
                <figcaption class="${styles.caption}">${imgData.caption}</figcaption>
            </figure>
          `;
            replacementHtml = replacementHtml + figureHtml;
          }
        }
        return replacementHtml;
      },
    );

    return (
      <div
        ref={contentRef}
        className={styles.articleBody}
        dangerouslySetInnerHTML={{ __html: processedHtml }}
      />
    );
  };

  // 封面图逻辑
  const defaultImages = [
    "https://assets.codepen.io/467/2020-08-26+-+09-30-18_00007+copy.jpg",
    "https://images.unsplash.com/photo-1586281380349-632531db7ed4?q=80&w=2070&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1549692520-acc6669e2f0c?q=80&w=1974&auto=format&fit=crop",
  ];

  const getCoverImage = () => {
    const defaultImg = defaultImages[parseInt(id || 0) % defaultImages.length];
    return article?.coverImage || defaultImg;
  };

  const fakeViews = useMemo(() => Math.floor(Math.random() * 5000 + 800), [id]);
  const fakeSource = useMemo(
    () =>
      ["人民网", "新华网", "公安部反诈中心", "央视新闻", "法治日报"][
        parseInt(id || 0) % 5
      ],
    [id],
  );

  return (
    <>
      <Nav />
      <div className={styles.pageLayout} ref={layoutRef}>
        <button className={styles.backBtn} onClick={() => navigate(-1)}>
          ← 返回探索
        </button>

        {loading ? (
          <div className={styles.loading}>加载案例详情中...</div>
        ) : article ? (
          <div className={styles.detailLayout}>
            {/* ── 主内容 ── */}
            <div className={styles.detailMain}>
              <div className={styles.header}>
                <img
                  className={styles.headerImg}
                  src={getCoverImage()}
                  alt="Case Cover"
                />
                <div className={styles.headerGroup}>
                  <h3 className={styles.label}>
                    {article.scamType || "诈骗案例 · Case Study"}
                  </h3>
                  {/* 置信度徽章 */}
                  <div className={styles.confidenceBadge}>
                    <span className={styles.confidenceLabel}>
                      AI 分析置信度
                    </span>
                    <span className={styles.confidenceValue}>
                      {article.confidence || "96%"}
                    </span>
                  </div>
                  <h1 className={styles.primaryHeadline}>{article.title}</h1>
                  {/* 元信息条 */}
                  <div className={styles.metaBar}>
                    <span className={styles.metaItem}>
                      <SourceIcon /> {fakeSource}
                    </span>
                    <span className={styles.metaDot}>·</span>
                    <span className={styles.metaItem}>
                      <EyeIcon /> {fakeViews.toLocaleString()} 次阅读
                    </span>
                  </div>
                  <h3 className={styles.byline}>
                    {article.author || "多模态反诈智库研究中心"}
                  </h3>
                  <h4 className={styles.dateline}>
                    {article.createdAt || "最新案例发布"}
                  </h4>
                </div>
              </div>

              {renderFormattedContent(article.content)}

              {/* 相关推荐 */}
              {relatedArticles.length > 0 && (
                <div className={styles.relatedSection}>
                  <h3 className={styles.relatedTitle}>相关案例推荐</h3>
                  <div className={styles.relatedGrid}>
                    {relatedArticles.map((r) => (
                      <a
                        key={r.id}
                        href={`/case/${r.id}`}
                        className={styles.relatedCard}
                      >
                        <span className={styles.relatedCat}>
                          {r.scamType || "诈骗案例"}
                        </span>
                        <h4 className={styles.relatedCardTitle}>{r.title}</h4>
                        <span className={styles.relatedDate}>
                          {(r.createdAt || "").split("T")[0]}
                        </span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 右侧 TOC 目录 */}
            {toc.length > 0 && (
              <aside className={styles.tocSidebar}>
                <div className={styles.tocBox}>
                  <div className={styles.tocHeader}>
                    <ListIcon /> 目录导航
                  </div>
                  <nav className={styles.tocNav}>
                    {toc.map((item) => (
                      <a
                        key={item.id}
                        href={`#${item.id}`}
                        className={`${styles.tocItem} ${
                          item.level !== "H2" ? styles.tocIndent : ""
                        } ${activeTocId === item.id ? styles.tocActive : ""}`}
                        onClick={(e) => {
                          e.preventDefault();
                          scrollToElement(item.id);
                        }}
                      >
                        {item.text}
                      </a>
                    ))}
                  </nav>
                </div>
              </aside>
            )}
          </div>
        ) : (
          <div className={styles.emptyState}>案例不存在或已被移出资料库</div>
        )}
        <BackBtn targetRef={layoutRef} scrollThreshold={600} />
      </div>
    </>
  );
};

export default CaseDetail;
