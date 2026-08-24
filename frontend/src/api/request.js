// api/request.js — Axios 实例，统一封装请求/响应拦截
import axios from "axios";

const request = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ==================== 请求拦截器 ====================
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ==================== 响应拦截器 ====================
request.interceptors.response.use(
  (response) => {
    // 后端统一返回 { code, message, data }
    const res = response.data;

    // 兼容部分接口直接返回二进制/字符串
    if (typeof res === "string" || res instanceof Blob) {
      return res;
    }

    if (res.code === 200) {
      // 成功：只返回 data，调用方无需每次 .data.data
      return res.data;
    }

    // 后端返回业务错误
    const errorMsg = res.message || "请求失败";
    return Promise.reject(new Error(errorMsg));
  },
  (error) => {
    // 网络错误或 HTTP 错误
    if (error.response) {
      const { status, data } = error.response;

      if (status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        localStorage.removeItem("username");
        window.location.href = import.meta.env.BASE_URL + "login";
        return Promise.reject(new Error("登录已过期，请重新登录"));
      }

      if (status === 403) {
        return Promise.reject(new Error("没有权限执行此操作"));
      }

      if (status === 404) {
        return Promise.reject(new Error("请求的资源不存在"));
      }

      if (status >= 500) {
        // 服务端内部错误
        const serverMsg = (data && data.message)
          ? data.message
          : "服务器繁忙，请稍后重试";
        return Promise.reject(new Error(serverMsg));
      }

      const msg = (data && data.message) || `请求失败 (${status})`;
      return Promise.reject(new Error(msg));
    }

    if (error.code === "ECONNABORTED") {
      return Promise.reject(new Error("请求超时，请检查网络后重试"));
    }

    if (error.message === "Network Error") {
      return Promise.reject(new Error("无法连接服务器，请检查网络或稍后再试"));
    }

    return Promise.reject(new Error("网络异常，请检查网络连接"));
  },
);

export default request;
