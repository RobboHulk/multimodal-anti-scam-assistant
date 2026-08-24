// MessageList.jsx - 使用模拟数据的完整版本
import styles from "./MessageList.module.css";
import { useCallback, useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { mockGuardians, mockNewMessage } from "./mockGuardians";

const MessageList = ({ guardians: propGuardians, onSelectContact }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const [guardians, setGuardians] = useState([]);
  const timerRef = useRef(null);
  const navigate = useNavigate();

  // 初始化数据：优先使用传入的 guardians，否则使用模拟数据
  useEffect(() => {
    if (propGuardians && propGuardians.length > 0) {
      setGuardians(propGuardians);
    } else {
      setGuardians(mockGuardians);
    }
  }, [propGuardians]);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const handleMouseEnter = useCallback(() => {
    clearTimer();
    setShouldRender(true);
    requestAnimationFrame(() => {
      setIsVisible(true);
    });
  }, [clearTimer]);

  const handleMouseLeave = useCallback(() => {
    setIsVisible(false);
    timerRef.current = setTimeout(() => {
      setShouldRender(false);
    }, 300);
  }, []);

  useEffect(() => {
    return () => clearTimer();
  }, [clearTimer]);

  // 获取消息预览内容
  const getMessagePreview = (guardian) => {
    if (guardian.unread > 0) {
      return guardian.lastMsg || `有 ${guardian.unread} 条未读消息`;
    }
    return guardian.lastMsg || "暂无新消息";
  };

  // 获取最后消息时间
  const getLastTime = (guardian) => {
    return guardian.lastTime || guardian.lastActive || "未知";
  };

  // 获取头像文字
  const getAvatarText = (name) => {
    return name.charAt(0);
  };

  // 渲染头像
  const renderAvatar = (guardian) => {
    if (guardian.avatarType === "image" && guardian.avatar) {
      return (
        <img
          src={guardian.avatar}
          alt={guardian.name}
          className={styles.avatarImg}
          onError={(e) => {
            e.target.style.display = "none";
            e.target.nextSibling.style.display = "flex";
          }}
        />
      );
    }
    return (
      <span className={styles.avatarText}>
        {guardian.avatar || getAvatarText(guardian.name)}
      </span>
    );
  };

  // 处理点击消息项
  const handleItemClick = (guardian) => {
    // 标记消息为已读
    setGuardians((prev) =>
      prev.map((g) => (g.id === guardian.id ? { ...g, unread: 0 } : g)),
    );

    if (onSelectContact) {
      onSelectContact(guardian);
    } else {
      navigate(
        `/user/messages?contactId=${guardian.id}&contactName=${encodeURIComponent(guardian.name)}`,
      );
    }
  };

  // 计算总未读消息数
  const totalUnread =
    guardians?.reduce((sum, g) => sum + (g.unread || 0), 0) || 0;

  // 排序：未读消息置顶，然后按最后活跃时间排序
  const sortedGuardians = [...guardians].sort((a, b) => {
    if (a.unread > 0 && b.unread === 0) return -1;
    if (a.unread === 0 && b.unread > 0) return 1;
    // 按最后活跃时间排序（最新的在前）
    const timeA = a.lastTime || a.lastActive || "";
    const timeB = b.lastTime || b.lastActive || "";
    return timeB.localeCompare(timeA);
  });

  return (
    <div
      className={styles.container}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className={styles.btn}>
        <span className={`icon-bubbles4 ${styles.icon}`}></span>
        <span className={styles.text}>消息</span>
        {totalUnread > 0 && (
          <span className={styles.badge}>
            {totalUnread > 99 ? "99+" : totalUnread}
          </span>
        )}
      </div>

      {shouldRender && (
        <div
          className={`${styles.contentBox} ${isVisible ? styles.enter : styles.exit}`}
        >
          <div className={styles.content}>
            <div className={styles.tool}>
              <span>消息列表</span>
              <span className={styles.toolCount}>
                {guardians?.filter((g) => g.unread > 0).length || 0} 条未读
              </span>
            </div>
            <div className={styles.list}>
              {sortedGuardians && sortedGuardians.length > 0 ? (
                sortedGuardians.map((guardian) => (
                  <div
                    key={guardian.id}
                    className={`${styles.item} ${guardian.unread > 0 ? styles.unread : ""}`}
                    onClick={() => handleItemClick(guardian)}
                  >
                    <div className={styles.itemAvatar}>
                      {renderAvatar(guardian)}
                    </div>
                    <div className={styles.itemInfo}>
                      <div className={styles.itemHeader}>
                        <span className={styles.itemName}>
                          {guardian.name}
                          <span className={styles.itemRelation}>
                            {guardian.relation ? ` · ${guardian.relation}` : ""}
                          </span>
                        </span>
                        <span className={styles.itemTime}>
                          {getLastTime(guardian)}
                        </span>
                      </div>
                      <div className={styles.itemContent}>
                        <span className={styles.itemMsg}>
                          {getMessagePreview(guardian)}
                        </span>
                        {guardian.unread > 0 && (
                          <span className={styles.unreadBadge}>
                            {guardian.unread}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className={styles.empty}>
                  <span>暂无消息</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageList;
