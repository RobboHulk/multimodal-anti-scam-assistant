// BackBtn.jsx
import { useState, useEffect } from "react";
import styles from "./BackBtn.module.css";

const BackBtn = ({ targetRef, scrollThreshold = 600 }) => {
  const [showBackToTop, setShowBackToTop] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (targetRef?.current) {
        const scrollTop = targetRef.current.scrollTop;
        setShowBackToTop(scrollTop > scrollThreshold);
      }
    };

    const element = targetRef?.current;
    if (element) {
      element.addEventListener("scroll", handleScroll);
      handleScroll();
    }

    return () => {
      if (element) {
        element.removeEventListener("scroll", handleScroll);
      }
    };
  }, [targetRef, scrollThreshold]);

  const scrollToTop = () => {
    if (targetRef?.current) {
      targetRef.current.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    }
  };

  return (
    <button
      className={`${styles.backToTop} ${showBackToTop ? styles.visible : styles.hidden}`}
      onClick={scrollToTop}
      aria-label="回到顶部"
    >
      <svg width="18" height="22" viewBox="0 0 18 22" fill="currentColor">
        <path d="M8.69899 3.08174L7.76441 4.02584L7.75493 4.0258L1.3542 10.4265L0.0117182 9.08405L6.41245 2.68332L8.69707 0.398693L10.0396 1.74118L17.4565 9.15817L16.1159 10.4893L9.66059 4.0339L8.69899 3.08174Z" />
        <path d="M8.22508 5.69881L10.4911 7.2949L10.5527 21.8672L8.29342 21.8576L8.22508 5.69881Z" />
      </svg>
    </button>
  );
};

export default BackBtn;
