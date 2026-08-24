import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Nav from "../../layouts/Nav/Nav";
import { logout } from "../../utils/auth";
import styles from "./User.module.css";

const Toggle = ({ checked, onChange, label }) => (
  <button type="button" className={[styles.toggle, checked ? styles.toggleOn : ""].filter(Boolean).join(" ")} onClick={() => onChange(!checked)} aria-label={label} aria-pressed={checked}>
    <span />
  </button>
);

const User = () => {
  const navigate = useNavigate();
  const storedUser = JSON.parse(localStorage.getItem("user") || "{}");
  const [nickname, setNickname] = useState(storedUser.nickname || localStorage.getItem("username") || "演示用户");
  const [privacy, setPrivacy] = useState({ precheck: true, localHistory: true, improvement: false });
  const [retention, setRetention] = useState("30天");
  const [editing, setEditing] = useState(false);

  const saveProfile = () => {
    localStorage.setItem("user", JSON.stringify({ ...storedUser, nickname }));
    localStorage.setItem("username", nickname);
    setEditing(false);
  };

  const signOut = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <header className={styles.pageHeader}><h1>个人中心</h1><span>管理账号、安全和数据偏好</span></header>
        <div className={styles.profileLayout}>
          <aside className={styles.profileCard}>
            <div className={styles.avatarLarge}><img src="/demo/landscape-avatar.png" alt="风景头像" /></div>
            <h2>{nickname}</h2>
            <span>普通用户</span>
            <div className={styles.accountState}><i />账号状态正常</div>
            <nav>
              <a href="#account" className={styles.current}>账号信息</a>
              <a href="#security">登录安全</a>
              <a href="#privacy">隐私与数据</a>
            </nav>
            <button type="button" className={styles.logoutButton} onClick={signOut}>退出登录</button>
          </aside>

          <div className={styles.settings}>
            <section id="account" className={styles.settingCard}>
              <div className={styles.cardHeader}><div><h2>账号信息</h2><span>用于登录和报告显示</span></div><button type="button" onClick={() => editing ? saveProfile() : setEditing(true)}>{editing ? "保存" : "编辑"}</button></div>
              <div className={styles.formRows}>
                <label><span>昵称</span><input value={nickname} readOnly={!editing} onChange={(event) => setNickname(event.target.value)} /></label>
                <label><span>账号</span><input value={storedUser.username || "veritide_demo"} readOnly /></label>
                <label><span>手机号</span><input value="138 **** 6024" readOnly /></label>
                <label><span>注册时间</span><input value="2026年4月18日" readOnly /></label>
              </div>
            </section>

            <section id="security" className={styles.settingCard}>
              <div className={styles.cardHeader}><div><h2>登录安全</h2><span>保护账号和研判记录</span></div></div>
              <div className={styles.settingRows}>
                <div><i className={styles.securityIcon}>密</i><span><strong>登录密码</strong><small>建议定期更换高强度密码</small></span><button type="button">修改</button></div>
                <div><i className={styles.securityIcon}>验</i><span><strong>二次验证</strong><small>新设备登录时进行身份确认</small></span><button type="button">开启</button></div>
                <div><i className={styles.securityIcon}>设</i><span><strong>登录设备</strong><small>当前1台设备保持登录</small></span><button type="button">查看</button></div>
              </div>
            </section>

            <section id="privacy" className={styles.settingCard}>
              <div className={styles.cardHeader}><div><h2>隐私与数据</h2><span>控制材料处理和记录留存</span></div></div>
              <div className={styles.privacyRows}>
                <div><span><strong>提交前隐私预检</strong><small>识别并提示身份证号、验证码等敏感信息</small></span><Toggle checked={privacy.precheck} onChange={(value) => setPrivacy({ ...privacy, precheck: value })} label="提交前隐私预检" /></div>
                <div><span><strong>保存本机研判记录</strong><small>便于回看报告和证据引用</small></span><Toggle checked={privacy.localHistory} onChange={(value) => setPrivacy({ ...privacy, localHistory: value })} label="保存本机研判记录" /></div>
                <div><span><strong>匿名改进产品</strong><small>默认关闭，不上传原始材料</small></span><Toggle checked={privacy.improvement} onChange={(value) => setPrivacy({ ...privacy, improvement: value })} label="匿名改进产品" /></div>
                <div><span><strong>记录留存期限</strong><small>到期后自动清理本机记录</small></span><select value={retention} onChange={(event) => setRetention(event.target.value)}><option>7天</option><option>30天</option><option>90天</option><option>不自动删除</option></select></div>
              </div>
              <div className={styles.dataActions}><button type="button">导出个人数据</button><button type="button" className={styles.dangerButton}>删除全部研判记录</button></div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default User;
