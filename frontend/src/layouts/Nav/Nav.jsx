import { Link, NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import styles from "./Nav.module.css";
import Avatar from "../../components/Avatar/Avatar";
import { isAuthenticated } from "../../utils/auth";
import logo from "../../assets/images/智能体.svg";

const menuItems = [
  { path: "/", label: "首页", protected: false },
  { path: "/detect", label: "智能体研判", protected: true },
  { path: "/analysis", label: "研判详情", protected: true },
  { path: "/reports", label: "安全报告", protected: true },
  { path: "/knowledge", label: "知识库", protected: true },
];

const BrandMark = () => (
  <img 
    src={logo}
    alt="智鉴安澜"
    style={{
      width: "45px",
      height: "50px",
      objectFit: "contain"
    }}
  />
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
