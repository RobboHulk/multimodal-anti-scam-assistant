"""
render_html_screenshots.py
===========================
将 datasets/maliciousWebPages/*.htm 渲染为 PNG 截图，
输出到 datasets/generated_screenshots/，并更新 screenshots_manifest.json。

依赖：playwright（pip install playwright && playwright install chromium）
"""
import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HTML_DIR = PROJECT_ROOT / "datasets" / "maliciousWebPages"
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "generated_screenshots"
MANIFEST_PATH = PROJECT_ROOT / "knowledge_graph" / "processed_data" / "screenshots_manifest.json"
IMAGES_MANIFEST_PATH = PROJECT_ROOT / "knowledge_graph" / "processed_data" / "images_manifest.json"

WIDTH = 1280
HEIGHT = 720
TIMEOUT_MS = 15000
CONCURRENCY = 4  # 并发渲染数


def make_screenshot_id(html_path: Path) -> str:
    stem = html_path.stem
    h = hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
    return f"malicious web pages_{stem}_{h}"


def make_output_filename(html_path: Path) -> str:
    stem = html_path.stem
    h = hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
    # 清理文件名中的非法字符
    safe_stem = re.sub(r'[<>:"/\\|?*]', '_', stem)[:80]
    return f"malicious web pages_{safe_stem}_{h}.png"


async def render_one(page, html_path: Path, output_path: Path) -> dict:
    result = {
        "screenshot_id": make_screenshot_id(html_path),
        "source_html": f"datasets/maliciousWebPages/{html_path.name}",
        "output_png": f"datasets/generated_screenshots/{output_path.name}",
        "category": "malicious web pages",
        "fraud_type": "PHISHING_LINK_QRCODE",
        "width": WIDTH,
        "height": HEIGHT,
        "success": False,
        "error_msg": "",
        "rendered_at": datetime.now().isoformat(),
    }
    if output_path.exists():
        result["success"] = True
        result["error_msg"] = "skipped (exists)"
        return result
    try:
        file_url = html_path.as_uri()
        await page.goto(file_url, timeout=TIMEOUT_MS, wait_until="domcontentloaded")
        await page.set_viewport_size({"width": WIDTH, "height": HEIGHT})
        await asyncio.sleep(0.5)  # 等待 JS 渲染
        await page.screenshot(path=str(output_path), full_page=False)
        result["success"] = True
    except Exception as e:
        result["error_msg"] = str(e)[:200]
    return result


async def render_batch(html_files: list[Path], output_dir: Path) -> list[dict]:
    from playwright.async_api import async_playwright

    results = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async def render_with_sem(browser, html_path):
        async with sem:
            page = await browser.new_page()
            try:
                out = output_dir / make_output_filename(html_path)
                r = await render_one(page, html_path, out)
            finally:
                await page.close()
            return r

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [render_with_sem(browser, f) for f in html_files]
        total = len(tasks)
        done = 0
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            done += 1
            status = "OK" if r["success"] else "ERR"
            if done % 50 == 0 or done == total:
                ok = sum(1 for x in results if x["success"])
                print(f"  [{done}/{total}] ok={ok}", flush=True)
        await browser.close()
    return results


def update_manifests(results: list[dict]):
    """将渲染结果合并进 screenshots_manifest.json 和 images_manifest.json。"""
    # 更新 screenshots_manifest
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)
    is_dict = isinstance(manifest, dict)
    items = list(manifest.values()) if is_dict else manifest
    existing_ids = {x.get("screenshot_id") for x in items}

    added = 0
    for r in results:
        if r["screenshot_id"] not in existing_ids and r["success"]:
            items.append(r)
            existing_ids.add(r["screenshot_id"])
            added += 1
        else:
            # 更新已有条目的 success 状态
            for item in items:
                if item.get("screenshot_id") == r["screenshot_id"]:
                    item.update(r)
                    break

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        if is_dict:
            keys = list(manifest.keys())
            new_dict = {k: v for k, v in zip(keys, items[:len(keys)])}
            for item in items[len(keys):]:
                new_dict[item["screenshot_id"]] = item
            json.dump(new_dict, f, ensure_ascii=False, indent=2)
        else:
            json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"  screenshots_manifest: 新增 {added} 条")

    # 更新 images_manifest（追加新截图）
    with open(IMAGES_MANIFEST_PATH, encoding="utf-8") as f:
        img_items = json.load(f)
    existing_paths = {x.get("file_path") for x in img_items}

    img_added = 0
    for r in results:
        if not r["success"]:
            continue
        rel_path = r["output_png"]
        if rel_path not in existing_paths:
            stem = Path(r["source_html"]).stem
            h = hashlib.md5(stem.encode("utf-8")).hexdigest()[:8]
            img_items.append({
                "image_id": f"img_malweb_{h}",
                "file_path": rel_path,
                "filename": Path(rel_path).name,
                "fraud_type": "PHISHING_LINK_QRCODE",
                "source": "malicious_web_pages",
                "width": WIDTH,
                "height": HEIGHT,
            })
            existing_paths.add(rel_path)
            img_added += 1

    with open(IMAGES_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(img_items, f, ensure_ascii=False, indent=2)
    print(f"  images_manifest: 新增 {img_added} 条，总计 {len(img_items)} 条")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    html_files = sorted(HTML_DIR.glob("*.htm")) + sorted(HTML_DIR.glob("*.html"))
    print(f"找到 {len(html_files)} 个 HTML 文件")

    # 过滤已渲染的
    pending = [f for f in html_files if not (OUTPUT_DIR / make_output_filename(f)).exists()]
    print(f"待渲染: {len(pending)} 个（已存在: {len(html_files) - len(pending)} 个）")

    if not pending:
        print("全部已渲染，无需重新处理。")
        update_manifests([])
        return

    print(f"开始渲染（并发={CONCURRENCY}）...")
    results = asyncio.run(render_batch(pending, OUTPUT_DIR))

    ok = sum(1 for r in results if r["success"])
    err = sum(1 for r in results if not r["success"])
    print(f"\n渲染完成: 成功={ok}, 失败={err}")

    if err > 0:
        print("失败样例:")
        for r in results:
            if not r["success"]:
                print(f"  {r['source_html']}: {r['error_msg'][:80]}")
                if sum(1 for x in results if not x["success"]) > 5:
                    break

    update_manifests(results)
    print("\n截图渲染完成。")


if __name__ == "__main__":
    main()
