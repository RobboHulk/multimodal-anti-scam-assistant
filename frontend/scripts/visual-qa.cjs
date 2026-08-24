const { chromium } = require("C:/Users/HulkQin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright");
const path = require("path");

const baseUrl = "http://127.0.0.1:5173";
const outputDir = "D:/Desktop/网挑国赛/ui-check";
const errors = [];

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error") errors.push("console: " + message.text());
  });
  page.on("pageerror", (error) => errors.push("page: " + error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
  });
  page.on("requestfailed", (request) => {
    errors.push(`request failed: ${request.url()} · ${request.failure()?.errorText || "unknown"}`);
  });

  await page.addInitScript(() => {
    localStorage.setItem("token", "visual-qa-token");
    localStorage.setItem("username", "演示用户");
    localStorage.setItem("theme", "dark");
    localStorage.setItem("user", JSON.stringify({ username: "veritide_demo", nickname: "演示用户" }));
  });

  const shot = async (name, route, fullPage = false) => {
    await page.goto(baseUrl + route, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(700);
    await page.screenshot({ path: path.join(outputDir, name + ".png"), fullPage });
  };

  await shot("01-home", "/", false);
  await shot("02-detect", "/detect", false);
  await shot("03-analysis-overview", "/analysis", false);

  for (const tab of ["内容鉴真", "攻击意图链", "证据图谱"]) {
    await page.getByRole("button", { name: new RegExp(tab) }).click();
    await page.waitForTimeout(250);
    await page.screenshot({ path: path.join(outputDir, "03-analysis-" + tab + ".png"), fullPage: false });
  }

  await shot("04-reports", "/reports", false);
  await page.getByRole("button", { name: "主张审计", exact: true }).click();
  await page.screenshot({ path: path.join(outputDir, "04-reports-claims.png"), fullPage: false });
  await page.getByRole("button", { name: "审计日志", exact: true }).click();
  await page.screenshot({ path: path.join(outputDir, "04-reports-log.png"), fullPage: false });
  await shot("05-user", "/user", true);

  console.log(JSON.stringify({ errors, screenshots: 10 }, null, 2));
  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
