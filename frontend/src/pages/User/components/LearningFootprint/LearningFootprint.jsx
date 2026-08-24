import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./LearningFootprint.module.css";

const HISTORY_KEY = "veritide_knowledge_history";

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return "";
  const now = Date.now();
  const diff = now - new Date(timestamp).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "刚刚";
  if (minutes < 60) return `${minutes}分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "昨天";
  if (days < 7) return `${days}天前`;
  if (days < 30) return `${Math.floor(days / 7)}周前`;
  return `${Math.floor(days / 30)}个月前`;
};

const LearningFootprint = () => {
  const [historyData, setHistoryData] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const saved = localStorage.getItem(HISTORY_KEY);
    if (saved) {
      try {
        setHistoryData(JSON.parse(saved));
      } catch {}
    }
  }, []);

  const filteredData = searchTerm.trim()
    ? historyData.filter((item) =>
        item.title.toLowerCase().includes(searchTerm.trim().toLowerCase())
      )
    : historyData;

  const handleClearAll = () => {
    if (window.confirm("确定要清空所有浏览记录吗？")) {
      localStorage.removeItem(HISTORY_KEY);
      setHistoryData([]);
    }
  };

  const handleRemoveItem = (id) => {
    const updated = historyData.filter((item) => item.id !== id);
    setHistoryData(updated);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.info}>
          <h1 className={styles.title}>浏览记录</h1>
          <div className={styles.subTitle}>
            您在威胁情报知识库的阅读足迹
          </div>
        </div>
        {historyData.length > 0 && (
          <button className={styles.clearAllBtn} onClick={handleClearAll}>
            清空记录
          </button>
        )}
      </header>

      <div className={styles.content}>
        {historyData.length > 0 && (
          <div className={styles.topBar}>
            <div className={styles.searchBox}>
              <input
                type="text"
                placeholder="搜索浏览记录..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                autoComplete="off"
              />
              {searchTerm && (
                <button className={styles.clearBtn} onClick={() => setSearchTerm("")}>
                  ×
                </button>
              )}
            </div>
            <span className={styles.countHint}>共 {filteredData.length} 条记录</span>
          </div>
        )}

        {filteredData.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>📖</div>
            <p>{searchTerm ? "没有找到匹配的记录" : "暂无浏览记录"}</p>
            {!searchTerm && (
              <button
                className={styles.goKnowledgeBtn}
                onClick={() => navigate("/knowledge")}
              >
                去知识库看看
              </button>
            )}
          </div>
        ) : (
          <div className={styles.cardsGrid}>
            {filteredData.map((item, index) => (
              <div
                key={item.id}
                className={styles.card}
                style={{ animationDelay: `${index * 0.05}s` }}
                onClick={() => navigate("/knowledge")}
              >
                <div className={styles.cardImage}>
                  <img src={item.coverImage} alt={item.title} loading="lazy" />
                </div>
                <div className={styles.cardContent}>
                  <h4 className={styles.cardTitle}>{item.title}</h4>
                  <div className={styles.cardMeta}>
                    {item.category && (
                      <span className={styles.categoryBadge}>{item.category}</span>
                    )}
                    <span className={styles.cardTime}>
                      {formatRelativeTime(item.readTime || item.timestamp)}
                    </span>
                    <button
                      className={styles.removeBtn}
                      onClick={(e) => { e.stopPropagation(); handleRemoveItem(item.id); }}
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningFootprint;
