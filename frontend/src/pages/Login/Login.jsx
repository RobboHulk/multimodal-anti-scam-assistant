// Login.jsx — 登录/注册页面（图片验证码 + 忘记密码 + 重构排版）
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import styles from "./Login.module.css";
import { login, register, getImageCaptcha, forgotPassword, checkUsername, getProfile } from "../../api/userApi";
import { setUserInfo } from "../../utils/auth";

const EMPTY_LOGIN = { username: "", password: "" };
const EMPTY_REGISTER = { username: "", password: "", confirmPassword: "", phone: "", captcha: "" };

const Login = () => {
  const [searchParams] = useSearchParams();
  const redirectPath = searchParams.get("redirect") || import.meta.env.BASE_URL || "/";

  const [isLoginActive, setIsLoginActive] = useState(true);
  const [isAnimating, setIsAnimating] = useState(false);
  const togglePanel = () => {
    if (isAnimating) return;
    if (isLoginActive && !regCaptcha.image) refreshRegCaptcha();
    setIsAnimating(true);
    setIsLoginActive((v) => !v);
    setTimeout(() => setIsAnimating(false), 1500);
  };

  const [loginForm, setLoginForm] = useState(EMPTY_LOGIN);
  const [registerForm, setRegisterForm] = useState(EMPTY_REGISTER);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [loading, setLoading] = useState({ login: false, register: false });
  const [error, setError] = useState({ login: "", register: "" });
  const [checkingName, setCheckingName] = useState(false);
  const [toast, setToast] = useState(null);

  const [regCaptcha, setRegCaptcha] = useState({ key: "", image: "" });

  const [forgotOpen, setForgotOpen] = useState(false);
  const [forgotStep, setForgotStep] = useState(0);
  const [forgotUsername, setForgotUsername] = useState("");
  const [forgotCaptcha, setForgotCaptcha] = useState({ key: "", image: "" });
  const [forgotCaptchaInput, setForgotCaptchaInput] = useState("");
  const [forgotResult, setForgotResult] = useState("");
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState("");

  // 用户名实时查重 → 写入全局 error.register
  useEffect(() => {
    const name = registerForm.username.trim();
    if (!name || name.length < 3) {
      return;
    }
    let active = true;
    const timer = setTimeout(async () => {
      try {
        const exists = await checkUsername(name);
        if (!active) return;
        if (exists) {
          setError((p) => ({ ...p, register: "用户名已被注册" }));
        } else {
          setError((p) => p.register === "用户名已被注册" ? { ...p, register: "" } : p);
        }
      } catch {
        // 忽略网络错误
      } finally {
        if (active) setCheckingName(false);
      }
    }, 500);
    return () => { active = false; clearTimeout(timer); };
  }, [registerForm.username]);

  const passwordMatch = registerForm.password && registerForm.confirmPassword
    ? (registerForm.password === registerForm.confirmPassword ? "ok" : "fail")
    : null;

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  const refreshRegCaptcha = async () => {
    try {
      const data = await getImageCaptcha();
      setRegCaptcha({ key: data.captchaKey, image: data.captchaImage });
    } catch { /* ignore */ }
  };

  const refreshForgotCaptcha = async () => {
    try {
      const data = await getImageCaptcha();
      setForgotCaptcha({ key: data.captchaKey, image: data.captchaImage });
      setForgotCaptchaInput("");
      setForgotError("");
    } catch { /* ignore */ }
  };

  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginForm((p) => ({ ...p, [name]: value }));
    if (error.login) setError((p) => ({ ...p, login: "" }));
  };

  const handleRegisterChange = (e) => {
    const { name, value } = e.target;
    setRegisterForm((p) => ({ ...p, [name]: value }));
    if (name === "username") setCheckingName(value.trim().length >= 3);
    if (error.register) setError((p) => ({ ...p, register: "" }));
  };

  const onLoginSuccess = async (token, username) => {
    // 从 JWT 解析 userId
    let userId = null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      userId = payload.sub;
    } catch { /* ignore */ }
    // 先存基本数据
    setUserInfo(token, { username, id: userId, avatar: "/demo/landscape-avatar.png" });
    // 异步拉取后端头像
    try {
      const profile = await getProfile();
      const avatar = profile?.avatar || "/demo/landscape-avatar.png";
      const stored = JSON.parse(localStorage.getItem("user") || "{}");
      stored.avatar = avatar;
      localStorage.setItem("user", JSON.stringify(stored));
      window.dispatchEvent(new Event("avatarUpdated"));
    } catch { /* ignore */ }
    window.location.href = redirectPath;
  };

  // ==================== 登录 ====================
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    if (!loginForm.username || !loginForm.password) {
      setError((p) => ({ ...p, login: "请输入用户名和密码" }));
      return;
    }
    setLoading((p) => ({ ...p, login: true }));
    setError((p) => ({ ...p, login: "" }));
    try {
      const token = await login(loginForm.username, loginForm.password);
      onLoginSuccess(token, loginForm.username);
    } catch (err) {
      const msg = err.message || "登录失败";
      if (msg.includes("Network Error") || msg.includes("connect")) {
        setError((p) => ({ ...p, login: "无法连接服务器，请确认后端已启动" }));
      } else if (msg.includes("超时")) {
        setError((p) => ({ ...p, login: "服务器响应超时，请稍后重试" }));
      } else {
        setError((p) => ({ ...p, login: msg }));
      }
    } finally {
      setLoading((p) => ({ ...p, login: false }));
    }
  };

  // ==================== 注册 ====================
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!registerForm.username || registerForm.username.length < 3) {
      setError((p) => ({ ...p, register: "用户名至少 3 个字符" }));
      return;
    }
    if (error.register) { // 包含实时查重结果（如"用户名已被注册"）
      return;
    }
    if (!registerForm.password || registerForm.password.length < 6) {
      setError((p) => ({ ...p, register: "密码至少 6 位" }));
      return;
    }
    if (registerForm.password !== registerForm.confirmPassword) {
      setError((p) => ({ ...p, register: "两次输入的密码不一致" }));
      return;
    }
    if (!/^1[3-9]\d{9}$/.test(registerForm.phone)) {
      setError((p) => ({ ...p, register: "请输入正确的手机号" }));
      return;
    }
    if (!registerForm.captcha || registerForm.captcha.length !== 4) {
      setError((p) => ({ ...p, register: "请输入 4 位图片验证码" }));
      return;
    }
    if (!regCaptcha.key) {
      setError((p) => ({ ...p, register: "验证码已失效，请刷新后重试" }));
      return;
    }
    setLoading((p) => ({ ...p, register: true }));
    setError((p) => ({ ...p, register: "" }));
    try {
      const token = await register({
        username: registerForm.username,
        password: registerForm.password,
        phone: registerForm.phone,
        captcha: registerForm.captcha,
        captchaKey: regCaptcha.key,
      });
      setToast({ type: "success", text: "注册成功，已自动登录" });
      onLoginSuccess(token, registerForm.username);
    } catch (err) {
      refreshRegCaptcha();
      const msg = err.message || "注册失败";
      if (msg.includes("Network Error") || msg.includes("connect")) {
        setError((p) => ({ ...p, register: "无法连接服务器，请确认后端已启动" }));
      } else if (msg.includes("超时")) {
        setError((p) => ({ ...p, register: "服务器响应超时，请稍后重试" }));
      } else {
        setError((p) => ({ ...p, register: msg }));
      }
    } finally {
      setLoading((p) => ({ ...p, register: false }));
    }
  };

  // ==================== 忘记密码 ====================
  const openForgotModal = () => {
    setForgotOpen(true); setForgotStep(0); setForgotUsername("");
    setForgotCaptcha({ key: "", image: "" }); setForgotCaptchaInput("");
    setForgotResult(""); setForgotError("");
  };
  const closeForgotModal = () => setForgotOpen(false);

  const handleForgotNext = async () => {
    if (!forgotUsername.trim()) { setForgotError("请输入用户名"); return; }
    setForgotError(""); setForgotLoading(true);
    try {
      const exists = await checkUsername(forgotUsername.trim());
      if (!exists) { setForgotError("该用户名不存在，请检查后重新输入"); setForgotLoading(false); return; }
      setForgotStep(1);
      const data = await getImageCaptcha();
      setForgotCaptcha({ key: data.captchaKey, image: data.captchaImage });
    } catch (err) {
      setForgotError(err.message || "网络异常，请稍后重试");
    } finally { setForgotLoading(false); }
  };

  const handleForgotSubmit = async () => {
    if (!forgotCaptchaInput || forgotCaptchaInput.length !== 4) { setForgotError("请输入 4 位图片验证码"); return; }
    setForgotLoading(true); setForgotError("");
    try {
      const password = await forgotPassword(forgotUsername, forgotCaptcha.key, forgotCaptchaInput);
      setForgotResult(password); setForgotStep(2);
    } catch (err) {
      refreshForgotCaptcha();
      setForgotError(err.message || "验证失败");
    } finally { setForgotLoading(false); }
  };

  return (
    <main className={styles.container}>
      {toast && <div className={`${styles.toast} ${styles[`toast-${toast.type}`]}`}>{toast.text}</div>}

      {/* ==================== 忘记密码弹窗 ==================== */}
      {forgotOpen && (
        <div className={styles.modalOverlay} onClick={closeForgotModal}>
          <div className={styles.modalBox} onClick={(e) => e.stopPropagation()}>
            <button className={styles.modalClose} onClick={closeForgotModal}>&times;</button>
            <h2 className={styles.modalTitle}>找回密码</h2>

            {forgotStep === 0 && (<>
              <p className={styles.modalDesc}>请输入您的用户名</p>
              <input type="text" className={styles.input} placeholder="用户名"
                value={forgotUsername} autoFocus
                onChange={(e) => { setForgotUsername(e.target.value); setForgotError(""); }}
                onKeyDown={(e) => e.key === "Enter" && handleForgotNext()} />
              {forgotError && <p className={styles.modalError}>{forgotError}</p>}
              <button className={`${styles.button} ${styles.primaryButton}`} onClick={handleForgotNext}>下一步</button>
            </>)}

            {forgotStep === 1 && (<>
              <p className={styles.modalDesc}>用户名：<strong>{forgotUsername}</strong>，请输入验证码</p>
              <div className={styles.captchaImageRow}>
                {forgotCaptcha.image ? (
                  <img src={forgotCaptcha.image} alt="验证码" className={styles.captchaImg}
                    onClick={refreshForgotCaptcha} title="点击刷新" />
                ) : <div className={styles.captchaImgPlaceholder}>加载中...</div>}
                <button type="button" className={styles.captchaRefreshBtn} onClick={refreshForgotCaptcha}>换一张</button>
              </div>
              <input type="text" className={styles.input} placeholder="请输入 4 位验证码"
                value={forgotCaptchaInput} maxLength={4} autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} autoFocus
                onChange={(e) => { setForgotCaptchaInput(e.target.value); setForgotError(""); }}
                onKeyDown={(e) => e.key === "Enter" && handleForgotSubmit()} />
              {forgotError && <p className={styles.modalError}>{forgotError}</p>}
              <button className={`${styles.button} ${styles.primaryButton}`}
                onClick={handleForgotSubmit} disabled={forgotLoading}>
                {forgotLoading ? "验证中..." : "找回密码"}
              </button>
            </>)}

            {forgotStep === 2 && (<>
              <p className={styles.modalDesc}>密码找回成功！</p>
              <div className={styles.passwordResult}>
                <span className={styles.passwordLabel}>您的密码：</span>
                <strong className={styles.passwordValue}>{forgotResult}</strong>
              </div>
              <p className={styles.passwordHint}>已自动填入下方登录框</p>
              <button className={`${styles.button} ${styles.primaryButton}`} onClick={() => {
                setLoginForm({ username: forgotUsername, password: forgotResult });
                closeForgotModal();
                if (!isLoginActive) togglePanel();
              }}>一键填写并登录</button>
            </>)}
          </div>
        </div>
      )}

      <div className={styles.box}>
        {/* ===================== 登录面板 ===================== */}
        <section className={`${styles.panel} ${styles.loginPanel} ${isLoginActive ? styles.active : ""}`}>
          <form onSubmit={handleLoginSubmit} className={styles.form} noValidate>
            <h1 className={styles.title}>登录账号</h1>

            <div className={styles.socialLogin}>
              <button type="button" className={styles.socialButton}><i className="iconfont icon-qq"></i></button>
              <button type="button" className={styles.socialButton}><i className="iconfont icon-weixin"></i></button>
            </div>

            {/* 账号 */}
            <div className={styles.inputGroup}>
              <label htmlFor="loginAccount" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>账号</span>
                  <svg t="1773667919709" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M511.808 512c121.344 0 219.84-100.352 219.84-224.128S633.152 63.808 511.808 63.808c-121.408 0-219.84 100.288-219.84 224.064s98.368 224.128 219.84 224.128z m302.848 139.84c-50.24-58.496-67.2-78.656-159.168-84.032h-287.04c-92.032 5.504-108.928 25.536-159.04 84.032-53.376 60.352-95.872 137.024-75.776 231.872 22.4 62.144 82.688 76.416 139.904 76.416H750.592c57.152 0 117.568-14.4 139.968-76.416 19.904-94.848-22.528-171.456-75.904-231.872z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <input type="text" id="loginAccount" name="username" value={loginForm.username}
                  onChange={handleLoginChange} className={styles.input} placeholder="请输入用户名"
                  autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.login} />
              </div>
            </div>

            {/* 密码 */}
            <div className={styles.inputGroup}>
              <label htmlFor="loginPassword" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>密码</span>
                  <svg t="1773667809322" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M297.4 250.2c22.6 0 41 18.3 41 41V462c0 22.6-18.3 41-41 41-22.6 0-41-18.3-41-41V291.2c0-22.6 18.4-41 41-41zM701.5 246.2c22.6 0 41 18.3 41 41v169.1c0 22.6-18.3 41-41 41-22.6 0-41-18.3-41-41V287.2c0-22.6 18.4-41 41-41z" fill="#A0A5A8"></path><path d="M499.4 126.2c89 0 161.1 72.1 161.1 161.1h81.9c0-134.2-108.8-243-243-243s-243 108.8-243 243h81.9c0-89 72.2-161.1 161.1-161.1zM865.4 938V482.1c-3.4-33.4-31-59.7-64.9-61H200.6c-37.5 0-68 30.4-68.1 67.9v444.3c4 30.2 27.8 54.2 57.9 58.5h621.5c27-5.4 48.3-26.8 53.5-53.8z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <div className={styles.passwordWrapper}>
                  <input type={showLoginPassword ? "text" : "password"} id="loginPassword" name="password"
                    value={loginForm.password} onChange={handleLoginChange} className={styles.input}
                    placeholder="请输入密码" autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.login} />
                  <button type="button" className={styles.passwordToggle} tabIndex={-1}
                    onClick={() => setShowLoginPassword(!showLoginPassword)}>
                    <span className={showLoginPassword ? "icon-view-show" : "icon-view-hide"}></span>
                  </button>
                </div>
                {/* 错误 + 忘记密码合并在一行 */}
                <div className={styles.loginFooter}>
                  <div className={`${styles.errorMessage} ${error.login ? styles.errorVisible : ""}`}>
                    {error.login && <><span className={styles.errorIcon}>⚠</span><span className={styles.errorText}>{error.login}</span></>}
                  </div>
                  <button type="button" className={styles.link} onClick={openForgotModal}>忘记密码?</button>
                </div>
              </div>
            </div>

            <button type="submit" className={`${styles.button} ${styles.primaryButton}`} disabled={loading.login}>
              {loading.login ? "登录中..." : "登录"}
            </button>
          </form>
        </section>

        {/* ===================== 注册面板 ===================== */}
        <section className={`${styles.panel} ${styles.registerPanel} ${!isLoginActive ? styles.active : ""}`}>
          <form onSubmit={handleRegisterSubmit} className={styles.form} noValidate>
            <h1 className={styles.title}>注册账号</h1>

            {/* 用户名 */}
            <div className={styles.inputGroup}>
              <label htmlFor="registerUsername" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>用户名</span>
                  <svg t="1773667919709" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M511.808 512c121.344 0 219.84-100.352 219.84-224.128S633.152 63.808 511.808 63.808c-121.408 0-219.84 100.288-219.84 224.064s98.368 224.128 219.84 224.128z m302.848 139.84c-50.24-58.496-67.2-78.656-159.168-84.032h-287.04c-92.032 5.504-108.928 25.536-159.04 84.032-53.376 60.352-95.872 137.024-75.776 231.872 22.4 62.144 82.688 76.416 139.904 76.416H750.592c57.152 0 117.568-14.4 139.968-76.416 19.904-94.848-22.528-171.456-75.904-231.872z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <div className={styles.passwordWrapper}>
                  <input type="text" id="registerUsername" name="username" value={registerForm.username}
                    onChange={handleRegisterChange}
                    className={`${styles.input} ${error.register === "用户名已被注册" ? styles.inputMismatch : registerForm.username.length >= 3 && !checkingName ? styles.inputMatch : ""}`}
                    placeholder="3~50 个字符" maxLength="50" autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.register} />
                  {checkingName && <span className={styles.checkingSpin}>⟳</span>}
                </div>
              </div>
            </div>

            {/* 密码 */}
            <div className={styles.inputGroup}>
              <label htmlFor="registerPassword" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>密码</span>
                  <svg t="1773667809322" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M297.4 250.2c22.6 0 41 18.3 41 41V462c0 22.6-18.3 41-41 41-22.6 0-41-18.3-41-41V291.2c0-22.6 18.4-41 41-41zM701.5 246.2c22.6 0 41 18.3 41 41v169.1c0 22.6-18.3 41-41 41-22.6 0-41-18.3-41-41V287.2c0-22.6 18.4-41 41-41z" fill="#A0A5A8"></path><path d="M499.4 126.2c89 0 161.1 72.1 161.1 161.1h81.9c0-134.2-108.8-243-243-243s-243 108.8-243 243h81.9c0-89 72.2-161.1 161.1-161.1zM865.4 938V482.1c-3.4-33.4-31-59.7-64.9-61H200.6c-37.5 0-68 30.4-68.1 67.9v444.3c4 30.2 27.8 54.2 57.9 58.5h621.5c27-5.4 48.3-26.8 53.5-53.8z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <div className={styles.passwordWrapper}>
                  <input type={showPassword ? "text" : "password"} id="registerPassword" name="password"
                    value={registerForm.password} onChange={handleRegisterChange} className={styles.input}
                    placeholder="至少 6 位密码" maxLength="100" autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.register} />
                  <button type="button" className={styles.passwordToggle} tabIndex={-1}
                    onClick={() => setShowPassword(!showPassword)}>
                    <span className={showPassword ? "icon-view-show" : "icon-view-hide"}></span>
                  </button>
                </div>
              </div>
            </div>

            {/* 确认密码 */}
            <div className={styles.inputGroup}>
              <label htmlFor="confirmPassword" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>重复密码</span>
                  <svg t="1773667809322" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M297.4 250.2c22.6 0 41 18.3 41 41V462c0 22.6-18.3 41-41 41-22.6 0-41-18.3-41-41V291.2c0-22.6 18.4-41 41-41zM701.5 246.2c22.6 0 41 18.3 41 41v169.1c0 22.6-18.3 41-41 41-22.6 0-41-18.3-41-41V287.2c0-22.6 18.4-41 41-41z" fill="#A0A5A8"></path><path d="M499.4 126.2c89 0 161.1 72.1 161.1 161.1h81.9c0-134.2-108.8-243-243-243s-243 108.8-243 243h81.9c0-89 72.2-161.1 161.1-161.1zM865.4 938V482.1c-3.4-33.4-31-59.7-64.9-61H200.6c-37.5 0-68 30.4-68.1 67.9v444.3c4 30.2 27.8 54.2 57.9 58.5h621.5c27-5.4 48.3-26.8 53.5-53.8z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <div className={styles.passwordWrapper}>
                  <input type={showConfirmPassword ? "text" : "password"} id="confirmPassword" name="confirmPassword"
                    value={registerForm.confirmPassword} onChange={handleRegisterChange}
                    className={`${styles.input} ${passwordMatch === "ok" ? styles.inputMatch : passwordMatch === "fail" ? styles.inputMismatch : ""}`}
                    placeholder="请重复密码" maxLength="100" autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.register} />
                  <button type="button" className={styles.passwordToggle} tabIndex={-1}
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                    <span className={showConfirmPassword ? "icon-view-show" : "icon-view-hide"}></span>
                  </button>
                </div>
              </div>
            </div>

            {/* 手机号 */}
            <div className={styles.inputGroup}>
              <label htmlFor="registerPhone" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>手机号</span>
                  <svg t="1773667967270" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M768 64H256c-35.346 0-64 28.654-64 64v768c0 35.346 28.654 64 64 64h512c35.346 0 64-28.654 64-64V128c0-35.346-28.654-64-64-64z m-256 832c-26.51 0-48-21.49-48-48s21.49-48 48-48 48 21.49 48 48-21.49 48-48 48z m208-160H256V192h512v544z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <input type="tel" id="registerPhone" name="phone" value={registerForm.phone}
                  onChange={handleRegisterChange} className={styles.input} placeholder="11 位手机号"
                  maxLength="11" autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.register} />
              </div>
            </div>

            {/* 图片验证码 */}
            <div className={styles.inputGroup}>
              <label htmlFor="captcha" className={styles.label}>
                <span className={styles.labelText}><span className={styles.labelContent}>验证码</span>
                  <svg t="1773670510431" className="icon" viewBox="0 0 1024 1024" width="16" height="16"><path d="M919.561369 245.727541c-0.899486-28.28623-24.311709-55.009871-52.010561-59.8409 0 0-107.385752-16.977673-167.643138-38.420031-75.231425-26.770713-149.681044-85.617983-149.681044-85.617983-23.220864-16.58063-58.83806-15.552208-80.374562 2.372024 0 0-52.704362 53.179177-151.044088 84.22117-90.852194 36.510542-163.464979 40.248679-163.464979 40.248679-27.402093 3.571339-50.991348 28.867468-51.522444 57.147558 0 0-3.690042 145.387251 0.966001 272.985348 1.759063 228.268914 271.994788 453.937606 408.55193 453.937606 134.416386 0 366.709963-157.224858 403.249157-450.619024C925.617295 347.953783 919.561369 245.727541 919.561369 245.727541zM709.887976 445.981401 477.54835 681.152515c-9.899464 10.018168-26.696012 11.174504-38.07927 2.124384l-121.329323-96.414887c-22.289656-17.711384-24.614607-48.538483-4.89038-69.169359 19.587104-20.48966 53.223179-23.199375 75.962066-5.403057l56.322773 44.083008 193.563484-182.358281c20.162202-18.995633 52.216245-18.458397 71.897493 0.325411-0.281409-0.293689-0.35918-0.693802-0.649799-0.984421l1.64036 1.64343c-0.290619-0.290619-0.696872-0.3776-0.99056-0.659009C729.922265 394.23076 729.659275 425.969625 709.887976 445.981401z" fill="#A0A5A8"></path></svg>
                  <span>:</span></span>
              </label>
              <div className={styles.fieldColumn}>
                <div className={styles.captchaGroup}>
                  <input type="text" id="captcha" name="captcha" value={registerForm.captcha}
                    onChange={handleRegisterChange} className={styles.input} placeholder="图片验证码"
                    maxLength="4" autoComplete="off" readOnly onFocus={(e) => { e.target.removeAttribute("readOnly"); }} required disabled={loading.register} />
                  {regCaptcha.image ? (
                    <img src={regCaptcha.image} alt="验证码" className={styles.captchaThumb}
                      onClick={refreshRegCaptcha} title="点击刷新" />
                  ) : (
                    <div className={styles.captchaThumbPlaceholder} onClick={refreshRegCaptcha}>点击<br/>加载</div>
                  )}
                </div>
              </div>
            </div>

            {/* 统一错误提示 —— 与输入框左对齐 */}
            <div className={styles.inputGroup}>
              <div className={styles.label} />
              <div className={styles.fieldColumn}>
                <div className={`${styles.errorMessage} ${error.register ? styles.errorVisible : ""}`}>
                  {error.register && <><span className={styles.errorIcon}>⚠</span><span className={styles.errorText}>{error.register}</span></>}
                </div>
              </div>
            </div>

            <button type="submit" className={`${styles.button} ${styles.primaryButton}`} disabled={loading.register}>
              {loading.register ? "注册中..." : "注册账号"}
            </button>
          </form>
        </section>

        {/* ===================== 切换覆盖层 ===================== */}
        <aside className={`${styles.overlay} ${isAnimating ? styles.animating : ""} ${isLoginActive ? styles.overlayRight : styles.overlayLeft}`}>
          <div className={styles.overlayBackground}>
            <div className={styles.circleBottom}></div>
            <div className={styles.circleTop}></div>
          </div>
          <div className={`${styles.overlayContent} ${isLoginActive ? styles.hidden : ""}`}>
            <h2 className={styles.overlayTitle}>Welcome Back</h2>
            <p className={styles.overlayText}>已经有账号了吗？那去登录进入网页吧</p>
            <button className={styles.overlayButton} onClick={togglePanel}>去登录</button>
          </div>
          <div className={`${styles.overlayContent} ${!isLoginActive ? styles.hidden : ""}`}>
            <h2 className={styles.overlayTitle}>Nice To Meet You</h2>
            <p className={styles.overlayText}>还没有账号吗？那去注册一个自己的账号吧</p>
            <button className={styles.overlayButton} onClick={togglePanel}>去注册</button>
          </div>
        </aside>
      </div>
    </main>
  );
};

export default Login;
