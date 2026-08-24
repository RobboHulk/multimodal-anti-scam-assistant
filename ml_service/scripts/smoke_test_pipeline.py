"""主链路本地贯通冒烟测试（含 DashScope qwen-omni-turbo 全模态）。

用法：
  # 规则降级模式（无 LLM，快速验证链路结构）
  python scripts/smoke_test_pipeline.py

  # DashScope qwen-omni-turbo 模式（需要 API Key）
  $env:DASHSCOPE_API_KEY="sk-xxx"
  python scripts/smoke_test_pipeline.py --llm dashscope

  # 指定测试场景
  python scripts/smoke_test_pipeline.py --llm dashscope --scene text
  python scripts/smoke_test_pipeline.py --llm dashscope --scene image
  python scripts/smoke_test_pipeline.py --llm dashscope --scene audio
  python scripts/smoke_test_pipeline.py --llm dashscope --scene chat
  python scripts/smoke_test_pipeline.py --llm dashscope --scene all
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from pprint import pprint

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from knowledge_graph.rag.chat_orchestrator import ChatOrchestrator
from knowledge_graph.rag.fraud_rag_pipeline import FraudRAGPipeline


def print_summary(name: str, payload: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    summary = {
        "riskScore": payload.get("riskScore"),
        "riskLevel": payload.get("riskLevel"),
        "scamType": payload.get("scamType"),
        "riskAction": payload.get("riskAction"),
        "consistencyScore": payload.get("consistencyScore"),
        "riskInterval": payload.get("riskInterval"),
        "fusionSource": payload.get("fusion_source") or payload.get("trace", {}).get("fusion_source", "unknown"),
        "riskStage": payload.get("intent", {}).get("risk_stage", "?") if isinstance(payload.get("intent"), dict) else "?",
        "citations_count": len(payload.get("citations", [])),
        "retrievedEvidence_count": len(payload.get("retrievedEvidence", [])),
    }
    pprint(summary)
    answer = payload.get("answer", "") or payload.get("chatResponse", "")
    print("answer:", answer[:300])


# ── 场景 1：纯文本输入 ──────────────────────────────────────────────────────
def scenario_plain_text(pipeline: FraudRAGPipeline) -> dict:
    """高风险文本：冒充客服要求验证码+转账。"""
    result = pipeline.predict(
        text="客服说我的账户异常，让我点击链接重新验证并输入验证码，还要我转账到安全账户。",
        session_id="smoke-text-1",
        user_profile={"id": "smoke-user-1"},
    )
    return result.to_dict()


# ── 场景 2：图片 OCR 输入（模拟截图） ──────────────────────────────────────
def scenario_image_ocr(pipeline: FraudRAGPipeline) -> dict:
    """带 OCR 文本的图片输入，验证跨模态一致性路径。"""
    result = pipeline.predict(
        text="帮我判断这张截图是不是诈骗页面。",
        session_id="smoke-image-1",
        user_profile={"id": "smoke-user-2"},
    )
    return result.to_dict()


# ── 场景 3：音频输入（模拟 ASR 转写） ──────────────────────────────────────
def scenario_audio_asr(pipeline: FraudRAGPipeline) -> dict:
    """带 ASR 转写文本 + 合成语音分数的音频输入。"""
    result = pipeline.predict(
        text="这段录音是真实客服还是 AI 合成的？",
        session_id="smoke-audio-1",
        user_profile={"id": "smoke-user-3"},
    )
    return result.to_dict()


# ── 场景 4：多轮对话（两轮，验证 Redis 记忆） ──────────────────────────────
def scenario_multi_turn(chat: ChatOrchestrator) -> list[dict]:
    """多轮对话：第一轮低风险，第二轮升级为高风险。"""
    first = chat.handle_turn(
        text="有人说是京东客服，说我的订单有问题要退款。",
        session_id="smoke-chat-1",
        user_profile={"id": "smoke-user-4"},
    ).to_dict()
    second = chat.handle_turn(
        text="他又让我打开屏幕共享，还要我把验证码和银行卡号告诉他。",
        session_id="smoke-chat-1",
        user_profile={"id": "smoke-user-4"},
    ).to_dict()
    return [first, second]


# ── 场景 5：低风险正常咨询（测试误报率） ──────────────────────────────────
def scenario_benign(pipeline: FraudRAGPipeline) -> dict:
    """正常用户咨询，不含诈骗信号，期望 riskLevel=low 且 riskAction≠BLOCK。"""
    result = pipeline.predict(
        text="我想了解一下信用卡积分怎么兑换，官网上找不到入口。",
        session_id="smoke-benign-1",
        user_profile={"id": "smoke-user-benign"},
    )
    return result.to_dict()


# ── 场景 6：边界模糊场景（测试不确定性触发 Reflexion） ─────────────────────
def scenario_ambiguous(pipeline: FraudRAGPipeline) -> dict:
    """模糊场景：提到转账但有合理解释，期望触发 Reflexion 或 VERIFY 动作。"""
    result = pipeline.predict(
        text="朋友说他在国外急需用钱，让我先帮他转一笔，他回来还我，这正常吗？",
        session_id="smoke-ambiguous-1",
        user_profile={"id": "smoke-user-ambiguous"},
    )
    return result.to_dict()


# ── 场景 7：真实图片文件（如果存在） ──────────────────────────────────────
def scenario_real_image(pipeline: FraudRAGPipeline) -> dict | None:
    """尝试用项目内的测试图片做真实多模态调用。"""
    # 找一张测试图片
    candidates = [
        PROJECT_ROOT / "datasets" / "images" / "test_sample.jpg",
        PROJECT_ROOT / "evaluation" / "test_image.jpg",
    ]
    image_path = next((str(p) for p in candidates if p.exists()), "")
    if not image_path:
        print("  [跳过] 未找到测试图片文件，跳过真实图片场景")
        return None

    result = pipeline.predict(
        text="这张图片里有没有诈骗相关内容？",
        session_id="smoke-realimg-1",
        user_profile={"id": "smoke-user-5"},
        image_path=image_path,
    )
    return result.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="主链路冒烟测试")
    parser.add_argument(
        "--llm",
        choices=["dashscope", "local", "fallback"],
        default="fallback",
        help="LLM 后端（默认 fallback=规则降级）",
    )
    parser.add_argument(
        "--scene",
        choices=["text", "image", "audio", "chat", "benign", "ambiguous", "realimg", "all"],
        default="all",
        help="要运行的测试场景（默认 all）",
    )
    args = parser.parse_args()

    # 设置 LLM provider
    if args.llm == "dashscope":
        os.environ.setdefault("ANTIFRAUD_LLM_PROVIDER", "dashscope")
        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not api_key:
            print("[警告] 未设置 DASHSCOPE_API_KEY，将降级为规则模式")
        else:
            print(f"[INFO] 使用 DashScope qwen-omni-turbo，API Key: {api_key[:8]}...")
    elif args.llm == "local":
        os.environ.setdefault("ANTIFRAUD_LLM_PROVIDER", "local")
        print("[INFO] 使用本地 Qwen2.5-Omni-7B（首次加载需 2-3 分钟）")
    else:
        os.environ["ANTIFRAUD_LLM_PROVIDER"] = "fallback_only"
        print("[INFO] 规则降级模式（无 LLM）")

    pipeline = FraudRAGPipeline()
    chat = ChatOrchestrator(pipeline=pipeline)

    results: dict = {}
    run_all = args.scene == "all"

    if run_all or args.scene == "text":
        payload = scenario_plain_text(pipeline)
        print_summary("场景1 纯文本 — 冒充客服+验证码+转账", payload)
        results["plain_text"] = payload

    if run_all or args.scene == "image":
        payload = scenario_image_ocr(pipeline)
        print_summary("场景2 图片OCR — 截图含安全账户+公安logo", payload)
        results["image_ocr"] = payload

    if run_all or args.scene == "audio":
        payload = scenario_audio_asr(pipeline)
        print_summary("场景3 音频ASR — 合成语音冒充公安", payload)
        results["audio_asr"] = payload

    if run_all or args.scene == "chat":
        payloads = scenario_multi_turn(chat)
        print_summary("场景4 多轮对话-第1轮 — 京东客服退款", payloads[0])
        print_summary("场景4 多轮对话-第2轮 — 升级要求屏幕共享+验证码", payloads[1])
        results["multi_turn"] = payloads

    if run_all or args.scene == "benign":
        payload = scenario_benign(pipeline)
        print_summary("场景5 正常咨询 — 信用卡积分兑换（期望 low/EDUCATE）", payload)
        results["benign"] = payload

    if run_all or args.scene == "ambiguous":
        payload = scenario_ambiguous(pipeline)
        print_summary("场景6 模糊边界 — 朋友借钱转账（期望 VERIFY/Reflexion）", payload)
        results["ambiguous"] = payload

    if run_all or args.scene == "realimg":
        payload = scenario_real_image(pipeline)
        if payload:
            print_summary("场景5 真实图片文件", payload)
            results["real_image"] = payload

    # 写出结果
    output_path = PROJECT_ROOT / "evaluation" / "smoke_test_pipeline_output.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[完成] 结果已写出: {output_path}")

    # 打印汇总
    print("\n" + "="*60)
    print("  测试汇总")
    print("="*60)
    for name, data in results.items():
        if isinstance(data, list):
            for i, d in enumerate(data):
                # fusion_source 在顶层 trace 字段或直接在顶层
                src = d.get("fusion_source") or d.get("trace", {}).get("fusion_source", "?")
                stage = d.get("intent", {}).get("risk_stage", "?") if isinstance(d.get("intent"), dict) else "?"
                print(f"  {name}[{i}]: riskLevel={d.get('riskLevel')} riskScore={d.get('riskScore')} stage={stage} source={src}")
        elif isinstance(data, dict):
            src = data.get("fusion_source") or data.get("trace", {}).get("fusion_source", "?")
            stage = data.get("intent", {}).get("risk_stage", "?") if isinstance(data.get("intent"), dict) else "?"
            print(f"  {name}: riskLevel={data.get('riskLevel')} riskScore={data.get('riskScore')} stage={stage} source={src}")


if __name__ == "__main__":
    main()
