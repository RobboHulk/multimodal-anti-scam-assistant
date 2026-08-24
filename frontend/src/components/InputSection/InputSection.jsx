// InputSection.jsx
import {
  useState,
  useRef,
  useCallback,
  useEffect,
  forwardRef,
  useImperativeHandle,
} from "react";
import FileCard from "../FileCard/FileCard";
import FileUpload from "../FileUpload/FileUpload";
import MicroPhone from "../Microphone/Microphone";
import styles from "./InputSection.module.css";

const InputSection = forwardRef(
  ({ onSend, disabled = false }, ref) => {
    const [message, setMessage] = useState("");
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [showLeftArrow, setShowLeftArrow] = useState(false);
    const [showRightArrow, setShowRightArrow] = useState(false);
    const textareaRef = useRef(null);
    const fileListRef = useRef(null);
    const idCounterRef = useRef(0);
    const scrollCheckTimerRef = useRef(null);

    // 草稿自动保存：初始化时读取
    useEffect(() => {
      const draft = localStorage.getItem("chat-draft");
      if (draft) setMessage(draft);
    }, []);

    // 草稿自动保存：输入时保存
    useEffect(() => {
      if (message) {
        localStorage.setItem("chat-draft", message);
      }
    }, [message]);

    // 暴露聚焦方法给父组件
    useImperativeHandle(ref, () => ({
      focusInput: () => {
        if (textareaRef.current) {
          textareaRef.current.focus();
        }
      },
      clearInput: () => {
        setMessage("");
        setUploadedFiles([]);
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
        }
      },
    }));

    const genId = () => {
      idCounterRef.current += 1;
      return `${Date.now()}-${idCounterRef.current}-${Math.random().toString(36).substring(2, 11)}`;
    };

    const canSend =
      (message.trim() !== "" || uploadedFiles.length > 0) &&
      !disabled;

    const handleKeyDown = (e) => {
      if (e.key === "Enter") {
        if (e.ctrlKey) {
          // Ctrl + Enter: 换行
          e.preventDefault();
          const textarea = textareaRef.current;
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          const newValue =
            message.substring(0, start) + "\n" + message.substring(end);
          setMessage(newValue);
          // 设置光标位置到新行后面
          setTimeout(() => {
            textarea.selectionStart = textarea.selectionEnd = start + 1;
            adjustTextHeight();
          }, 0);
        } else {
          // 普通 Enter: 发送消息
          e.preventDefault();
          if (canSend) {
            handleSubmit(e);
          }
        }
      }
    };

    const audioCapture = (audioBlob, audioUrl) => {
      const timestamp = Date.now();
      const audioFile = new File(
        [audioBlob],
        `recording_${timestamp}.webm`,
        {
          type: "audio/webm",
          lastModified: timestamp,
        },
      );

      const fileInfo = {
        id: genId(),
        file: audioFile,
        name: audioFile.name,
        size: audioBlob.size,
        type: "audio/webm",
        url: audioUrl,
      };

      handleFileSelect(fileInfo);
    };

    const handleFileSelect = (fileInfo) => {
      if (Array.isArray(fileInfo)) {
        // 为每个文件生成独立的 ID
        const filesWithIds = fileInfo.map((file) => ({
          ...file,
          id: genId(), // 为每个文件生成唯一 ID
        }));

        setUploadedFiles((prev) => {
          // 合并所有文件
          const newFiles = [...prev, ...filesWithIds];
          // 使用 id 去重
          const uniqueFiles = newFiles.filter((file, index, self) => {
            return index === self.findIndex((f) => f.id === file.id);
          });
          console.log(
            "Added multiple files:",
            filesWithIds.map((f) => ({ id: f.id, name: f.name })),
          );
          return uniqueFiles;
        });
      } else {
        // 处理单个文件
        setUploadedFiles((prev) => {
          const fileWithId = {
            ...fileInfo,
            id: fileInfo.id || genId(),
          };

          const isDuplicate = prev.some((f) => f.id === fileWithId.id);
          if (isDuplicate) return prev;

          console.log("Added single file:", {
            id: fileWithId.id,
            name: fileWithId.name,
          });
          return [...prev, fileWithId];
        });
      }
    };

    // 获取文件图标（保持不变）
    const getFileIcon = (fileType) => {
      const mainType = fileType?.split("/")[0];
      switch (mainType) {
        case "image":
          return (
            <svg viewBox="0 0 1024 1024" width="20" height="20">
              <path
                d="M938.666667 553.92V768c0 64.8-52.533333 117.333333-117.333334 117.333333H202.666667c-64.8 0-117.333333-52.533333-117.333334-117.333333V256c0-64.8 52.533333-117.333333 117.333334-117.333333h618.666666c64.8 0 117.333333 52.533333 117.333334 117.333333v297.92z m-64-74.624V256a53.333333 53.333333 0 0 0-53.333334-53.333333H202.666667a53.333333 53.333333 0 0 0-53.333334 53.333333v344.48A290.090667 290.090667 0 0 1 192 597.333333a286.88 286.88 0 0 1 183.296 65.845334C427.029333 528.384 556.906667 437.333333 704 437.333333c65.706667 0 126.997333 16.778667 170.666667 41.962667z m0 82.24c-5.333333-8.32-21.130667-21.653333-43.648-32.917333C796.768 511.488 753.045333 501.333333 704 501.333333c-121.770667 0-229.130667 76.266667-270.432 188.693334-2.730667 7.445333-7.402667 20.32-13.994667 38.581333-7.68 21.301333-34.453333 28.106667-51.370666 13.056-16.437333-14.634667-28.554667-25.066667-36.138667-31.146667A222.890667 222.890667 0 0 0 192 661.333333c-14.464 0-28.725333 1.365333-42.666667 4.053334V768a53.333333 53.333333 0 0 0 53.333334 53.333333h618.666666a53.333333 53.333333 0 0 0 53.333334-53.333333V561.525333zM320 480a96 96 0 1 1 0-192 96 96 0 0 1 0 192z m0-64a32 32 0 1 0 0-64 32 32 0 0 0 0 64z"
                fill="currentColor"
              />
            </svg>
          );
        case "audio":
          return (
            <svg viewBox="0 0 1024 1024" width="20" height="20">
              <path
                d="M257.493333 322.4l215.573334-133.056c24.981333-15.413333 57.877333-7.914667 73.493333 16.746667 5.301333 8.373333 8.106667 18.048 8.106667 27.914666v555.989334C554.666667 819.093333 530.784 842.666667 501.333333 842.666667c-9.994667 0-19.786667-2.773333-28.266666-8L257.493333 701.6H160c-41.237333 0-74.666667-33.013333-74.666667-73.738667V396.138667c0-40.725333 33.429333-73.738667 74.666667-73.738667h97.493333z m26.133334 58.4a32.298667 32.298667 0 0 1-16.96 4.8H160c-5.888 0-10.666667 4.714667-10.666667 10.538667v231.733333c0 5.813333 4.778667 10.538667 10.666667 10.538667h106.666667c5.994667 0 11.872 1.664 16.96 4.8L490.666667 770.986667V253.013333L283.626667 380.8zM800.906667 829.653333a32.288 32.288 0 0 1-45.248-0.757333 31.317333 31.317333 0 0 1 0.768-44.693333c157.653333-150.464 157.653333-393.962667 0-544.426667a31.317333 31.317333 0 0 1-0.768-44.682667 32.288 32.288 0 0 1 45.248-0.757333c183.68 175.306667 183.68 460.010667 0 635.317333z m-106.901334-126.186666a32.288 32.288 0 0 1-45.248-1.216 31.328 31.328 0 0 1 1.237334-44.672c86.229333-80.608 86.229333-210.56 0-291.178667a31.328 31.328 0 0 1-1.237334-44.672 32.288 32.288 0 0 1 45.248-1.216c112.885333 105.546667 112.885333 277.418667 0 382.965333z"
                fill="currentColor"
              />
            </svg>
          );
        case "video":
          return (
            <svg viewBox="0 0 1024 1024" width="20" height="20">
              <path
                d="M269.44 256l23.296-75.381333A74.666667 74.666667 0 0 1 364.074667 128h295.850666a74.666667 74.666667 0 0 1 71.338667 52.618667L754.56 256H821.333333c64.8 0 117.333333 52.533333 117.333334 117.333333v426.666667c0 64.8-52.533333 117.333333-117.333334 117.333333H202.666667c-64.8 0-117.333333-52.533333-117.333334-117.333333V373.333333c0-64.8 52.533333-117.333333 117.333334-117.333333h66.773333z m23.605333 64H202.666667a53.333333 53.333333 0 0 0-53.333334 53.333333v426.666667a53.333333 53.333333 0 0 0 53.333334 53.333333h618.666666a53.333333 53.333333 0 0 0 53.333334-53.333333V373.333333a53.333333 53.333333 0 0 0-53.333334-53.333333h-90.378666a32 32 0 0 1-30.570667-22.549333l-30.272-97.930667a10.666667 10.666667 0 0 0-10.186667-7.52H364.074667a10.666667 10.666667 0 0 0-10.186667 7.52l-30.272 97.92A32 32 0 0 1 293.045333 320zM512 725.333333c-88.362667 0-160-71.637333-160-160 0-88.362667 71.637333-160 160-160 88.362667 0 160 71.637333 160 160 0 88.362667-71.637333 160-160 160z m0-64a96 96 0 1 0 0-192 96 96 0 0 0 0 192z"
                fill="currentColor"
              />
            </svg>
          );
        default:
          return (
            <svg viewBox="0 0 1024 1024" width="20" height="20">
              <path
                d="M738.461538 572.258462H285.538462c-27.175385 0-45.686154 18.510769-45.686154 46.473846s18.510769 46.867692 45.686154 46.867692h452.923076c26.781538 0 45.292308-18.904615 45.292308-46.867692s-18.510769-46.473846-45.292308-46.473846z m-226.461538 163.052307H285.538462c-27.175385 0-45.686154 18.510769-45.686154 46.473846s18.510769 46.473846 45.686154 46.473847h226.461538c26.781538 0 45.292308-18.510769 45.292308-46.473847s-18.510769-46.473846-45.292308-46.473846z m-226.461538-232.763077h203.618461c27.175385 0 45.292308-18.510769 45.292308-46.473846V269.784615c0-27.963077-18.116923-46.473846-45.292308-46.473846H285.538462c-27.175385 0-45.686154 18.510769-45.686154 46.473846v186.289231c0 27.963077 18.510769 46.473846 45.686154 46.473846zM330.830769 316.258462h113.033846v93.341538H330.830769V316.258462z m629.366154-9.058462l-4.726154-4.726154c0-4.726154-4.332308-4.726154-4.332307-9.452308L702.227692 13.784615c-4.726154-4.726154-9.452308-4.726154-9.452307-9.452307L688.443077 0H172.110769C108.701538 0 59.076923 51.2 59.076923 116.184615v791.236923C59.076923 972.8 108.701538 1024 172.110769 1024h679.384616c63.409231 0 113.427692-51.2 113.427692-116.578462V325.710769c0-4.726154 0-14.178462-4.726154-18.510769z m-244.578461-139.815385l99.643076 111.852308h-99.643076V167.384615z m135.876923 763.273847H172.110769c-13.784615 0-22.449231-9.058462-22.449231-23.236924V116.184615c0-14.178462 8.664615-23.236923 22.449231-23.236923h452.923077v232.763077c0 27.963077 18.116923 46.473846 45.292308 46.473846h203.618461v535.236923c0 14.178462-8.664615 23.236923-22.44923 23.236924z"
                fill="currentColor"
              />
            </svg>
          );
      }
    };

    const handleChange = (e) => {
      setMessage(e.target.value);
    };

    const handleRemoveFile = (fileId) => {
      console.log("Removing file with ID:", fileId);
      setUploadedFiles((prev) => {
        const fileToRemove = prev.find((file) => file.id === fileId);

        if (fileToRemove?.url && fileToRemove.url.startsWith("blob:")) {
          URL.revokeObjectURL(fileToRemove.url);
        }

        const newFiles = prev.filter((file) => file.id !== fileId);
        console.log(
          "Files after removal:",
          newFiles.map((f) => ({ id: f.id, name: f.name })),
        );
        return newFiles;
      });
    };

    // 检查滚动箭头显示状态
    const checkScrollButtons = useCallback(() => {
      const container = fileListRef.current;
      if (container && uploadedFiles.length > 0) {
        const hasScroll = container.scrollWidth > container.clientWidth;
        if (!hasScroll) {
          setShowLeftArrow(false);
          setShowRightArrow(false);
          return;
        }

        const scrollLeft = container.scrollLeft;
        const maxScrollLeft = container.scrollWidth - container.clientWidth;

        setShowLeftArrow(scrollLeft > 5);
        setShowRightArrow(scrollLeft < maxScrollLeft - 5);
      } else {
        setShowLeftArrow(false);
        setShowRightArrow(false);
      }
    }, [uploadedFiles.length]);

    // 监听滚动事件
    useEffect(() => {
      const container = fileListRef.current;
      if (container) {
        container.addEventListener("scroll", checkScrollButtons);
        checkScrollButtons();
        return () => {
          container.removeEventListener("scroll", checkScrollButtons);
        };
      }
    }, [checkScrollButtons]);

    // 文件列表变化时重新检查按钮状态（带清理）
    useEffect(() => {
      scrollCheckTimerRef.current = setTimeout(checkScrollButtons, 100);
      return () => {
        if (scrollCheckTimerRef.current) {
          clearTimeout(scrollCheckTimerRef.current);
        }
      };
    }, [uploadedFiles, checkScrollButtons]);

    const adjustTextHeight = useCallback(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = "auto";
        const maxHeight = 200;
        const newHeight = Math.min(textarea.scrollHeight, maxHeight);
        textarea.style.height = `${newHeight}px`;
        textarea.style.overflowY =
          textarea.scrollHeight > maxHeight ? "auto" : "hidden";
      }
    }, []);

    useEffect(() => {
      adjustTextHeight();
    }, [adjustTextHeight, message]);

    const handleSend = () => {
      setMessage("");
      setUploadedFiles([]);
      // 发送成功后清除草稿
      localStorage.removeItem("chat-draft");
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = "auto";
        }
      }, 0);
    };

    const handleSubmit = (e) => {
      e.preventDefault();
      if (!canSend) return;

      const formData = {
        message: message,
        files: uploadedFiles.map((file) => ({
          id: file.id,
          name: file.name,
          size: file.size,
          type: file.type,
          file: file.file,
          url: file.url,
        })),
      };

      if (onSend) {
        onSend(formData);
      }

      handleSend();
    };

    // 添加滚动速度控制
    const scrollWithSpeed = useCallback(
      (direction) => {
        if (fileListRef.current) {
          const container = fileListRef.current;
          const scrollAmount = container.clientWidth * 0.8; // 滚动视口宽度的80%

          container.scrollBy({
            left: direction === "left" ? -scrollAmount : scrollAmount,
            behavior: "smooth",
          });

          // 立即检查按钮状态，不需要延迟
          checkScrollButtons();
        }
      },
      [checkScrollButtons],
    );

    // 优化后的滚动函数
    const scrollLeft = useCallback(() => {
      scrollWithSpeed("left");
    }, [scrollWithSpeed]);

    const scrollRight = useCallback(() => {
      scrollWithSpeed("right");
    }, [scrollWithSpeed]);

    // 添加键盘支持
    useEffect(() => {
      const handleKeyDown = (e) => {
        if (uploadedFiles.length === 0) return;

        // 当文件列表有焦点时，支持左右箭头键滚动
        if (
          document.activeElement === fileListRef.current ||
          fileListRef.current?.contains(document.activeElement)
        ) {
          if (e.key === "ArrowLeft") {
            e.preventDefault();
            scrollLeft();
          } else if (e.key === "ArrowRight") {
            e.preventDefault();
            scrollRight();
          }
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [scrollLeft, scrollRight, uploadedFiles.length]);

    // 添加滚轮滚动优化
    useEffect(() => {
      const container = fileListRef.current;
      if (!container) return;

      const handleWheel = (e) => {
        if (uploadedFiles.length === 0) return;

        // 阻止垂直滚动，改为水平滚动
        if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
          e.preventDefault();
          container.scrollBy({
            left: e.deltaY,
            behavior: "smooth",
          });
        }
      };

      container.addEventListener("wheel", handleWheel, { passive: false });
      return () => container.removeEventListener("wheel", handleWheel);
    }, [uploadedFiles.length]);

    return (
      <div className={styles.inputBox}>
        <div className={styles.mulInput}>
          {uploadedFiles.length > 0 && (
            <div className={styles.fileListWrapper}>
              <div
                className={`${styles.scrollLeftContainer} ${showLeftArrow ? styles.visible : ""}`}
              >
                <button
                  className={styles.scrollBtn}
                  onClick={scrollLeft}
                  type="button"
                >
                  <span
                    className="icon-chevron-right"
                    style={{ transform: "rotate(180deg)" }}
                  ></span>
                </button>
              </div>

              <div className={styles.fileList} ref={fileListRef} tabIndex={0}>
                {uploadedFiles.map((file) => (
                  <FileCard
                    key={file.id}
                    fileId={file.id}
                    fileIcon={getFileIcon(file.type)}
                    fileName={file.name}
                    fileSize={file.size}
                    fileType={file.type}
                    onRemove={handleRemoveFile}
                    fileUrl={file.url}
                  />
                ))}
              </div>

              <div
                className={`${styles.scrollRightContainer} ${showRightArrow ? styles.visible : ""}`}
              >
                <button
                  className={styles.scrollBtn}
                  onClick={scrollRight}
                  type="button"
                >
                  <span className="icon-chevron-right"></span>
                </button>
              </div>
            </div>
          )}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            className={styles.textarea}
            placeholder="给 VeriTide 发送消息..."
            disabled={disabled}
          />
          <div className={styles.toolList}>
            <ul className={styles.upLoad}>
              <li className={styles.upLoadBtn}>
                <FileUpload
                  accept="image/*"
                  multiple={true}
                  maxSize={5 * 1024 * 1024}
                  onFileSelect={handleFileSelect}
                >
                  <svg viewBox="0 0 1024 1024" width="20" height="20">
                    <path
                      d="M938.666667 553.92V768c0 64.8-52.533333 117.333333-117.333334 117.333333H202.666667c-64.8 0-117.333333-52.533333-117.333334-117.333333V256c0-64.8 52.533333-117.333333 117.333334-117.333333h618.666666c64.8 0 117.333333 52.533333 117.333334 117.333333v297.92z m-64-74.624V256a53.333333 53.333333 0 0 0-53.333334-53.333333H202.666667a53.333333 53.333333 0 0 0-53.333334 53.333333v344.48A290.090667 290.090667 0 0 1 192 597.333333a286.88 286.88 0 0 1 183.296 65.845334C427.029333 528.384 556.906667 437.333333 704 437.333333c65.706667 0 126.997333 16.778667 170.666667 41.962667z m0 82.24c-5.333333-8.32-21.130667-21.653333-43.648-32.917333C796.768 511.488 753.045333 501.333333 704 501.333333c-121.770667 0-229.130667 76.266667-270.432 188.693334-2.730667 7.445333-7.402667 20.32-13.994667 38.581333-7.68 21.301333-34.453333 28.106667-51.370666 13.056-16.437333-14.634667-28.554667-25.066667-36.138667-31.146667A222.890667 222.890667 0 0 0 192 661.333333c-14.464 0-28.725333 1.365333-42.666667 4.053334V768a53.333333 53.333333 0 0 0 53.333334 53.333333h618.666666a53.333333 53.333333 0 0 0 53.333334-53.333333V561.525333zM320 480a96 96 0 1 1 0-192 96 96 0 0 1 0 192z m0-64a32 32 0 1 0 0-64 32 32 0 0 0 0 64z"
                      fill="currentColor"
                    />
                  </svg>
                </FileUpload>
              </li>
              <li className={styles.upLoadBtn}>
                <FileUpload
                  accept="audio/*"
                  multiple={false}
                  maxSize={5 * 1024 * 1024}
                  onFileSelect={handleFileSelect}
                >
                  <svg viewBox="0 0 1024 1024" width="20" height="20">
                    <path
                      d="M257.493333 322.4l215.573334-133.056c24.981333-15.413333 57.877333-7.914667 73.493333 16.746667 5.301333 8.373333 8.106667 18.048 8.106667 27.914666v555.989334C554.666667 819.093333 530.784 842.666667 501.333333 842.666667c-9.994667 0-19.786667-2.773333-28.266666-8L257.493333 701.6H160c-41.237333 0-74.666667-33.013333-74.666667-73.738667V396.138667c0-40.725333 33.429333-73.738667 74.666667-73.738667h97.493333z m26.133334 58.4a32.298667 32.298667 0 0 1-16.96 4.8H160c-5.888 0-10.666667 4.714667-10.666667 10.538667v231.733333c0 5.813333 4.778667 10.538667 10.666667 10.538667h106.666667c5.994667 0 11.872 1.664 16.96 4.8L490.666667 770.986667V253.013333L283.626667 380.8zM800.906667 829.653333a32.288 32.288 0 0 1-45.248-0.757333 31.317333 31.317333 0 0 1 0.768-44.693333c157.653333-150.464 157.653333-393.962667 0-544.426667a31.317333 31.317333 0 0 1-0.768-44.682667 32.288 32.288 0 0 1 45.248-0.757333c183.68 175.306667 183.68 460.010667 0 635.317333z m-106.901334-126.186666a32.288 32.288 0 0 1-45.248-1.216 31.328 31.328 0 0 1 1.237334-44.672c86.229333-80.608 86.229333-210.56 0-291.178667a31.328 31.328 0 0 1-1.237334-44.672 32.288 32.288 0 0 1 45.248-1.216c112.885333 105.546667 112.885333 277.418667 0 382.965333z"
                      fill="currentColor"
                    />
                  </svg>
                </FileUpload>
              </li>
              <li className={styles.upLoadBtn}>
                <FileUpload
                  accept="video/*"
                  multiple={false}
                  maxSize={10 * 1024 * 1024}
                  onFileSelect={handleFileSelect}
                >
                  <svg viewBox="0 0 1024 1024" width="20" height="20">
                    <path
                      d="M269.44 256l23.296-75.381333A74.666667 74.666667 0 0 1 364.074667 128h295.850666a74.666667 74.666667 0 0 1 71.338667 52.618667L754.56 256H821.333333c64.8 0 117.333333 52.533333 117.333334 117.333333v426.666667c0 64.8-52.533333 117.333333-117.333334 117.333333H202.666667c-64.8 0-117.333333-52.533333-117.333334-117.333333V373.333333c0-64.8 52.533333-117.333333 117.333334-117.333333h66.773333z m23.605333 64H202.666667a53.333333 53.333333 0 0 0-53.333334 53.333333v426.666667a53.333333 53.333333 0 0 0 53.333334 53.333333h618.666666a53.333333 53.333333 0 0 0 53.333334-53.333333V373.333333a53.333333 53.333333 0 0 0-53.333334-53.333333h-90.378666a32 32 0 0 1-30.570667-22.549333l-30.272-97.930667a10.666667 10.666667 0 0 0-10.186667-7.52H364.074667a10.666667 10.666667 0 0 0-10.186667 7.52l-30.272 97.92A32 32 0 0 1 293.045333 320zM512 725.333333c-88.362667 0-160-71.637333-160-160 0-88.362667 71.637333-160 160-160 88.362667 0 160 71.637333 160 160 0 88.362667-71.637333 160-160 160z m0-64a96 96 0 1 0 0-192 96 96 0 0 0 0 192z"
                      fill="currentColor"
                    />
                  </svg>
                </FileUpload>
              </li>
            </ul>
            <div className={styles.sendBox}>
              <MicroPhone
                onAudioCapture={audioCapture}
                disabled={disabled}
              />
              <div className={styles.line}></div>
              <button
                className={`${styles.send}`}
                onClick={handleSubmit}
                disabled={!canSend}
              >
                <svg viewBox="0 0 1024 1024" width="22" height="22">
                  <path
                    d="M507.904 882.688c-18.432 0-33.28-14.848-33.28-33.28v-655.36c0-18.432 14.848-33.28 33.28-33.28s33.28 14.848 33.28 33.28v654.848c0 18.432-14.848 33.792-33.28 33.792z"
                    fill="currentColor"
                  />
                  <path
                    d="M787.968 502.784c-8.704 0-16.896-3.072-23.552-9.728L507.904 236.544 251.392 493.056c-12.8 12.8-34.304 12.8-47.104 0-12.8-12.8-12.8-34.304 0-47.104l280.064-280.064c6.144-6.144 14.848-9.728 23.552-9.728s17.408 3.584 23.552 9.728l280.064 280.064c12.8 12.8 12.8 34.304 0 47.104-6.656 6.656-15.36 9.728-23.552 9.728z"
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  },
);

InputSection.displayName = "InputSection";

export default InputSection;
