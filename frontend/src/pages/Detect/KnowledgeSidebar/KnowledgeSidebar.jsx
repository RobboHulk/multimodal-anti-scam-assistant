// src/pages/Detect/KnowledgeSidebar.jsx
import { useState, useEffect } from "react";
import styles from "./KnowledgeSidebar.module.css";
import Icons from "../../../data/detectIcons";

const KnowledgeSidebar = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState("policy");
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
    } else {
      const timer = setTimeout(() => setIsVisible(false), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const knowledgeData = {
    policy: {
      title: "政策解读",
      items: [
        {
          title: "关于进一步规范大学生互联网消费贷款监督管理工作的通知",
          summary: "银保监发〔2021〕8号文件确实存在，但文件内容被故意曲解。",
          detail:
            "文件旨在规范大学生互联网消费贷款，保护学生权益，并非要求强制注销校园贷账户。诈骗分子利用真实政策文件制造恐慌，诱导受害者进行资金操作。",
          tags: ["银保监会", "2021年第8号", "校园贷规范"],
        },
        {
          title: "中国人民银行关于加强支付受理终端及相关业务管理的通知",
          summary: "支付受理终端管理新规，防范跨境赌博、电信诈骗等风险。",
          detail:
            "该通知强化了支付终端管理，要求收单机构建立终端序列号与收单机构代码等要素的关联对应关系。",
          tags: ["央行", "支付安全", "反洗钱"],
        },
      ],
    },
    scam: {
      title: "诈骗识别",
      items: [
        {
          title: "校园贷注销诈骗特点",
          summary: "冒充金融平台客服，声称需要注销校园贷账户",
          detail:
            "以影响征信为由制造恐慌，诱导下载虚假APP并转账，利用真实政策文件制造可信度。",
          tags: ["校园贷", "征信威胁", "注销诈骗"],
        },
        {
          title: "冒充客服诈骗话术特征",
          summary:
            "身份冒充 → 确认信息 → 制造恐慌 → 曲解政策 → 诱导操作 → 要求转账",
          detail:
            "诈骗分子通常会先建立信任，然后制造紧急情况，最后诱导受害者进行资金操作。",
          tags: ["话术分析", "冒充客服", "心理操控"],
        },
      ],
    },
    prevention: {
      title: "防范措施",
      items: [
        {
          title: "官方客服核实指南",
          summary:
            "官方客服不会通过个人微信联系您，涉及资金操作需通过官方渠道验证。",
          detail:
            "接到可疑电话时，挂断后主动拨打官方客服热线核实。不要使用对方提供的联系方式。",
          tags: ["核实方法", "官方渠道", "主动联系"],
        },
        {
          title: "96110反诈热线使用说明",
          summary: "全国统一反诈预警劝阻咨询专线",
          detail:
            "接到96110来电说明您或家人正在遭遇诈骗，请务必接听。发现诈骗线索也可拨打举报。",
          tags: ["96110", "反诈热线", "紧急求助"],
        },
      ],
    },
  };

  const tabs = [
    { id: "policy", label: "政策解读", icon: Icons.policy },
    { id: "scam", label: "诈骗识别", icon: Icons.Fraud },
    { id: "prevention", label: "防范措施", icon: Icons.protect },
  ];

  const currentData = knowledgeData[activeTab];

  return (
    <>
      {isVisible && (
        <div
          className={`${styles.sidebar} ${isOpen ? styles.open : styles.closed}`}
        >
          <div className={styles.header}>
            <div className={styles.title}>
              <span className={styles.icon}>{Icons.knowledge}</span>
              <h3>知识库</h3>
            </div>
            <button className={styles.closeBtn} onClick={onClose}>
              ×
            </button>
          </div>

          <div className={styles.tabs}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`${styles.tab} ${activeTab === tab.id ? styles.active : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          <div className={styles.content}>
            <div className={styles.sectionTitle}>
              <span>{currentData.title}</span>
            </div>
            <div className={styles.knowledgeList}>
              {currentData.items.map((item, index) => (
                <div key={index} className={styles.knowledgeCard}>
                  <h4>{item.title}</h4>
                  <p className={styles.summary}>{item.summary}</p>
                  <p className={styles.detail}>{item.detail}</p>
                  <div className={styles.tags}>
                    {item.tags.map((tag, i) => (
                      <span key={i} className={styles.tag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.footer}>
            <p>内容来源于官方公开资料，仅供参考</p>
          </div>
        </div>
      )}
    </>
  );
};

export default KnowledgeSidebar;
