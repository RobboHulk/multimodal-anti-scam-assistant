const { chromium } = require("C:/Users/HulkQin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const path = require("path");
const fs = require("fs");

const baseUrl = "http://127.0.0.1";
const outputDir = "D:/Desktop/网挑国赛/ui-check-video";
const pdfOutputDir = "D:/Desktop/网挑国赛/multimodal-anti-scam-assistant/output/pdf";
const errors = [];

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") errors.push("console: " + message.text()); });
  page.on("pageerror", (error) => errors.push("page: " + error.message));
  page.on("response", (response) => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
  await page.addInitScript(() => {
    localStorage.setItem("token", "video-qa-token");
    localStorage.setItem("username", "演示用户");
    localStorage.setItem("theme", "dark");
    localStorage.removeItem("veritide_detect_history");
  });

  await page.goto(baseUrl + "/detect", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "载入演示案例" }).click();
  await page.locator('input[type="file"]').setInputFiles([
    "D:/Desktop/网挑国赛/拍视频案例/银行工作人员资质证明.png",
    "D:/Desktop/网挑国赛/拍视频案例/通话录音.m4a",
    "D:/Desktop/网挑国赛/拍视频案例/案例视频.mp4",
  ]);
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(outputDir, "01-detect-ready.png") });
  await page.getByRole("button", { name: /开始研判/ }).click();
  await page.waitForTimeout(3600);
  await page.screenshot({ path: path.join(outputDir, "02-deep-processing.png") });
  await page.waitForTimeout(10300);
  await page.screenshot({ path: path.join(outputDir, "03-fixed-result.png") });
  const chatScroll = await page.locator('[class*="chatMessages"]').evaluate((node) => ({ scrollHeight: node.scrollHeight, clientHeight: node.clientHeight, scrollTop: node.scrollTop }));
  const historyBeforeDelete = await page.getByRole("button", { name: /删除研判记录/ }).count();
  if (historyBeforeDelete) await page.getByRole("button", { name: /删除研判记录/ }).first().click();
  const historyAfterDelete = await page.getByRole("button", { name: /删除研判记录/ }).count();

  await page.goto(baseUrl + "/analysis", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: /内容鉴真/ }).click();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(outputDir, "04-content-forensics.png"), fullPage: false });
  await page.getByText("可疑区间局部放大", { exact: true }).scrollIntoViewIfNeeded();
  await page.waitForTimeout(250);
  await page.screenshot({ path: path.join(outputDir, "05-audio-waveform.png"), fullPage: false });

  await page.goto(baseUrl + "/reports", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(600);
  await page.screenshot({ path: path.join(outputDir, "06-report-export.png"), fullPage: false });
  fs.mkdirSync(pdfOutputDir, { recursive: true });
  const downloadPromise = page.waitForEvent("download", { timeout: 30000 });
  await page.getByRole("button", { name: /一键导出 PDF/ }).click();
  const download = await downloadPromise;
  const pdfPath = path.join(pdfOutputDir, "智鉴安澜-RPT-0824-03-安全研判报告.pdf");
  await download.saveAs(pdfPath);
  console.log(JSON.stringify({ errors, screenshots: 6, chatScroll, historyBeforeDelete, historyAfterDelete, pdfPath }, null, 2));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
