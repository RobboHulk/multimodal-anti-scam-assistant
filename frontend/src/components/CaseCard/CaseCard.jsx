import { Link } from "react-router-dom";
import styles from "./CaseCard.module.css";

const CaseCard = ({ data }) => {
  return (
    <div className={styles.cardBox}>
      <div className={styles.title}>
        <div className={styles.score}>{data.category || "安全案例"}</div>
        <div className={styles.time}>{data.time}</div>
      </div>
      <div className={styles.content}>
        <p className={styles.text}>{data.text}</p>
      </div>
      <div className={styles.imgBox}>
        <Link to="/case/1001">
          <img src={data.imageUrl} alt="" className={styles.img} />
        </Link>
      </div>
    </div>
  );
};

export default CaseCard;
