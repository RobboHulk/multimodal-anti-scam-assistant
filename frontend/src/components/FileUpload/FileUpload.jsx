// FileUpload.jsx
import { useRef, useState } from "react";
import styles from "./FileUpload.module.css";

export default function FileUpload({
  className = "",
  text = "",
  accept = "*/*",
  multiple = false,
  maxSize = 10 * 1024 * 1024,
  onFileSelect,
  children = "",
}) {
  const [error, setError] = useState("");
  const inputRef = useRef();

  const validateFile = (file) => {
    if (file.size > maxSize) {
      return {
        valid: false,
        error: `文件 ${file.name} 超过大小限制，最大允许：${(maxSize / 1024 / 1024).toFixed(2)}MB`,
      };
    }
    return { valid: true, error: "" };
  };

  const handleFileChange = (e) => {
    setError("");

    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length === 0) return;

    const validFiles = [];
    const invalidFiles = [];

    for (const file of selectedFiles) {
      const validation = validateFile(file);
      if (validation.valid) {
        const fileInfo = {
          file: file,
          name: file.name,
          size: file.size,
          sizeFormatted: (file.size / 1024).toFixed(2) + " KB",
          type: file.type,
          lastModified: file.lastModified,
          preview: file.type.startsWith("image/")
            ? URL.createObjectURL(file)
            : null,
          url: file.type.startsWith("image/")
            ? URL.createObjectURL(file)
            : null,
        };
        validFiles.push(fileInfo);
      } else {
        invalidFiles.push({ name: file.name, error: validation.error });
      }
    }

    if (invalidFiles.length > 0) {
      setError(invalidFiles.map((f) => f.error).join("\n"));
      setTimeout(() => setError(""), 3000);
    }

    if (validFiles.length > 0) {
      if (multiple) {
        onFileSelect(validFiles);
      } else {
        onFileSelect(validFiles[0]);
      }
    }

    e.target.value = "";
  };

  return (
    <div className={`${className} ${styles.box}`}>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      <button onClick={() => inputRef.current?.click()} className={styles.btn}>
        {children}
        {text}
      </button>
      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}
