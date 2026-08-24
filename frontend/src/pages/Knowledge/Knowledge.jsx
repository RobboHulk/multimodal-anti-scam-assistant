import { useState, useMemo, useCallback, useRef } from "react";
import Nav from "../../layouts/Nav/Nav";
import styles from "./Knowledge.module.css";
import knowledgeData from "../../data/knowledgeData";

const CATEGORIES = ["全部", "法律法规", "案例警示", "防范指南", "反诈科普"];
const PAGE_SIZE = 20;

const CATEGORY_COLORS = {
  "法律法规": "#f59e0b",
  "案例警示": "#ef4444",
  "防范指南": "#10b981",
  "反诈科普": "#3b82f6",
};

const Knowledge = () => {
  const [searchKeyword, setSearchKeyword] = useState("");
  const [activeCategory, setActiveCategory] = useState("全部");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem("veritide_favorites");
    return saved ? JSON.parse(saved) : [];
  });
  const [readProgress, setReadProgress] = useState(0);
  const modalBodyRef = useRef(null);

  // 计算阅读时间（假设中文阅读速度 400 字/分钟）
  const getReadingTime = (text) => {
    if (!text) return 1;
    const chars = text.replace(/\s/g, "").length;
    return Math.max(1, Math.ceil(chars / 400));
  };

  // 收藏文章
  const toggleFavorite = useCallback((articleId) => {
    setFavorites((prev) => {
      const newFavs = prev.includes(articleId)
        ? prev.filter((id) => id !== articleId)
        : [...prev, articleId];
      localStorage.setItem("veritide_favorites", JSON.stringify(newFavs));
      return newFavs;
    });
  }, []);

  // 分享文章
  const shareArticle = useCallback((article) => {
    const shareUrl = `${window.location.origin}${window.location.pathname}?article=${article.id}`;
    navigator.clipboard.writeText(shareUrl).then(() => {
      alert("链接已复制到剪贴板");
    });
  }, []);

  // 处理滚动进度
  const handleModalScroll = useCallback(() => {
    if (!modalBodyRef.current) return;
    const el = modalBodyRef.current;
    const scrollTop = el.scrollTop;
    const scrollHeight = el.scrollHeight - el.clientHeight;
    const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 100;
    setReadProgress(progress);
  }, []);

  // 高亮关键词
  const highlightText = (text) => {
    const keywords = ["诈骗", "骗子", "警惕", "防范", "注意", "切勿", "谨慎", "陷阱", "套路", "钱财", "转账", "汇款", "验证码", "银行卡", "个人信息"];
    let result = text;
    keywords.forEach((kw) => {
      result = result.replace(new RegExp(kw, "g"), `<strong>${kw}</strong>`);
    });
    return result;
  };

  // FILTERED_DATA
  const filteredData = useMemo(() => {
    let data = knowledgeData;
    if (activeCategory !== "全部") {
      data = data.filter((item) => item.category === activeCategory);
    }
    if (searchKeyword.trim()) {
      const kw = searchKeyword.trim().toLowerCase();
      data = data.filter((item) => item.title.toLowerCase().includes(kw));
    }
    return data;
  }, [activeCategory, searchKeyword]);

  const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredData.slice(start, start + PAGE_SIZE);
  }, [filteredData, currentPage]);

  const handleCategoryChange = (cat) => {
    setActiveCategory(cat);
    setCurrentPage(1);
  };

  const handleSearch = (e) => {
    setSearchKeyword(e.target.value);
    setCurrentPage(1);
  };

  const saveReadHistory = useCallback((article) => {
    const record = {
      id: article.id,
      title: article.title,
      category: article.category,
      readAt: Date.now(),
      readTime: Date.now(),
      coverImage: `https://picsum.photos/seed/${article.id}/400/240`,
    };
    const key = "veritide_knowledge_history";
    const saved = JSON.parse(localStorage.getItem(key) || "[]");
    const filtered = saved.filter((r) => r.id !== article.id);
    const updated = [record, ...filtered].slice(0, 100);
    localStorage.setItem(key, JSON.stringify(updated));
  }, []);

  const handleReadArticle = (article) => {
    saveReadHistory(article);
    setSelectedArticle(article);
  };

  const closeModal = () => {
    setSelectedArticle(null);
    setReadProgress(0);
  };

  const renderPagination = () => {
    if (totalPages <= 1) return null;
    const pages = [];
    const maxVisible = 7;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }
    if (startPage > 1) {
      pages.push(<button key={1} className={`${styles.pageBtn} ${currentPage === 1 ? styles.activePage : ""}`} onClick={() => setCurrentPage(1)}>1</button>);
      if (startPage > 2) pages.push(<span key="e1" className={styles.ellipsis}>...</span>);
    }
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button key={i} className={`${styles.pageBtn} ${currentPage === i ? styles.activePage : ""}`} onClick={() => setCurrentPage(i)}>{i}</button>
      );
    }
    if (endPage < totalPages) {
      if (endPage < totalPages - 1) pages.push(<span key="e2" className={styles.ellipsis}>...</span>);
      pages.push(<button key={totalPages} className={`${styles.pageBtn} ${currentPage === totalPages ? styles.activePage : ""}`} onClick={() => setCurrentPage(totalPages)}>{totalPages}</button>);
    }
    return (
      <div className={styles.pagination}>
        <button className={styles.pageNavBtn} disabled={currentPage === 1} onClick={() => setCurrentPage((p) => p - 1)}>&laquo; 上一页</button>
        <div className={styles.pageNumbers}>{pages}</div>
        <button className={styles.pageNavBtn} disabled={currentPage === totalPages} onClick={() => setCurrentPage((p) => p + 1)}>下一页 &raquo;</button>
      </div>
    );
  };

  return (
    <div className={styles.pageWrapper}>
      <Nav />
      <div className={styles.container}>
        <header className={styles.header}>
          <h1 className={styles.title}>威胁情报库</h1>
          <p className={styles.subtitle}>实时聚合全网权威防护资讯，共收录 {knowledgeData.length} 篇文章</p>
        </header>

        <div className={styles.toolbar}>
          <div className={styles.categories}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                className={`${styles.catBtn} ${activeCategory === cat ? styles.catBtnActive : ""}`}
                onClick={() => handleCategoryChange(cat)}
              >{cat}</button>
            ))}
          </div>
          <div className={styles.searchBox}>
            <svg className={styles.searchIcon} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              type="text"
              className={styles.searchInput}
              placeholder="搜索文章标题..."
              value={searchKeyword}
              onChange={handleSearch}
            />
          </div>
        </div>

        {filteredData.length === 0 ? (
          <div className={styles.empty}>
            <svg className={styles.emptyIcon} width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              <line x1="8" y1="11" x2="14" y2="11"/>
            </svg>
            <p className={styles.emptyText}>暂无匹配的文章</p>
            <p className={styles.emptyHint}>试试其他关键词或分类</p>
          </div>
        ) : (
          <>
            <div className={styles.grid}>
              {paginatedData.map((article) => (
                <div key={article.id} className={styles.card}>
                  <div className={styles.cardCover}>
                    <img
                      src={`https://picsum.photos/seed/${article.id}/400/240`}
                      alt={article.title}
                      className={styles.coverImg}
                      loading="lazy"
                    />
                    <span className={styles.badge} style={{ backgroundColor: CATEGORY_COLORS[article.category] || "#3b82f6" }}>
                      {article.category}
                    </span>
                  </div>
                  <div className={styles.cardBody}>
                    <h3 className={styles.cardTitle}>{article.title}</h3>
                    <p className={styles.cardContent}>{article.content.replace(/\n/g, " ")}</p>
                    <button className={styles.readBtn} onClick={() => handleReadArticle(article)}>阅读全文</button>
                  </div>
                </div>
              ))}
            </div>
            {renderPagination()}
          </>
        )}
      </div>

      {selectedArticle && (
        <div className={styles.modalOverlay} onClick={closeModal}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.readingProgressBar} style={{ width: `${readProgress}%` }} />
            <button className={styles.modalClose} onClick={closeModal}>&times;</button>
            <div className={styles.modalHeader}>
              <span className={styles.modalBadge} style={{ backgroundColor: CATEGORY_COLORS[selectedArticle.category] || "#3b82f6" }}>
                {selectedArticle.category}
              </span>
              <h2 className={styles.modalTitle}>{selectedArticle.title}</h2>
              <div className={styles.modalMeta}>
                <span className={styles.readingTime}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/>
                  </svg>
                  约 {getReadingTime(selectedArticle.fullContent)} 分钟阅读
                </span>
                <span className={styles.wordCount}>
                  {selectedArticle.fullContent.replace(/\s/g, "").length} 字
                </span>
              </div>
              <div className={styles.modalActions}>
                <button
                  className={`${styles.actionBtn} ${favorites.includes(selectedArticle.id) ? styles.favorited : ""}`}
                  onClick={() => toggleFavorite(selectedArticle.id)}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill={favorites.includes(selectedArticle.id) ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                  </svg>
                  {favorites.includes(selectedArticle.id) ? "已收藏" : "收藏"}
                </button>
                <button className={styles.actionBtn} onClick={() => shareArticle(selectedArticle)}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                  </svg>
                  分享
                </button>
              </div>
            </div>
            <div className={styles.modalBody} ref={modalBodyRef} onScroll={handleModalScroll}>
              {selectedArticle.fullContent.split("\n").map((para, i) => (
                para.trim() ? (
                  <p key={i} className={styles.modalPara} style={{ animationDelay: `${i * 0.03}s` }}
                    dangerouslySetInnerHTML={{ __html: highlightText(para) }} />
                ) : null
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Knowledge;
