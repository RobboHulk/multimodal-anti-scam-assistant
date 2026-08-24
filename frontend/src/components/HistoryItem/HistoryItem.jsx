// HistoryItem.jsx
import { useEffect, useState, useRef, useCallback, memo } from "react";
import { createPortal } from "react-dom";
import styles from "./HistoryItem.module.css";

const TipCard = memo(({ onTipClick, isPinned, ref, style }) => {
  const TIP_ITEMS = [
    { id: "rename", icon: "icon-edit-3", text: "重命名", className: "" },
    { id: "pin", icon: "icon-uniE92D", text: isPinned ? "取消置顶" : "置顶", className: "" },
    { id: "delete", icon: "icon-trash-2", text: "删除", className: styles.tipDelete },
  ];

  return (
    <div ref={ref} className={styles.tipCard} style={style}>
      {TIP_ITEMS.map((item) => (
        <div
          key={item.id}
          className={`${styles.tip} ${item.className}`}
          onClick={(e) => {
            e.stopPropagation();
            onTipClick?.(item.id);
          }}
        >
          <span className={item.icon}></span>
          <span>{item.text}</span>
        </div>
      ))}
    </div>
  );
});

TipCard.displayName = "TipCard";

const HistoryItem = ({
  title,
  isSelected,
  onSelect,
  itemID,
  onRename,
  onPin,
  onDelete,
  isPinned,
}) => {
  const [showTipCard, setShowTipCard] = useState(false);
  const [isHover, setIsHover] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState(title.replace(/^📌\s*/, ""));
  const [tipPosition, setTipPosition] = useState({ top: 0, left: 0 });
  const itemRef = useRef(null);
  const iconRef = useRef(null);
  const tipCardRef = useRef(null);
  const renameInputRef = useRef(null);

  const shouldShowIcon = isHover || isSelected || showTipCard;
  const displayTitle = title;

  const handleItemHover = useCallback(() => {
    setIsHover(true);
  }, []);

  const handleItemLeave = useCallback(() => {
    setIsHover(false);
  }, []);

  const handleItemClick = useCallback(
    (e) => {
      if (isRenaming) return;
      e.stopPropagation();
      onSelect?.(itemID);
    },
    [itemID, onSelect, isRenaming],
  );

  const handleIconClick = useCallback(
    (e) => {
      e.stopPropagation();

      if (!showTipCard && iconRef.current) {
        const rect = iconRef.current.getBoundingClientRect();
        const cardHeight = 136;

        let left = rect.left;
        let top = rect.bottom + 5;

        if (top + cardHeight > window.innerHeight - 10) {
          top = rect.top - cardHeight - 5;
        }

        setTipPosition({
          top: top,
          left: left,
        });
      }

      setShowTipCard((prev) => !prev);
    },
    [showTipCard],
  );

  const handleTipClick = useCallback(
    (tipId) => {
      setShowTipCard(false);
      switch (tipId) {
        case "rename":
          setIsRenaming(true);
          setRenameValue(displayTitle.replace(/^📌\s*/, ""));
          setTimeout(() => {
            renameInputRef.current?.focus();
            renameInputRef.current?.select();
          }, 50);
          break;
        case "pin":
          onPin?.(itemID);
          break;
        case "delete":
          onDelete?.(itemID);
          break;
        default:
          break;
      }
    },
    [itemID, displayTitle, onPin, onDelete],
  );

  const handleRenameSubmit = useCallback(() => {
    if (
      renameValue.trim() &&
      renameValue.trim() !== displayTitle.replace(/^📌\s*/, "")
    ) {
      onRename?.(itemID, renameValue.trim());
    }
    setIsRenaming(false);
  }, [renameValue, displayTitle, itemID, onRename]);

  const handleRenameCancel = useCallback(() => {
    setIsRenaming(false);
  }, []);

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter") {
        handleRenameSubmit();
      } else if (e.key === "Escape") {
        handleRenameCancel();
      }
    },
    [handleRenameSubmit, handleRenameCancel],
  );

  // 点击外部关闭卡片
  useEffect(() => {
    if (!showTipCard) return;

    const handleClickOutside = (e) => {
      if (iconRef.current?.contains(e.target)) {
        return;
      }
      if (tipCardRef.current && !tipCardRef.current.contains(e.target)) {
        setShowTipCard(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showTipCard]);

  // 滚动时关闭卡片
  useEffect(() => {
    if (!showTipCard) return;

    const handleScroll = () => {
      setShowTipCard(false);
    };

    window.addEventListener("scroll", handleScroll, true);
    return () => {
      window.removeEventListener("scroll", handleScroll, true);
    };
  }, [showTipCard]);

  // ESC键关闭卡片
  useEffect(() => {
    if (!showTipCard) return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setShowTipCard(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [showTipCard]);

  return (
    <div
      ref={itemRef}
      className={`${styles.historyItem} ${isSelected ? styles.historyItemActive : ""} ${isPinned ? styles.pinned : ""}`}
      onMouseEnter={handleItemHover}
      onMouseLeave={handleItemLeave}
      onClick={handleItemClick}
      data-id={itemID}
    >
      <div className={styles.itemTitle}>
        {isRenaming ? (
          <input
            ref={renameInputRef}
            type="text"
            className={styles.renameInput}
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={handleRenameSubmit}
            onKeyDown={handleKeyDown}
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className={styles.titleText}>{displayTitle}</span>
        )}
      </div>
      {shouldShowIcon && !isRenaming && (
        <div
          ref={iconRef}
          className={styles.tipIcon}
          data-id={itemID}
          onClick={handleIconClick}
        >
          <span className="icon-more-horizontal" data-id={itemID}></span>
        </div>
      )}
      {showTipCard &&
        createPortal(
          <TipCard
            ref={tipCardRef}
            onTipClick={handleTipClick}
            isPinned={isPinned}
            style={{
              position: "fixed",
              top: tipPosition.top,
              left: tipPosition.left,
              zIndex: 9999,
            }}
          />,
          document.body,
        )}
    </div>
  );
};

export default HistoryItem;
