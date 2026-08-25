import { Link } from "react-router-dom";
import styles from "./Navbar.module.css";
import Avatar from "../../components/Avatar/Avatar";
import MessageList from "../../components/MessageList/MessageList";
import logoImg from "../../assets/images/智能体.svg";

const Navbar = () => {
  return (
    <nav className={styles.navbar}>
      <div className={styles.navContainer}>

        <div className={styles.navLogo}>
          <Link to="/">
            <img
              src={logoImg}
              alt="智鉴安澜"
              width="32"
              height="32"
            />
          </Link>
        </div>

        <ul className={styles.navLinks}>
          <li className={styles.navItem}>
            <Link to="/">首页</Link>
          </li>

          <li className={styles.navItem}>
            <Link to="/detect">风险检测</Link>
          </li>

          <li className={styles.navItem}>
            <Link to="/knowledge">知识库</Link>
          </li>

          <li className={styles.navItem}>
            <Link to="/community">反诈社区</Link>
          </li>

          <li className={styles.navItem}>
            <Link to="/about">关于我们</Link>
          </li>
        </ul>


        <ul className={styles.navUser}>
          <div className={`${styles.navUserItem} ${styles.navUserImgBox}`}>
            <Avatar />
          </div>

          <li className={`${styles.navUserItem} ${styles.navUserMsg}`}>
            <MessageList />
          </li>
        </ul>

      </div>
    </nav>
  );
};

export default Navbar;