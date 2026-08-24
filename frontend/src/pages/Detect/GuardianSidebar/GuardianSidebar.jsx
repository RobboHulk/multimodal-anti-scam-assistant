// src/pages/Detect/GuardianSidebar.jsx
import { useState, useEffect } from "react";
import styles from "./GuardianSidebar.module.css";
import Icons from "../../../data/detectIcons";

const GuardianSidebar = ({ isOpen, onClose, guardians, onNotify }) => {
  const [isVisible, setIsVisible] = useState(false);
  // 存储每个头像加载失败的状态
  const [imgErrors, setImgErrors] = useState({});

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
    } else {
      const timer = setTimeout(() => setIsVisible(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const getStatusClass = (status) => {
    if (status === "在线") return styles.statusOnline;
    if (status === "已通知") return styles.statusNotified;
    return styles.statusOffline;
  };

  // 获取头像图片路径
  const getAvatarSrc = (guardian) => {
    if (guardian.avatar && guardian.avatar.trim() !== "") {
      return guardian.avatar;
    }
    return null;
  };

  // 获取头像 fallback 文字（名字第一个字）
  const getAvatarFallbackText = (guardian) => {
    return guardian.name?.charAt(0) || "无";
  };

  // 处理图片加载失败
  const handleImageError = (guardianId) => {
    setImgErrors((prev) => ({ ...prev, [guardianId]: true }));
  };

  // 判断是否应该显示图片（有头像路径且未加载失败）
  const shouldShowImage = (guardian) => {
    const avatarSrc = getAvatarSrc(guardian);
    return avatarSrc && !imgErrors[guardian.id];
  };

  const getStatusText = (status) => {
    if (status === "在线") return "在线";
    if (status === "已通知")
      return <span className={styles.notice}>{Icons.notice} 已通知</span>;
    return "离线";
  };

  return (
    <>
      {isVisible && (
        <div
          className={`${styles.sidebar} ${isOpen ? styles.open : styles.closed}`}
        >
          <div className={styles.header}>
            <div className={styles.title}>
              <span className={styles.icon}>{Icons.guardian}</span>
              <h3>紧急通知</h3>
            </div>
            <button className={styles.closeBtn} onClick={onClose}>
              ×
            </button>
          </div>

          <div className={styles.content}>
            <div className={styles.sectionTitle}>
              <span>{Icons.guardians} 我的监护人</span>
            </div>
            <div className={styles.guardianList}>
              {guardians.map((guardian) => (
                <div key={guardian.id} className={styles.guardianCard}>
                  <div className={styles.guardianAvatar}>
                    {shouldShowImage(guardian) ? (
                      <img
                        src={getAvatarSrc(guardian)}
                        alt={guardian.name}
                        className={styles.avatarImg}
                        onError={() => handleImageError(guardian.id)}
                      />
                    ) : (
                      <div className={styles.avatarFallback}>
                        {getAvatarFallbackText(guardian)}
                      </div>
                    )}
                  </div>
                  <div className={styles.guardianInfo}>
                    <div className={styles.guardianName}>
                      {guardian.name}
                      <span className={styles.guardianRelation}>
                        ({guardian.relation})
                      </span>
                    </div>
                    <div className={styles.guardianPhone}>{guardian.phone}</div>
                  </div>
                  <div
                    className={`${styles.guardianStatus} ${getStatusClass(guardian.status)}`}
                  >
                    {getStatusText(guardian.status)}
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.tipBox}>
              <ul className={styles.tipList}>
                <li>紧急情况下系统会自动通知在线的监护人</li>
                <li>检测到高危风险时会立即发送预警</li>
                <li>您也可以手动通知所有监护人</li>
                <li>监护人可帮助您核实可疑信息</li>
              </ul>
            </div>
          </div>

          <div className={styles.footer}>
            <button className={styles.notifyBtn} onClick={onNotify}>
              <span>{Icons.bell}</span>
              通知所有监护人
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default GuardianSidebar;
