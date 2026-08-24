"""
分批执行大型 Cypher 脚本导入 Neo4j。
将脚本按语句分割，每批 500 条提交一次事务，支持断点续传。
"""
import re
import sys
import time
from pathlib import Path

CYPHER_FILE = Path(r"D:\Desktop\multimodal_antifraud_agent\knowledge_graph\cypher_scripts\build_graph_enhanced_v1.0.0.cypher")
PROGRESS_FILE = Path(r"D:\Desktop\multimodal_antifraud_agent\knowledge_graph\cypher_scripts\.import_progress")
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "antifraud2026"
BATCH_SIZE = 200

try:
    from neo4j import GraphDatabase
except ImportError:
    print("安装 neo4j 驱动...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "neo4j", "-q"])
    from neo4j import GraphDatabase


def split_statements(text: str) -> list[str]:
    """按分号分割 Cypher 语句，跳过注释行。"""
    stmts = []
    current = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or stripped == "":
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";")
            if stmt:
                stmts.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip().rstrip(";")
        if stmt:
            stmts.append(stmt)
    return stmts


def load_progress() -> int:
    if PROGRESS_FILE.exists():
        try:
            return int(PROGRESS_FILE.read_text().strip())
        except Exception:
            return 0
    return 0


def save_progress(idx: int):
    PROGRESS_FILE.write_text(str(idx))


def run_batch(session, batch: list[str]) -> tuple[int, int]:
    ok = err = 0
    for stmt in batch:
        try:
            session.run(stmt)
            ok += 1
        except Exception as e:
            err += 1
            if err <= 3:
                print(f"  [WARN] {str(e)[:120]}")
    return ok, err


def main():
    print(f"读取 Cypher 脚本: {CYPHER_FILE.name} ({CYPHER_FILE.stat().st_size/1024/1024:.1f} MB)")
    text = CYPHER_FILE.read_text(encoding="utf-8", errors="replace")
    stmts = split_statements(text)
    total = len(stmts)
    print(f"共 {total} 条语句")

    start_idx = load_progress()
    if start_idx > 0:
        print(f"从断点续传: 第 {start_idx} 条开始")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    t0 = time.time()
    total_ok = total_err = 0

    try:
        with driver.session() as session:
            i = start_idx
            while i < total:
                batch = stmts[i: i + BATCH_SIZE]
                ok, err = run_batch(session, batch)
                total_ok += ok
                total_err += err
                i += len(batch)
                save_progress(i)

                elapsed = time.time() - t0
                pct = i / total * 100
                speed = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / speed if speed > 0 else 0
                print(f"  [{pct:5.1f}%] {i}/{total}  ok={total_ok} err={total_err}  "
                      f"速度={speed:.0f}条/s  ETA={eta:.0f}s", end="\r", flush=True)
    finally:
        driver.close()

    print(f"\n完成: ok={total_ok}, err={total_err}, 耗时={time.time()-t0:.1f}s")
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()

    # 最终统计
    driver2 = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver2.session() as s:
        result = s.run("MATCH (n) RETURN labels(n)[0] AS lbl, count(*) AS cnt ORDER BY cnt DESC LIMIT 10")
        print("\n=== 图谱节点统计 ===")
        for r in result:
            print(f"  {r['lbl']:25} {r['cnt']}")
        result2 = s.run("MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt ORDER BY cnt DESC LIMIT 10")
        print("\n=== 关系统计 ===")
        for r in result2:
            print(f"  {r['rel']:25} {r['cnt']}")
    driver2.close()


if __name__ == "__main__":
    main()
