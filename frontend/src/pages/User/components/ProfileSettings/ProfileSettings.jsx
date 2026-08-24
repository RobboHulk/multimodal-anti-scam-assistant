import { useState, useRef, useEffect, useCallback } from "react";
import { useOutletContext } from "react-router-dom";
import { uploadFile } from "../../../../api/chatService";
import styles from "./ProfileSettings.module.css";

const ageGroupMap = { 1: "儿童（需监护人）", 2: "成年人", 3: "老年人" };
const roleToAgeGroup = { "儿童（需监护人）": 1, "青少年": 1, "成年人": 2, "老年人": 3 };
const genderMap = { 1: "男", 2: "女" };
const genderToNum = { "男": 1, "女": 2, "保密": null };

const ProfileSettings = () => {
  const { userData: initialUserData, refreshUser } = useOutletContext();

  const [userData, setUserData] = useState({
    id: null,
    nickname: "",
    avatar: "/icons/default.png",
    role: "成年人",
    phone: "",
    gender: "保密",
    occupation: "",
  });

  const [editingField, setEditingField] = useState(null);
  const [tempValue, setTempValue] = useState("");
  const [notification, setNotification] = useState(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);
  const notificationTimeout = useRef(null);

  const fetchUserProfile = useCallback(async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const resp = await fetch("/api/user/profile", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const result = await resp.json();
        if (result.code === 200 && result.data) {
          const d = result.data;
          setUserData({
            id: d.id,
            nickname: d.username || "",
            avatar: d.avatar || "/icons/default.png",
            role: ageGroupMap[d.ageGroup] || "成年人",
            phone: d.phone || "",
            gender: genderMap[d.gender] || "保密",
            occupation: d.occupation || "",
          });
        }
      }
    } catch (err) {
      console.error("获取用户信息失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUserProfile();
  }, [fetchUserProfile]);

  useEffect(() => {
    if (notification) {
      if (notificationTimeout.current) clearTimeout(notificationTimeout.current);
      notificationTimeout.current = setTimeout(() => setNotification(null), 3000);
    }
    return () => {
      if (notificationTimeout.current) clearTimeout(notificationTimeout.current);
    };
  }, [notification]);

  const showNotification = (message, type = "info") => {
    setNotification({ message, type });
  };

  const getFieldName = (field) => {
    const names = { nickname: "昵称", phone: "手机号", occupation: "职业", gender: "性别", role: "身份角色" };
    return names[field] || field;
  };

  const updateBackend = async (updates) => {
    const token = localStorage.getItem("token");
    if (!token) return false;
    try {
      const resp = await fetch("/api/user/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });
      return resp.ok;
    } catch (err) {
      console.error("更新失败:", err);
      return false;
    }
  };

  const startEdit = (field, value) => {
    setEditingField(field);
    setTempValue(value);
  };

  const saveEdit = async (field) => {
    if (!tempValue || tempValue.trim() === "") {
      showNotification(`${getFieldName(field)}不能为空`, "error");
      setEditingField(null);
      return;
    }
    if (field === "phone" && !/^1[3-9]\d{9}$/.test(tempValue)) {
      showNotification("请输入正确的11位手机号", "error");
      return;
    }

    const backendField = field === "nickname" ? null : field;
    let updates = {};
    if (field === "phone") updates.phone = tempValue;
    if (field === "occupation") updates.occupation = tempValue;

    if (Object.keys(updates).length > 0) {
      const success = await updateBackend(updates);
      if (!success) {
        showNotification(`${getFieldName(field)}更新失败`, "error");
        return;
      }
    }

    setUserData((prev) => ({ ...prev, [field]: tempValue }));
    showNotification(`${getFieldName(field)}修改成功`, "success");
    setEditingField(null);
    setTempValue("");
    if (refreshUser) refreshUser();
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowedTypes = ["image/jpeg", "image/png", "image/jpg", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      showNotification("只支持 JPG、PNG、WEBP 格式", "error");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      showNotification("图片大小不能超过 2MB", "error");
      return;
    }

    setUploadingAvatar(true);
    try {
      const avatarUrl = await uploadFile(file);
      const token = localStorage.getItem("token");
      const res = await fetch("/api/user/avatar", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ avatar: avatarUrl }),
      });
      if (!res.ok) throw new Error("更新头像失败");
      setUserData((prev) => ({ ...prev, avatar: avatarUrl }));
      if (refreshUser) await refreshUser();
      showNotification("头像更新成功", "success");
    } catch (err) {
      showNotification(err.message || "头像上传失败", "error");
    } finally {
      setUploadingAvatar(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const renderField = (field, label, type = "text", required = false) => (
    <div className={styles.formGroup} key={field}>
      <label htmlFor={field}>
        {label} {required && <span className={styles.required}>*</span>}
      </label>
      <div className={styles.formField}>
        {editingField === field ? (
          <div className={styles.editContainer}>
            <input
              type={type}
              value={tempValue}
              onChange={(e) => setTempValue(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && saveEdit(field)}
              autoFocus
              placeholder={`请输入${label}`}
            />
            <button onClick={() => saveEdit(field)} className={styles.confirmBtn}>确认</button>
            <button onClick={() => setEditingField(null)} className={styles.cancelBtn}>取消</button>
          </div>
        ) : (
          <div className={styles.displayField}>
            <input type="text" value={userData[field] || ""} readOnly />
            <button onClick={() => startEdit(field, userData[field] || "")} className={styles.editBtn}>修改</button>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={styles.container}>
      {notification && (
        <div className={`${styles.notification} ${styles[notification.type]}`}>
          <span>{notification.message}</span>
          <button className={styles.notificationClose} onClick={() => setNotification(null)}>×</button>
        </div>
      )}

      <header className={styles.header}>
        <div className={styles.info}>
          <h1 className={styles.title}>个人信息</h1>
          <div className={styles.subtitle}>管理您的基本账户信息</div>
        </div>
      </header>

      <div className={styles.content}>
        <div className={`${styles.information} ${styles.section}`}>
          <div className={styles.settingForm}>
            <div className={styles.avatarSection}>
              <div className={styles.avatarWrapper}>
                <div 
                  className={`${styles.avatarImg} ${uploadingAvatar ? styles.uploading : ''}`}
                  onClick={() => !uploadingAvatar && fileInputRef.current?.click()}
                >
                  <img src={userData.avatar} alt="avatar" />
                  <div className={styles.avatarOverlay}>
                    {uploadingAvatar ? (
                      <span className={styles.uploadingText}>上传中...</span>
                    ) : (
                      <span className={styles.uploadHint}>点击更换</span>
                    )}
                  </div>
                </div>
                <button 
                  className={styles.uploadBtn} 
                  onClick={() => fileInputRef.current?.click()} 
                  type="button"
                  disabled={uploadingAvatar}
                >
                  {uploadingAvatar ? "上传中..." : "更换头像"}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/jpg,image/webp"
                  style={{ display: "none" }}
                  onChange={handleAvatarUpload}
                />
              </div>
              <div className={styles.avatarTip}>支持 JPG、PNG 等格式，图片需小于 2M</div>
            </div>

            <div className={styles.formSection}>
              {renderField("nickname", "昵称", "text", true)}
              {renderField("phone", "手机号", "tel", true)}
              {renderField("occupation", "职业", "text", false)}

              <div className={styles.formGroup}>
                <label>性别</label>
                <div className={styles.formField}>
                  <div className={styles.radioGroup}>
                    {["男", "女", "保密"].map((g) => (
                      <label key={g} className={styles.radioLabel}>
                        <input
                          type="radio"
                          name="gender"
                          value={g}
                          checked={userData.gender === g}
                          onChange={async (e) => {
                            const newGender = e.target.value;
                            const genderNum = genderToNum[newGender];
                            if (genderNum !== null) {
                              await updateBackend({ gender: genderNum });
                            }
                            setUserData((prev) => ({ ...prev, gender: newGender }));
                            showNotification("性别修改成功", "success");
                          }}
                        />
                        <span>{g}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="role">身份角色</label>
                <div className={styles.formField}>
                  <select
                    className={styles.selectInput}
                    value={userData.role}
                    id="role"
                    onChange={async (e) => {
                      const newRole = e.target.value;
                      const ageGroup = roleToAgeGroup[newRole];
                      if (ageGroup) {
                        await updateBackend({ ageGroup });
                      }
                      setUserData((prev) => ({ ...prev, role: newRole }));
                      showNotification("身份角色修改成功", "success");
                    }}
                  >
                    <option>儿童（需监护人）</option>
                    <option>青少年</option>
                    <option>成年人</option>
                    <option>老年人</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className={`${styles.safe} ${styles.section}`}>
          <h2 className={styles.sectionTitle}>账户安全</h2>
          <div className={styles.securityList}>
            <div className={styles.securityItem}>
              <div className={styles.itemInfo}>
                <h4>登录密码</h4>
                <p>已设置，建议定期更换以保障账户安全</p>
              </div>
              <button className={styles.securityAction}>修改密码</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileSettings;
