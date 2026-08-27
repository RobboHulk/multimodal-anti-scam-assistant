import { useMemo, useState } from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
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

const escapeHtml = (text = "") => text
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;");

const inlineMarkdown = (text = "") => escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

const buildReportMarkdown = (report) => `# 智鉴安澜安全研判报告

**${report.title}**

报告编号：${report.id}
生成时间：2026-08-24 20:42
综合风险：${report.risk}
证据数量：${report.evidence} 项

## AI 研判结论

现有图片、通话录音与链接共同支持“虚假银行工作人员身份冒充并诱导用户提交账户凭据”的判断。资质图片负责建立权威身份，通话内容制造账户异常与限时处理压力，仿冒页面进一步索取账号、密码和短信验证码。

用户明确表示尚未打开链接、提交凭据或转账，因此当前没有账号已泄露、账户已被接管或资金已经损失的证据。攻击链仍可在凭据请求阶段中断。

> 综合结论：建议将本次事件按高风险社会工程诱导处置，同时保留“尚未发生实际损害”的判断边界。

## 风险可视化

- 内容伪造：84/100
- 网络载荷：91/100
- 认知诱导：89/100
- 证据充分性：88/100

## 多模态证据分析

- **IMG-HEAT-01｜资质图片：** 人物边界、印章叠加和编号区域存在局部噪声、频域纹理与版面一致性异常，图像伪造风险为 87。
- **AUDIO-02｜通话录音：** 00:08—00:13 出现谐波截断、相位跳变及韵律过度规则等合成语音线索，音频风险为 86。
- **URL-03｜核验链接：** 域名与声称的银行主体不一致，页面包含密码和短信验证码收集字段，网络载荷风险为 95。
- **META-01｜来源信息：** 文件创建软件字段与时间链不完整，未发现可验证的生成内容标识或 C2PA 来源凭证。

## 攻击意图链

身份接触 → 资质塑造 → 信任强化 → 紧迫施压 → 凭据请求 → 账户接管（条件推演）

已观察到攻击推进至“凭据请求”；“账户接管”仅为用户提交凭据后的条件性推演，不作为已经发生的事实。

## 处置建议

- **立即停止：** 不要打开对方提供的链接，不要提交账号、密码或短信验证码。
- **独立核验：** 通过银行官方 App、银行卡背面的客服电话或线下网点核验身份。
- **保留材料：** 保存原始资质图、通话录音、聊天记录、链接和页面截图。
- **误点处置：** 如果已经访问页面或输入过信息，立即修改网银密码并联系银行限制高风险操作。

## 结论审计与边界

- 有效证据引用：18 项
- 已支持原子主张：3 项
- 已撤回主张：1 项（“用户账号已经泄露”缺少执行与后果证据）
- 报告完整性：SM3 摘要验证通过

本报告用于个人安全研判与材料复核，不作为公安定性、司法鉴定或身份认定结论。`;

const markdownToReportHtml = (markdown) => {
  const sections = markdown.trim().split(/\n(?=## )/);
  return sections.map((section, sectionIndex) => {
    const lines = section.split("\n").filter((line) => line.trim());
    const heading = lines.shift() || "";
    const title = heading.replace(/^#{1,2}\s+/, "");
    const body = [];
    let listOpen = false;
    const closeList = () => {
      if (listOpen) body.push("</ul>");
      listOpen = false;
    };

    lines.forEach((line) => {
      const risk = line.match(/^- (.+?)：(\d+)\/100$/);
      if (risk) {
        closeList();
        body.push(`<div style="display:grid;grid-template-columns:120px 1fr 44px;align-items:center;gap:14px;margin:12px 0;color:#334155;font-size:15px"><span>${escapeHtml(risk[1])}</span><i style="height:10px;overflow:hidden;border-radius:99px;background:#e2e8f0"><b style="display:block;width:${risk[2]}%;height:100%;border-radius:inherit;background:linear-gradient(90deg,#6366f1,#ef476f)"></b></i><strong style="color:#0f172a;text-align:right">${risk[2]}</strong></div>`);
        return;
      }
      if (line.startsWith("- ")) {
        if (!listOpen) {
          body.push('<ul style="margin:8px 0;padding-left:24px;color:#334155">');
          listOpen = true;
        }
        body.push(`<li style="margin:8px 0;line-height:1.72">${inlineMarkdown(line.slice(2))}</li>`);
        return;
      }
      closeList();
      if (line.startsWith("> ")) {
        body.push(`<blockquote style="margin:14px 0;padding:13px 16px;border-left:4px solid #6366f1;border-radius:0 9px 9px 0;background:#eef2ff;color:#312e81;line-height:1.72">${inlineMarkdown(line.slice(2))}</blockquote>`);
      } else if (line.includes("→")) {
        body.push(`<div style="display:flex;flex-wrap:wrap;gap:8px;margin:15px 0">${line.split("→").map((item, index, array) => `<span style="padding:8px 11px;border:${item.includes("条件推演") ? "1px dashed #ef476f" : "1px solid #c7d2fe"};border-radius:8px;background:${item.includes("条件推演") ? "#fff1f2" : "#eef2ff"};color:${item.includes("条件推演") ? "#be123c" : "#3730a3"};font-size:13px">${escapeHtml(item.trim())}</span>${index < array.length - 1 ? '<b style="align-self:center;color:#94a3b8">→</b>' : ""}`).join("")}</div>`);
      } else {
        body.push(`<p style="margin:9px 0;color:#334155;font-size:15px;line-height:1.78">${inlineMarkdown(line.replace(/\s{2}$/, ""))}</p>`);
      }
    });
    closeList();

    return `<section data-pdf-section style="margin:0 0 18px;padding:${sectionIndex === 0 ? "28px 30px" : "22px 26px"};border:1px solid #dbe3ef;border-radius:14px;background:#fff;box-shadow:0 8px 26px rgba(15,23,42,.05)"><${sectionIndex === 0 ? "h1" : "h2"} style="margin:0 0 15px;color:#0f172a;font-size:${sectionIndex === 0 ? "30px" : "21px"};letter-spacing:-.02em">${escapeHtml(title)}</${sectionIndex === 0 ? "h1" : "h2"}>${body.join("")}</section>`;
  }).join("");
};

const Reports = () => {
  const [selectedId, setSelectedId] = useState(reportList[0].id);
  const [panel, setPanel] = useState("报告摘要");
  const [integrity, setIntegrity] = useState("valid");
  const [isExporting, setIsExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState("");
  const selected = useMemo(() => reportList.find((item) => item.id === selectedId), [selectedId]);

  const exportPdf = async () => {
    if (isExporting) return;
    setIsExporting(true);
    setExportNotice("正在生成 PDF…");
    const host = document.createElement("div");
    host.setAttribute("aria-hidden", "true");
    host.style.cssText = "position:fixed;left:-12000px;top:0;width:920px;padding:34px;background:#f4f7fb;font-family:'Microsoft YaHei','PingFang SC',sans-serif;z-index:-1";
    host.innerHTML = markdownToReportHtml(buildReportMarkdown(selected));
    document.body.appendChild(host);

    try {
      await document.fonts?.ready;
      const pdf = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait", compress: true });
      const pageWidth = 210;
      const pageHeight = 297;
      const marginX = 12;
      const contentWidth = pageWidth - marginX * 2;
      const bottomLimit = pageHeight - 16;
      let cursorY = 12;
      const sections = Array.from(host.querySelectorAll("[data-pdf-section]"));

      for (const section of sections) {
        const canvas = await html2canvas(section, { scale: 2, backgroundColor: "#ffffff", logging: false, useCORS: true });
        const renderHeight = canvas.height * (contentWidth / canvas.width);
        if (cursorY + renderHeight > bottomLimit && cursorY > 12) {
          pdf.addPage();
          cursorY = 12;
        }
        const fittedHeight = Math.min(renderHeight, bottomLimit - cursorY);
        const fittedWidth = contentWidth * (fittedHeight / renderHeight);
        pdf.addImage(canvas.toDataURL("image/jpeg", .94), "JPEG", marginX, cursorY, fittedWidth, fittedHeight, undefined, "FAST");
        cursorY += fittedHeight + 5;
      }

      const pages = pdf.getNumberOfPages();
      for (let page = 1; page <= pages; page += 1) {
        pdf.setPage(page);
        pdf.setFontSize(9);
        pdf.setTextColor(100, 116, 139);
        pdf.text(`VERITIDE · ${selected.id}`, marginX, 290);
        pdf.text(`${page} / ${pages}`, 198, 290, { align: "right" });
      }
      pdf.save(`智鉴安澜-${selected.id}-安全研判报告.pdf`);
      setExportNotice("PDF 已导出");
      window.setTimeout(() => setExportNotice(""), 2600);
    } catch (error) {
      console.error("PDF export failed", error);
      setExportNotice("导出失败，请重试");
    } finally {
      host.remove();
      setIsExporting(false);
    }
  };

  return (
    <div className={styles.page}>
      <Nav />
      <main className={styles.main}>
        <header className={styles.pageHeader}>
          <div><h1>安全报告</h1><span>个人安全研判记录</span></div>
          <div className={styles.headerButtons}>
            {exportNotice && <span className={styles.exportNotice}>{exportNotice}</span>}
            <button type="button" className={styles.exportButton} onClick={exportPdf} disabled={isExporting}>{isExporting ? "正在生成…" : "一键导出 PDF"}</button>
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
