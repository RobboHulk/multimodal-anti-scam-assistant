import { useNavigate } from "react-router-dom";
import styles from "./NotFound.module.css";

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div className={styles.notFoundContainer}>
      <div className={styles.mars}></div>
      <img src="https://assets.codepen.io/1538474/404.svg" className={styles["logo-404"]} alt="404" />
      <img src="https://assets.codepen.io/1538474/meteor.svg" className={styles.meteor} alt="meteor" />
      <p className={styles.title}>Oh no!!</p>
      <p className={styles.subtitle}>
        You’re either misspelling the URL <br /> or requesting a page that's no longer here.
      </p>
      <div className={styles["btn-back-container"]}>
        <button className={styles["btn-back"]} onClick={() => navigate(-1)}>
          Back to previous page
        </button>
      </div>
      <img src="https://assets.codepen.io/1538474/astronaut.svg" className={styles.astronaut} alt="astronaut" />
      <img src="https://assets.codepen.io/1538474/spaceship.svg" className={styles.spaceship} alt="spaceship" />
    </div>
  );
};

export default NotFound;
