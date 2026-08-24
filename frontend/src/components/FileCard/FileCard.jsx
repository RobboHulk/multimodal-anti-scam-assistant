// FileCard.jsx
import { useState } from "react";
import styles from "./FileCard.module.css";

export default function FileCard({
  fileIcon,
  fileName,
  fileSize,
  fileType,
  onRemove,
  fileUrl,
  fileId, // 添加 fileId 属性
  isReadOnly = false,
  hideRemoveBtn = false,
}) {
  // 格式化文件大小
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  // 处理删除
  const handleRemove = (e) => {
    e.stopPropagation();
    if (onRemove) {
      onRemove(fileId); // 传递 fileId 而不是依赖闭包
    }
    // 如果是blob URL，需要清理
    if (fileUrl && fileUrl.startsWith("blob:")) {
      URL.revokeObjectURL(fileUrl);
    }
  };

  return (
    <div className={`${styles.fileCard} ${isReadOnly ? styles.readOnlu : ""}`}>
      <span className={styles.fileIcon}>{fileIcon}</span>
      <div className={styles.fileInfo}>
        <span className={styles.fileName}>{fileName}</span>
        <div className={styles.fileDetail}>
          <span className={styles.filetype}>{fileType}</span>
          {fileSize && (
            <span className={styles.fileSize}>{formatFileSize(fileSize)}</span>
          )}
        </div>
      </div>

      {!hideRemoveBtn && (
        <button className={styles.fileRemove} onClick={handleRemove}>
          ×
        </button>
      )}
    </div>
  );
}
