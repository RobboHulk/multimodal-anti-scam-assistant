import { useMemo, useState } from "react";
import Nav from "../../layouts/Nav/Nav";
import styles from "./Reports.module.css";

const reportList = [
  { id: "RPT-0824-03", title: "银行工作人员身份核验诱导", time: "今天 20:42", risk: "高风险", status: "已验证", evidence: 18 },
  { id: "RPT-0823-02", title: "可疑投资群链接核验", time: "昨天 18:06", risk: "高风险", status: "待补证", evidence: 11 },
  { id: "RPT-0822-01", title: "快递理赔短信复核", time: "8月22日", risk: "中风险", status: "已验证", evidence: 9 },
  { id: "RPT-0819-04", title: "熟人语音请求转账", time: "8月19日", risk: "中风险", status: "已验证", evidence: 14 },
];

const claims = [
  { id: "C-01", claim: "工作人员资质图存在局部合成与版面篡改线索", evidence: "IMG-HEAT-01、META-01", state: "已支持" },
  { id: "C-02", claim: "演示链接指向索取账号凭据的页面", evidence: "URL-03、DOMAIN-03", state: "已支持" },
  { id: "C-03", claim: "通话音频存在合成语音异常", evidence: "AUDIO-02、SPEC-03", state: "已支持" },
  { id: "C-04", claim: "用户账号已经泄露", evidence: "无用户执行证据", state: "已撤回" },
];

const auditEvents = [
  ["20:42:18", "报告生成", "已固定18项证据与4项原子主张"],
  ["20:42:11", "结论审计", "C-04缺少用户执行证据，已撤回"],
  ["20:41:56", "音频鉴真", "AUDIO-02定位到00:08—00:13异常区间"],
  ["20:41:44", "图像与链接核验", "资质图完成热力定位，URL-03完成域名检查"],
  ["20:41:30", "隐私处理", "手机号与验证码已遮蔽，域名保留用于核验"],
];

const Reports = () => {
  const [selectedId, setSelectedId] = useState(reportList[0].id);
  const [panel, setPanel] = useState("报告摘要");
  const [integrity, setIntegrity] = useState("valid");
  const selected = useMemo(() => reportList.find((item) => item.id === selectedId), [selectedId]);

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <header className={styles.pageHeader}>
          <div><h1>安全报告</h1><span>个人安全研判记录</span></div>
          <div className={styles.headerButtons}>
            <button type="button">导出脱敏副本</button>
            <button type="button" className={styles.primaryButton} onClick={() => { window.location.href = "/detect"; }}>发起新研判</button>
          </div>
        </header>

        <section className={styles.stats}>
          <div><i className={styles.statBlue}>12</i><span><strong>本机报告</strong><small>最近30天</small></span></div>
          <div><i className={styles.statAmber}>2</i><span><strong>待补证</strong><small>需要继续核验</small></span></div>
          <div><i className={styles.statViolet}>1</i><span><strong>结论已降级</strong><small>避免过度推断</small></span></div>
          <div><i className={styles.statGreen}>9</i><span><strong>完整性通过</strong><small>报告与目录一致</small></span></div>
        </section>

        <div className={styles.reportWorkspace}>
          <aside className={styles.reportQueue}>
            <div className={styles.queueHeader}><h2>报告记录</h2><button type="button">筛选</button></div>
            <div className={styles.searchBox}><span>⌕</span><input placeholder="搜索报告编号或标题" /></div>
            <div className={styles.queueList}>
              {reportList.map((report) => (
                <button type="button" className={[styles.reportItem, selectedId === report.id ? styles.reportActive : ""].filter(Boolean).join(" ")} onClick={() => { setSelectedId(report.id); setIntegrity("valid"); }} key={report.id}>
                  <div className={styles.reportItemTop}><strong>{report.title}</strong><i className={report.risk === "高风险" ? styles.riskHigh : styles.riskMid}>{report.risk}</i></div>
                  <span>{report.id} · {report.time}</span>
                  <div className={styles.reportItemBottom}><b>{report.evidence}项证据</b><em className={report.status === "待补证" ? styles.waiting : ""}>{report.status}</em></div>
                </button>
              ))}
            </div>
          </aside>

          <section className={styles.reportView}>
            <header className={styles.reportHeader}>
              <div>
                <div className={styles.reportIdentity}><span>{selected.id}</span><i>{selected.status}</i></div>
                <h2>{selected.title}</h2>
              </div>
              <div className={styles.reportRisk}><span>当前风险</span><strong>{selected.risk}</strong></div>
            </header>

            <nav className={styles.reportTabs}>
              {["报告摘要", "主张审计", "审计日志"].map((tab) => <button type="button" className={panel === tab ? styles.reportTabActive : ""} onClick={() => setPanel(tab)} key={tab}>{tab}</button>)}
            </nav>

            {panel === "报告摘要" && (
              <div className={styles.reportContent}>
                <div className={styles.summaryRow}>
                  <section className={styles.riskSummary}>
                    <div className={styles.cardTitle}><h3>风险研判</h3><span>证据充分性 88</span></div>
                    <div className={styles.riskBands}>
                      <div><span>内容伪造</span><b><i style={{ width: "84%" }} /></b><strong>84</strong></div>
                      <div><span>网络载荷</span><b><i style={{ width: "91%" }} /></b><strong>91</strong></div>
                      <div><span>认知诱导</span><b><i style={{ width: "89%" }} /></b><strong>89</strong></div>
                    </div>
                    <p>资质图、通话音频与演示链接共同支持身份冒充和凭据窃取诱导结论；用户尚未打开链接或提交信息，当前没有账号泄露与资金损失证据。</p>
                  </section>

                  <section className={styles.integrityCard}>
                    <div className={styles.cardTitle}><h3>完整性验证</h3><span className={integrity === "valid" ? styles.integrityValid : styles.integrityFailed}>{integrity === "valid" ? "验证通过" : "验证失败"}</span></div>
                    <div className={styles.fingerprint}><i /><span><b>SM3 摘要</b><code>{integrity === "valid" ? "54A3 98C2 7F10 D84B" : "9C11 0AF8 46B2 E3D0"}</code></span></div>
                    <dl><div><dt>证据目录</dt><dd>18项</dd></div><div><dt>签发时间</dt><dd>2026-08-24 20:42</dd></div><div><dt>状态</dt><dd>{integrity === "valid" ? "内容未修改" : "检测到内容变化"}</dd></div></dl>
                    <button type="button" onClick={() => setIntegrity(integrity === "valid" ? "failed" : "valid")}>{integrity === "valid" ? "模拟内容修改" : "恢复原始报告"}</button>
                  </section>
                </div>

                <div className={styles.detailRow}>
                  <section className={styles.actionList}>
                    <div className={styles.cardTitle}><h3>行动清单</h3><span>用户尚未操作</span></div>
                    {[
                      ["立即停止", "不要打开链接，不要提交账号、密码或验证码"],
                      ["独立核验", "通过银行官方应用或客服电话核验身份"],
                      ["保留材料", "保存资质图、通话录音和原始消息"],
                    ].map(([title, text], index) => <div key={title}><i>{index + 1}</i><span><strong>{title}</strong><small>{text}</small></span><b>未完成</b></div>)}
                  </section>

                  <section className={styles.auditTrend}>
                    <div className={styles.cardTitle}><h3>审计变化</h3><span>候选主张 5 → 保留 3</span></div>
                    <svg viewBox="0 0 520 190" aria-label="主张审计变化图">
                      <defs><linearGradient id="auditFill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#818cf8" stopOpacity=".35" /><stop offset="1" stopColor="#818cf8" stopOpacity="0" /></linearGradient></defs>
                      <path d="M20 55 C90 48 115 82 180 72 S280 92 330 112 S430 118 500 136 L500 175 L20 175Z" fill="url(#auditFill)" />
                      <path d="M20 55 C90 48 115 82 180 72 S280 92 330 112 S430 118 500 136" fill="none" stroke="#818cf8" strokeWidth="3" />
                      {[["接收",20,55],["补证",180,72],["审计",330,112],["定稿",500,136]].map(([name,x,y]) => <g key={name}><circle cx={x} cy={y} r="6" fill="#0f131c" stroke="#aab4ff" strokeWidth="3" /><text x={x} y="187" textAnchor="middle">{name}</text></g>)}
                    </svg>
                    <div className={styles.auditNumbers}><span><b>3</b>已支持</span><span><b>1</b>已撤回</span><span><b>1</b>待补证</span></div>
                  </section>
                </div>
              </div>
            )}

            {panel === "主张审计" && (
              <div className={styles.claimAudit}>
                <div className={styles.claimHeader}><span>主张编号</span><span>原子主张</span><span>证据引用</span><span>审计状态</span></div>
                {claims.map((claim) => (
                  <div className={styles.claimRow} key={claim.id}>
                    <b>{claim.id}</b><strong>{claim.claim}</strong><span>{claim.evidence}</span><i className={claim.state === "已撤回" ? styles.claimRetracted : styles.claimSupported}>{claim.state}</i>
                  </div>
                ))}
                <aside className={styles.claimExplanation}><i>i</i><p>每项结论只表达一个可验证事实。引用不存在、证据冲突或超出用户实际动作时，系统会降级或撤回主张。</p></aside>
              </div>
            )}

            {panel === "审计日志" && (
              <div className={styles.auditLog}>
                <div className={styles.logToolbar}><span>共 5 条可审计事件</span><button type="button">导出日志</button></div>
                {auditEvents.map(([time, title, detail], index) => (
                  <div className={styles.logItem} key={time}><time>{time}</time><i>{index === 0 ? "✓" : ""}</i><span><strong>{title}</strong><small>{detail}</small></span><button type="button">查看</button></div>
                ))}
              </div>
            )}
          </section>
        </div>

        <p className={styles.boundaryNote}>报告用于个人安全研判与材料复核，不作为公安定性或司法鉴定结论。</p>
      </main>
    </div>
  );
};

export default Reports;
