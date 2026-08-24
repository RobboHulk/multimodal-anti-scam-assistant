import { useState, useEffect, useRef, useCallback } from "react";
import CaseCard from "../CaseCard/CaseCard";
import styles from "./CaseColumn.module.css";

const CaseColumn = ({
  data,
  columnIndex,
  speed = "medium",
  className = "",
}) => {
  const [position, setPosition] = useState(() => {
    return -Math.floor(Math.random() * 100);
  });
  const [isHover, setIsHover] = useState(false);
  const animationRef = useRef(null);
  const columnRef = useRef(null);

  const CARD_HEIGHT = 400;
  const GAP_HEIGHT = 20;
  const TOTAL_HEIGHT = data.length * (CARD_HEIGHT + GAP_HEIGHT);

  const getStep = useCallback(() => {
    switch (speed) {
      case "slow":
        return 0.4;
      case "fast":
        return 0.8;
      case "medium":
      default:
        return 0.5;
    }
  }, [speed]);

  const animate = useCallback(() => {
    setPosition((prev) => {
      if (isHover) return prev;

      let newPos = prev - getStep();

      if (Math.abs(newPos) >= TOTAL_HEIGHT) {
        newPos = 0;
      }
      return newPos;
    });

    animationRef.current = requestAnimationFrame(animate);
  }, [isHover, TOTAL_HEIGHT, getStep]);

  useEffect(() => {
    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [animate]);

  const mouseEnter = () => {
    setIsHover(true);
  };

  const mouseLeave = () => {
    setIsHover(false);
  };

  // 修改：阻止事件冒泡，但允许在 hover 时手动控制滚动
  const handleWheel = useCallback(
    (e) => {
      // 阻止事件冒泡到父级，避免页面滚动
      e.stopPropagation();
      e.preventDefault();

      const delta = e.deltaY > 0 ? -GAP_HEIGHT : GAP_HEIGHT;

      setPosition((prev) => {
        let newPos = prev + 2 * delta;

        if (newPos < -TOTAL_HEIGHT) {
          newPos = 0;
        } else if (newPos > 0) {
          newPos = -TOTAL_HEIGHT;
        }

        return newPos;
      });
    },
    [GAP_HEIGHT, TOTAL_HEIGHT],
  );

  // 添加：监听 wheel 事件，使用 capture 阶段确保优先处理
  useEffect(() => {
    const columnElement = columnRef.current;
    if (!columnElement) return;

    // 使用 capture 阶段捕获事件，优先于页面滚动
    columnElement.addEventListener("wheel", handleWheel, {
      passive: false,
      capture: true,
    });

    return () => {
      columnElement.removeEventListener("wheel", handleWheel, {
        capture: true,
      });
    };
  }, [handleWheel]);

  return (
    <div
      className={`${styles.columnContainer} ${className}`}
      ref={columnRef}
      onMouseEnter={mouseEnter}
      onMouseLeave={mouseLeave}
    >
      <div
        className={styles.columnWrapper}
        style={{
          transform: `translateY(${position}px)`,
        }}
      >
        {data.map((item, index) => (
          <CaseCard key={`original-${columnIndex}-${index}`} data={item} />
        ))}
        {data.map((item, index) => (
          <CaseCard key={`clone-${columnIndex}-${index}`} data={item} />
        ))}
      </div>
    </div>
  );
};

export default CaseColumn;
