// api/userApi.js — 用户相关 API
import request from "./request";

/** 检查用户名是否存在 */
export const checkUsername = (username) => {
  return request.get("/user/exists", { params: { username } });
};

/**
 * 用户登录
 * @returns {Promise<string>} JWT Token
 */
export const login = (username, password) => {
  return request.post("/user/login", { username, password });
};

/**
 * 用户注册
 * @param {string} params.username  用户名
 * @param {string} params.password  密码
 * @param {string} params.phone     手机号
 * @param {string} params.captcha   图片验证码（用户输入的值）
 * @param {string} params.captchaKey 图片验证码唯一 key
 * @returns {Promise<string>} JWT Token
 */
export const register = ({ username, password, phone, captcha, captchaKey }) => {
  return request.post("/user/register", {
    username,
    password,
    phone,
    captcha,
    captchaKey,
  });
};

/**
 * 获取图片验证码
 * @returns {Promise<{captchaKey: string, captchaImage: string}>}
 *          captchaImage 为 base64 data URI
 */
export const getImageCaptcha = () => {
  return request.get("/user/image-captcha");
};

/**
 * 忘记密码 - 校验验证码后返回密码
 * @returns {Promise<string>} 用户密码
 */
export const forgotPassword = (username, captchaKey, captchaCode) => {
  return request.post("/user/forgot-password", {
    username,
    captchaKey,
    captchaCode,
  });
};

/** 用户登出 */
export const userLogout = () => {
  return request.post("/user/logout");
};

/** 获取当前用户画像 */
export const getProfile = () => {
  return request.get("/user/profile");
};

/** 修改密码 */
export const changePassword = (oldPassword, newPassword) => {
  return request.put("/user/change-password", { oldPassword, newPassword });
};

/** 更新头像 */
export const updateAvatar = (avatar) => {
  return request.put("/user/avatar", { avatar });
};

/** 更新用户画像 */
export const updateProfile = (data) => {
  return request.put("/user/profile", data);
};
