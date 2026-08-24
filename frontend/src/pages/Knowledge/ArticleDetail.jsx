// ArticleDetail.jsx - 知识库文章详情页（简化版）
import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import Nav from "../../layouts/Nav/Nav";
import BackBtn from "../../components/BackBtn/BackBtn";
import styles from "./ArticleDetail.module.css";
import { getLocalArticleById, getLocalRelatedArticles } from "../../api/knowledgeDataService";

const TYPE_COLORS = {
  "冒充公检法": "#ef4444",
  "冒充客服": "#f97316",
  "虚假投资理财": "#eab308",
  "网络贷款诈骗": "#84cc16",
  "刷单返利": "#22c55e",
  "杀猪盘": "#06b6d4",
  "冒充亲友": "#3b82f6",
  "钓鱼链接": "#8b5cf6",
  "游戏诈骗": "#ec4899",
  "虚假购物": "#f43f5e",
  "其他诈骗": "#6b7280",
};

const ArticleDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const layoutRef = useRef(null);

  const [article, setArticle] = useState(null);
  const [relatedArticles, setRelatedArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 获取文章详情
  useEffect(() => {
    const fetchArticle = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem("token");
        let articleData = null;

        try {
          const res = await fetch(`/api/knowledge/${id}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });
          if (res.ok) {
            const json = await res.json();
            if (json.code === 200 && json.data) {
              articleData = json.data;
            }
          }
        } catch {
          // 网络错误，回退到本地
        }

        if (!articleData) {
          articleData = getLocalArticleById(id);
        }

        if (articleData) {
          setArticle(articleData);
          fetchRelated(articleData.id);
        } else {
          setError("文章不存在");
        }
      } catch (e) {
        console.error("获取文章失败:", e);
        const localArticle = getLocalArticleById(id);
        if (localArticle) {
          setArticle(localArticle);
          fetchRelated(localArticle.id);
        } else {
          setError("网络错误，请稍后重试");
        }
      } finally {
        setLoading(false);
      }
    };

    const fetchRelated = async (articleId) => {
      try {
        const token = localStorage.getItem("token");
        let relatedData = null;

        try {
          const res = await fetch(`/api/knowledge/related?id=${articleId}&limit=4`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          });
          if (res.ok) {
            const json = await res.json();
            if (json.code === 200 && json.data && json.data.length > 0) {
              relatedData = json.data;
            }
          }
        } catch {
          // 网络错误，回退到本地
        }

        if (!relatedData) {
          relatedData = getLocalRelatedArticles(articleId, 4);
        }

        setRelatedArticles(relatedData || []);
      } catch (e) {
        console.error("获取相关文章失败:", e);
        setRelatedArticles(getLocalRelatedArticles(articleId, 4));
      }
    };

    if (id) {
      fetchArticle();
    }
  }, [id]);

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <>
        <Nav />
        <div className={styles.container}>
          <div className={styles.loadingState}>
            <div className={styles.loadingSpinner}></div>
            加载中...
          </div>
        </div>
      </>
    );
  }

  if (error || !article) {
    return (
      <>
        <Nav />
        <div className={styles.container}>
          <div className={styles.errorState}>
            <p>{error || "文章不存在"}</p>
            <button onClick={() => navigate("/knowledge")}>返回知识库</button>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Nav />
      <div className={styles.container} ref={layoutRef}>
        <article className={styles.articleWrapper}>
          {/* 文章头部 */}
          <header className={styles.articleHeader}>
            <div className={styles.breadcrumb}>
              <Link to="/knowledge">知识库</Link>
              <span className={styles.breadcrumbSep}>/</span>
              <span>{article.scamType}</span>
            </div>
            <h1 className={styles.articleTitle}>{article.title}</h1>
            <div className={styles.articleMeta}>
              <span
                className={styles.typeTag}
                style={{ backgroundColor: TYPE_COLORS[article.scamType] || "#6b7280" }}
              >
                {article.scamType}
              </span>
              <span className={styles.metaItem}>
                来源：{article.source || "未知来源"}
              </span>
              <span className={styles.metaItem}>
                发布时间：{formatDate(article.createdAt)}
              </span>
            </div>
          </header>

          {/* 文章正文 */}
          <div className={styles.articleContent}>
            <ContentRenderer content={article.content} />
          </div>

          {/* 标签 */}
          {article.tags && (
            <div className={styles.tagsSection}>
              <span className={styles.tagsLabel}>标签：</span>
              {article.tags.split(",").map((tag, i) => (
                <span key={i} className={styles.tag}>
                  {tag.trim()}
                </span>
              ))}
            </div>
          )}
        </article>

        {/* 相关文章 */}
        {relatedArticles.length > 0 && (
          <aside className={styles.relatedSection}>
            <h3 className={styles.relatedTitle}>相关文章</h3>
            <div className={styles.relatedList}>
              {relatedArticles.map((r) => (
                <Link
                  key={r.id}
                  to={`/article/${r.id}`}
                  className={styles.relatedItem}
                >
                  <span
                    className={styles.relatedType}
                    style={{ backgroundColor: TYPE_COLORS[r.scamType] || "#6b7280" }}
                  >
                    {r.scamType}
                  </span>
                  <span className={styles.relatedItemTitle}>{r.title}</span>
                </Link>
              ))}
            </div>
          </aside>
        )}

        <BackBtn targetRef={layoutRef} scrollThreshold={400} />
      </div>
    </>
  );
};

// 内容渲染器：将纯文本转换为格式化的段落
function ContentRenderer({ content }) {
  if (!content) return null;

  // 按换行符分割，处理连续换行
  const paragraphs = content.split(/\n+/).filter((p) => p.trim());

  return (
    <>
      {paragraphs.map((para, i) => {
        const trimmed = para.trim();

        // 检测标题格式
        if (trimmed.startsWith("# ")) {
          return <h2 key={i}>{trimmed.slice(2)}</h2>;
        }
        if (trimmed.startsWith("## ")) {
          return <h3 key={i}>{trimmed.slice(3)}</h3>;
        }
        if (trimmed.startsWith("### ")) {
          return <h4 key={i}>{trimmed.slice(4)}</h4>;
        }

        // 检测数字序号开头（如 "1." "01" "1、" "一、"）
        if (/^(\d+[.、]|[一二三四五六七八九十]+[、.])/.test(trimmed)) {
          return (
            <p key={i} className={styles.numberedPara}>
              <strong>{trimmed}</strong>
            </p>
          );
        }

        // 检测列表项
        if (trimmed.startsWith("- ") || trimmed.startsWith("• ") || trimmed.startsWith("* ")) {
          return (
            <p key={i} className={styles.listItem}>
              • {trimmed.slice(2)}
            </p>
          );
        }

        // 普通段落
        return <p key={i}>{trimmed}</p>;
      })}
    </>
  );
}

export default ArticleDetail;
