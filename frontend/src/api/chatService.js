/**
 * ML 服务对话 API - 支持流式响应
 */

const ML_BASE = "/ml";

/**
 * 发送对话请求（流式）
 * @param {Object} params - 请求参数
 * @param {string} params.text - 用户输入文本
 * @param {string} params.sessionId - 会话ID
 * @param {string} [params.imagePath] - 图片路径
 * @param {string} [params.audioPath] - 音频路径
 * @param {string} [params.videoPath] - 视频路径
 * @param {Object} [params.userProfile] - 用户画像
 * @param {Function} onThinking - 思考过程回调
 * @param {Function} onContent - 内容流回调
 * @param {Function} onResult - 最终结果回调
 * @param {Function} onError - 错误回调
 * @returns {AbortController} - 用于取消请求
 */
export function streamChat({
  text,
  sessionId = `sess-${Date.now()}`,
  imagePath = "",
  audioPath = "",
  videoPath = "",
  dimensions = [],
  userProfile = null,
  onThinkingStart = () => {},
  onThinking = () => {},
  onThinkingEnd = () => {},
  onContent = () => {},
  onResult = () => {},
  onError = () => {},
  onDone = () => {},
}) {
  const controller = new AbortController();

  const body = {
    text,
    session_id: sessionId,
    image_path: imagePath,
    audio_path: audioPath,
    video_path: videoPath,
    dimensions,
  };

  if (userProfile) {
    body.userProfile = userProfile;
  }

  fetch(`${ML_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6).trim();

          if (data === "[DONE]") {
            onDone();
            return;
          }

          try {
            const parsed = JSON.parse(data);
            switch (parsed.type) {
              case "thinking_start":
                onThinkingStart();
                break;
              case "thinking":
                onThinking(parsed.content || "");
                break;
              case "thinking_end":
                onThinkingEnd();
                break;
              case "content":
                onContent(parsed.content || "");
                break;
              case "result":
                onResult(parsed.data || {});
                break;
              case "error":
                onError(parsed.content || "未知错误");
                break;
            }
          } catch {
            // 忽略解析错误
          }
        }
      }
      onDone();
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError(err.message);
      }
    });

  return controller;
}

/**
 * 发送对话请求（非流式）
 */
export async function sendChat({
  text,
  sessionId = `sess-${Date.now()}`,
  imagePath = "",
  audioPath = "",
  videoPath = "",
  userProfile = null,
}) {
  const body = {
    text,
    session_id: sessionId,
    image_path: imagePath,
    audio_path: audioPath,
    video_path: videoPath,
  };

  if (userProfile) {
    body.userProfile = userProfile;
  }

  const response = await fetch(`${ML_BASE}/chat/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * 上传文件到后端
 */
export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const token = localStorage.getItem("token");
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const response = await fetch("/api/file/upload", {
    method: "POST",
    headers,
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`上传失败: ${response.status}`);
  }

  const json = await response.json();
  return json.data?.url || json.data || "";
}
