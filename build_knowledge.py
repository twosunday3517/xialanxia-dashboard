#!/usr/bin/env python3
"""
build_knowledge.py — 🧠 从 Dashboard 数据构建 RAG 知识库

安装依赖（只需一次）：
    pip install chromadb sentence-transformers

用法：
    python build_knowledge.py              # 构建知识库
    python build_knowledge.py --query "..." # 查询
    python build_knowledge.py --rebuild     # 强制重建
"""

import json, os, sys, argparse
from pathlib import Path

HERE = Path(__file__).parent
DATA_JSON = HERE / "data.json"
DB_DIR = HERE / "knowledge_db"

# ============ 文档构建器 ============

def load_data():
    """从 data.json 加载数据"""
    if not DATA_JSON.exists():
        print(f"❌ 未找到 {DATA_JSON}")
        sys.exit(1)
    return json.loads(DATA_JSON.read_text(encoding="utf-8"))


def build_documents(data) -> list[dict]:
    """将 data.json 中的所有内容转为文档列表
    每条文档 = {id, text, source, date, category}
    """
    docs = []

    # 1. 论文（memories）
    for i, m in enumerate(data.get("memories", [])):
        docs.append({
            "id": f"paper_{i:03d}",
            "text": f"论文：{m.get('title','')}。摘要：{m.get('summary','')}",
            "source": "论文",
            "date": m.get("time", ""),
            "category": "论文",
            "url": m.get("url", ""),
            "summary": m.get("summary", ""),
        })

    # 2. 网站推荐（cronTasks）
    for i, t in enumerate(data.get("cronTasks", [])):
        docs.append({
            "id": f"web_{i:03d}",
            "text": f"网站：{t.get('name','')}。类型：{t.get('cron','')}。说明：{t.get('lastRun','')}",
            "source": "网站",
            "date": "",
            "category": "网站",
            "url": t.get("url", ""),
            "summary": t.get("lastRun", ""),
        })

    # 3. 开源项目（watchlist）
    for i, w in enumerate(data.get("watchlist", [])):
        docs.append({
            "id": f"oss_{i:03d}",
            "text": f"开源项目：{w.get('ticker','')}。特性：{w.get('price','')}。方向：{w.get('trigger','')}。推荐理由：{w.get('direction','')}",
            "source": "开源",
            "date": "",
            "category": "开源",
            "url": w.get("url", ""),
            "summary": w.get("direction", ""),
        })

    # 4. 每日日志（logs）
    for day in data.get("logs", []):
        date = day.get("date", "")
        for j, e in enumerate(day.get("entries", [])):
            docs.append({
                "id": f"log_{date}_{j:03d}",
                "text": f"[{date} {e.get('time','')}] {e.get('action','')}（分类：{e.get('tag','')}）",
                "source": "日志",
                "date": date,
                "category": e.get("tag", "其他"),
                "url": "",
                "summary": e.get("action", ""),
            })

    # 5. 比赛（在 HTML 里硬编码的，也加到知识库）
    competitions = [
        {"name": "电赛电源组", "time": "8月", "deadline": "7月", "prepare": "Buck/Boost 拓扑"},
        {"name": "TI杯电源设计赛", "time": "9月", "deadline": "8月", "prepare": "TI 芯片方案选型"},
        {"name": "中国电源学会竞赛", "time": "10月", "deadline": "9月", "prepare": "论文方向"},
        {"name": "集成电路双创赛", "time": "7月", "deadline": "6月", "prepare": "尽快报名"},
    ]
    for i, c in enumerate(competitions):
        docs.append({
            "id": f"comp_{i:03d}",
            "text": f"比赛：{c['name']}。时间：{c['time']}。报名截止：{c['deadline']}。准备：{c['prepare']}",
            "source": "比赛",
            "date": "",
            "category": "比赛",
            "url": "",
            "summary": c['prepare'],
        })

    # 6. AI 工具（在 HTML 里，也加进来）
    aitools = [
        {"name": "VS Code + Copilot", "use": "AI 补全 STM32 代码"},
        {"name": "PLECS + DeepSeek", "use": "AI 辅助电力电子仿真"},
        {"name": "MATLAB/Simulink + Claude", "use": "AI 生成 Bode 图、PID 整定"},
        {"name": "Altium + ChatGPT", "use": "AI 建议元件布局"},
        {"name": "TI WebBench + DeepSeek", "use": "AI 辅助电源方案选型"},
    ]
    for i, a in enumerate(aitools):
        docs.append({
            "id": f"ai_{i:03d}",
            "text": f"AI 工具：{a['name']}。用法：{a['use']}",
            "source": "AI工具",
            "date": "",
            "category": "AI工具",
            "url": "",
            "summary": a['use'],
        })

    print(f"📚 共构建 {len(docs)} 条知识文档")
    return docs


# ============ 向量数据库 ============

def build_vector_db(docs: list[dict]):
    """用 ChromaDB 构建向量知识库"""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        print("❌ 需要安装 chromadb: pip install chromadb sentence-transformers")
        sys.exit(1)

    # 使用本地中文嵌入模型
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5"
    )

    # 删除旧的数据库（如果指定了 --rebuild）
    if args.rebuild and DB_DIR.exists():
        import shutil
        shutil.rmtree(DB_DIR)
        print("🗑️  已删除旧知识库")

    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        collection = client.get_collection("电源知识库")
        if args.rebuild:
            client.delete_collection("电源知识库")
            collection = client.create_collection("电源知识库", embedding_function=ef)
        else:
            print("ℹ️  知识库已存在，追加新数据（用 --rebuild 重建）")
    except:
        collection = client.create_collection("电源知识库", embedding_function=ef)

    # 分批添加（ChromaDB 每次最多 100 条）
    batch_size = 100
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i+batch_size]
        try:
            collection.add(
                ids=[d["id"] for d in batch],
                documents=[d["text"] for d in batch],
                metadatas=[{
                    "source": d["source"],
                    "date": d["date"],
                    "category": d["category"],
                    "url": d["url"],
                } for d in batch],
            )
        except Exception as e:
            # 可能是 ID 重复，跳过已存在的
            print(f"  ⚠️  部分文档跳过: {e}")

    count = collection.count()
    print(f"✅ 知识库构建完成！共 {count} 条向量")
    return collection


# ============ 查询 ============

def query(question: str, top_k: int = 5):
    """查询知识库"""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        print("❌ 需要安装 chromadb: pip install chromadb sentence-transformers")
        sys.exit(1)

    if not DB_DIR.exists():
        print("❌ 知识库不存在，请先运行: python build_knowledge.py")
        sys.exit(1)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5"
    )
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection("电源知识库", embedding_function=ef)

    results = collection.query(
        query_texts=[question],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\n🔍 问题: {question}")
    print(f"{'='*60}")
    print(f"📚 找到 {len(results['documents'][0])} 条相关内容:\n")

    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0],
    )):
        score = 1 - dist  # 相似度得分
        src = meta.get('source', '')
        date = meta.get('date', '')
        cat = meta.get('category', '')
        url = meta.get('url', '')
        print(f"  [{i+1}] (相似度: {score:.2f})")
        print(f"      来源: {src} | 分类: {cat} | 日期: {date}")
        print(f"      内容: {doc[:200]}...")
        if url:
            print(f"      链接: {url}")
        print()

    # 拼接上下文，方便发给 LLM
    context = "\n".join([
        f"- [{m.get('source','')}] {d}"
        for d, m in zip(results['documents'][0], results['metadatas'][0])
    ])
    print(f"{'='*60}")
    print(f"📋 上下文（可直接发给 AI）:\n\n{context}")

    return context


# ============ CLI ============

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🧠 电源知识库 RAG 系统")
    parser.add_argument("--query", "-q", help="查询问题")
    parser.add_argument("--rebuild", action="store_true", help="强制重建知识库")
    parser.add_argument("--topk", type=int, default=5, help="返回结果数")
    args = parser.parse_args()

    if args.query:
        query(args.query, args.topk)
    else:
        data = load_data()
        docs = build_documents(data)
        build_vector_db(docs)
