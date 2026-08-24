// components/Loading.jsx
import styles from "./Loading.module.css";

const Loading = () => {
  return (
    <div className={styles.loadingContainer}>
      <div className={styles.spinner}></div>
      <p>加载中</p>
    </div>
  );
};

export default Loading;
