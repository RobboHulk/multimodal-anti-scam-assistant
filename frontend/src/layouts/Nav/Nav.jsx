import { Link, NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import styles from "./Nav.module.css";
import Avatar from "../../components/Avatar/Avatar";
import { isAuthenticated } from "../../utils/auth";

const menuItems = [
  { path: "/", label: "首页", protected: false },
  { path: "/detect", label: "智能体研判", protected: true },
  { path: "/analysis", label: "研判详情", protected: true },
  { path: "/reports", label: "安全报告", protected: true },
  { path: "/knowledge", label: "知识库", protected: true },
];

const BrandMark = () => (
  <svg viewBox="0 0 42 42" aria-hidden="true">
    <defs>
      <linearGradient id="navBrandGradient" x1="6" y1="4" x2="36" y2="38">
        <stop stopColor="#8b9cff" />
        <stop offset="1" stopColor="#5eead4" />
      </linearGradient>
    </defs>
    <path d="M21 3 36 9v11c0 9-6.2 15.6-15 19-8.8-3.4-15-10-15-19V9l15-6Z" fill="url(#navBrandGradient)" />
    <path d="M11.5 21c3.2-4.7 6.6-5.1 9.5-1.1 3-4 6.3-3.6 9.5 1.1-3.2 4.7-6.5 5.1-9.5 1.1-2.9 4-6.3 3.6-9.5-1.1Z" fill="#0b1020" fillOpacity=".88" />
  </svg>
);

const Nav = ({ className = "" }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const closeOnDesktop = () => window.innerWidth > 860 && setMenuOpen(false);
    window.addEventListener("resize", closeOnDesktop);
    return () => window.removeEventListener("resize", closeOnDesktop);
  }, []);

  const follow = (event, item) => {
    if (item.protected && !isAuthenticated()) {
      event.preventDefault();
      navigate("/login");
    }
    setMenuOpen(false);
  };

  return (
    <nav className={`${styles.nav} ${className}`}>
      <div className={styles.navContainer}>
        <Link to="/" className={styles.logo} onClick={() => setMenuOpen(false)}>
          <span className={styles.logoIcon}><BrandMark /></span>
          <span className={styles.logoText}>智鉴安澜</span>
        </Link>

        <div className={styles.desktopNav}>
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) => `${styles.navLink} ${isActive ? styles.active : ""}`}
              onClick={(event) => follow(event, item)}
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className={styles.navRight}>
          <span className={styles.secureStatus}><i />安全连接</span>
          <Avatar />
          <button
            type="button"
            className={`${styles.hamburger} ${menuOpen ? styles.open : ""}`}
            onClick={() => setMenuOpen((value) => !value)}
            aria-label="打开导航菜单"
            aria-expanded={menuOpen}
          >
            <span /><span /><span />
          </button>
        </div>
      </div>

      <div className={`${styles.mobileMenu} ${menuOpen ? styles.mobileMenuOpen : ""}`}>
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) => `${styles.mobileNavLink} ${isActive ? styles.active : ""}`}
            onClick={(event) => follow(event, item)}
          >
            {item.label}
          </NavLink>
        ))}
        <NavLink to="/user" className={styles.mobileNavLink} onClick={(event) => follow(event, { protected: true })}>
          个人中心
        </NavLink>
      </div>
      {menuOpen && <button className={styles.overlay} type="button" aria-label="关闭菜单" onClick={() => setMenuOpen(false)} />}
    </nav>
  );
};

export default Nav;
