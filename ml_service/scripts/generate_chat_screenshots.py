"""
generate_chat_screenshots.py
=============================
将 AntiFraudMatrix 诈骗对话数据渲染为仿微信聊天截图 PNG，
补充 RAG 知识库的图片模态数量（聊天截图类型）。

输入：datasets/teleAntiFraud/multi-agents-tools/AntiFraudMatrix/results/*.jsonl
输出：datasets/generated_screenshots/chat_*.png
      knowledge_graph/processed_data/images_manifest.json（追加）
"""
import asyncio
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIALOGUE_DIR = (
    PROJECT_ROOT
    / "datasets" / "teleAntiFraud"
    / "multi-agents-tools" / "AntiFraudMatrix" / "results"
)
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "generated_screenshots"
IMAGES_MANIFEST = PROJECT_ROOT / "knowledge_graph" / "processed_data" / "images_manifest.json"

MAX_PER_FILE = 200   # 每个 jsonl 最多取多少条
CONCURRENCY = 4

# 诈骗类型 → RAG 主类型映射
FRAUD_TYPE_MAP = {
    "投资理财": "INVESTMENT_FRAUD",
    "兼职刷单": "PART_TIME_JOB_FRAUD",
    "冒充公检法": "IMPERSONATE_POLICE_GOV",
    "冒充客服": "IMPERSONATE_CUSTOMER_SERVICE",
    "网络贷款": "FAKE_LOAN",
    "情感诈骗": "ROMANCE_FRAUD",
    "虚假购物": "FAKE_SHOPPING",
    "邮件诈骗": "PHISHING_LINK_QRCODE",
    "中奖诈骗": "LOTTERY_PRIZE_FRAUD",
    "游戏诈骗": "GAME_ITEM_FRAUD",
    "冒充熟人": "IMPERSONATE_ACQUAINTANCE",
    "虚假征信": "FAKE_CREDIT_REPAIR",
}


def get_fraud_rag_type(fraud_type: str) -> str:
    for k, v in FRAUD_TYPE_MAP.items():
        if k in fraud_type:
            return v
    return "OTHER_UNKNOWN"


def build_html(dialogue: dict) -> str:
    """将对话数据渲染为仿微信聊天界面 HTML。"""
    left_msgs = dialogue.get("left", [])
    right_msgs = dialogue.get("right", [])
    fraud_type = dialogue.get("fraud_type", "未知诈骗")
    user_age = dialogue.get("user_age", "")
    occupation = dialogue.get("occupation", "")

    # 交替合并对话（left 先说）
    messages = []
    max_len = max(len(left_msgs), len(right_msgs))
    for i in range(max_len):
        if i < len(left_msgs):
            messages.append(("left", left_msgs[i]))
        if i < len(right_msgs):
            messages.append(("right", right_msgs[i]))

    # 只取前 8 条消息，保证截图不过长
    messages = messages[:8]

    def escape(text: str) -> str:
        return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    msg_html = ""
    for side, text in messages:
        safe_text = escape(str(text))
        if side == "left":
            msg_html += f"""
            <div class="msg-row left">
              <div class="avatar scammer">骗</div>
              <div class="bubble left-bubble">{safe_text}</div>
            </div>"""
        else:
            msg_html += f"""
            <div class="msg-row right">
              <div class="bubble right-bubble">{safe_text}</div>
              <div class="avatar victim">我</div>
            </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1280">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #ededed;
    width: 480px;
    min-height: 720px;
  }}
  .header {{
    background: #2c2c2c;
    color: #fff;
    text-align: center;
    padding: 12px 16px;
    font-size: 16px;
    font-weight: 500;
    position: sticky;
    top: 0;
  }}
  .header .sub {{
    font-size: 11px;
    color: #aaa;
    margin-top: 2px;
  }}
  .chat-area {{
    padding: 12px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .msg-row {{
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }}
  .msg-row.right {{ flex-direction: row-reverse; }}
  .avatar {{
    width: 38px;
    height: 38px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: bold;
    color: #fff;
    flex-shrink: 0;
  }}
  .avatar.scammer {{ background: #e74c3c; }}
  .avatar.victim {{ background: #07c160; }}
  .bubble {{
    max-width: 300px;
    padding: 9px 12px;
    border-radius: 4px;
    font-size: 14px;
    line-height: 1.5;
    word-break: break-all;
    position: relative;
  }}
  .left-bubble {{
    background: #fff;
    border-radius: 0 4px 4px 4px;
  }}
  .left-bubble::before {{
    content: '';
    position: absolute;
    left: -6px;
    top: 10px;
    border: 6px solid transparent;
    border-right-color: #fff;
    border-left: none;
  }}
  .right-bubble {{
    background: #95ec69;
    border-radius: 4px 0 4px 4px;
  }}
  .right-bubble::after {{
    content: '';
    position: absolute;
    right: -6px;
    top: 10px;
    border: 6px solid transparent;
    border-left-color: #95ec69;
    border-right: none;
  }}
  .fraud-label {{
    background: #ff4d4f;
    color: #fff;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    margin: 6px auto;
    display: table;
  }}
</style>
</head>
<body>
  <div class="header">
    微信
    <div class="sub">诈骗类型：{escape(fraud_type)}
    {f'&nbsp;|&nbsp;年龄：{user_age}' if user_age else ''}
    {f'&nbsp;|&nbsp;职业：{escape(str(occupation))}' if occupation else ''}
    </div>
  </div>
  <div class="chat-area">
    <div class="fraud-label">⚠ 疑似诈骗对话</div>
    {msg_html}
  </div>
</body>
</html>"""


def load_dialogues() -> list[dict]:
    """加载所有 jsonl 文件中的对话数据。"""
    all_dialogues = []
    for jsonl_file in sorted(DIALOGUE_DIR.glob("fraud_dialogues-*.jsonl")):
        lines = jsonl_file.read_text(encoding="utf-8").splitlines()
        count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                # 过滤掉 left/right 为空的记录
                if d.get("left") and d.get("right"):
                    all_dialogues.append(d)
                    count += 1
                    if count >= MAX_PER_FILE:
                        break
            except json.JSONDecodeError:
                continue
        print(f"  {jsonl_file.name}: 加载 {count} 条")
    return all_dialogues


def make_output_name(dialogue: dict, idx: int) -> str:
    fraud_type = dialogue.get("fraud_type", "unknown")
    safe_type = re.sub(r"[^\w\u4e00-\u9fff]", "_", fraud_type)[:20]
    h = hashlib.md5(f"{idx}_{fraud_type}".encode()).hexdigest()[:8]
    return f"chat_{safe_type}_{h}.png"


async def render_dialogues(dialogues: list[dict]) -> list[dict]:
    from playwright.async_api import async_playwright

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(CONCURRENCY)
    results = []

    async def render_one(browser, dialogue, idx):
        async with sem:
            out_name = make_output_name(dialogue, idx)
            out_path = OUTPUT_DIR / out_name
            result = {
                "image_id": f"img_chat_{out_name[5:-4]}",
                "file_path": f"datasets/generated_screenshots/{out_name}",
                "filename": out_name,
                "fraud_type": get_fraud_rag_type(dialogue.get("fraud_type", "")),
                "source_fraud_type": dialogue.get("fraud_type", ""),
                "source": "antifraud_matrix_dialogue",
                "interface_type": "chat",
                "chat_platform": "wechat_style",
                "width": 480,
                "height": 720,
                "success": False,
                "error_msg": "",
            }
            if out_path.exists():
                result["success"] = True
                result["error_msg"] = "skipped (exists)"
                return result
            try:
                html_content = build_html(dialogue)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 480, "height": 720})
                await page.set_content(html_content, wait_until="domcontentloaded")
                await asyncio.sleep(0.3)
                await page.screenshot(path=str(out_path), full_page=False)
                await page.close()
                result["success"] = True
            except Exception as e:
                result["error_msg"] = str(e)[:200]
            return result

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [render_one(browser, d, i) for i, d in enumerate(dialogues)]
        total = len(tasks)
        done = 0
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            done += 1
            if done % 100 == 0 or done == total:
                ok = sum(1 for x in results if x["success"])
                print(f"  [{done}/{total}] ok={ok}", flush=True)
        await browser.close()
    return results


def update_images_manifest(results: list[dict]):
    with open(IMAGES_MANIFEST, encoding="utf-8") as f:
        items = json.load(f)
    existing_paths = {x.get("file_path") for x in items}
    added = 0
    for r in results:
        if r["success"] and r["file_path"] not in existing_paths:
            items.append(r)
            existing_paths.add(r["file_path"])
            added += 1
    with open(IMAGES_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"  images_manifest: 新增 {added} 条，总计 {len(items)} 条")


def main():
    print("加载对话数据...")
    dialogues = load_dialogues()
    print(f"共加载 {len(dialogues)} 条对话")

    # 统计诈骗类型分布
    from collections import Counter
    type_dist = Counter(d.get("fraud_type", "unknown") for d in dialogues)
    print("诈骗类型分布（前10）:")
    for t, c in type_dist.most_common(10):
        print(f"  {t}: {c}")

    # 过滤已渲染的
    pending = [d for i, d in enumerate(dialogues)
               if not (OUTPUT_DIR / make_output_name(d, i)).exists()]
    print(f"\n待渲染: {len(pending)} 条（已存在: {len(dialogues) - len(pending)} 条）")

    if not pending:
        print("全部已渲染。")
        update_images_manifest([])
        return

    print(f"开始渲染（并发={CONCURRENCY}）...")
    results = asyncio.run(render_dialogues(pending))

    ok = sum(1 for r in results if r["success"])
    err = sum(1 for r in results if not r["success"])
    print(f"\n渲染完成: 成功={ok}, 失败={err}")

    update_images_manifest(results)
    print("\n聊天截图生成完成。")


if __name__ == "__main__":
    main()
