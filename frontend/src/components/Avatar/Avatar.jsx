import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import styles from "./Avatar.module.css";
import { getCurrentUser, logout } from "../../utils/auth";

const Avatar = ({ className = "" }) => {
  const [show, setShow] = useState(false);
  const [user, setUser] = useState(() => getCurrentUser());
  const closeTimer = useRef(null);
  const loggedIn = Boolean(user?.token && user?.username);
  const avatarUrl = user?.avatar && !user.avatar.includes("默认头像")
    ? user.avatar
    : "/demo/landscape-avatar.png";

  const refreshUser = useCallback(() => setUser(getCurrentUser()), []);
  useEffect(() => {
    window.addEventListener("avatarUpdated", refreshUser);
    return () => window.removeEventListener("avatarUpdated", refreshUser);
  }, [refreshUser]);
  useEffect(() => () => closeTimer.current && clearTimeout(closeTimer.current), []);

  const open = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setShow(true);
  };
  const close = () => {
    closeTimer.current = setTimeout(() => setShow(false), 160);
  };
  const handleLogout = () => {
    logout();
    setUser(getCurrentUser());
    setShow(false);
  };

  return (
    <div className={[className, styles.userBox].filter(Boolean).join(" ")} onMouseEnter={open} onMouseLeave={close}>
      <Link to={loggedIn ? "/user" : "/login"} className={[styles.userImg, !loggedIn ? styles.loginAvatar : ""].filter(Boolean).join(" ")}>
        {loggedIn ? <img src={avatarUrl} alt="个人中心" /> : <span className={styles.loginText}>登录</span>}
      </Link>
      {show && (
        <div className={styles.cardBox} onMouseEnter={open} onMouseLeave={close}>
          {loggedIn && <div className={styles.userID}>{user.username}</div>}
          <Link to={loggedIn ? "/user" : "/login"} className={[styles.cardItem, styles.userCenter].join(" ")}>
            <div className={styles.iconCard}><span className="icon-user" /><span>{loggedIn ? "个人中心" : "立即登录"}</span></div>
            <span className="icon-chevron-right" />
          </Link>
          {loggedIn && (
            <>
              <div className={styles.line} />
              <div className={[styles.cardItem, styles.logOut].join(" ")}><button className={styles.iconCard} type="button" onClick={handleLogout}><span className="icon-log-out" />退出登录</button></div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default Avatar;
