#!/usr/bin/env python3
"""
🦞 小龙虾 Dashboard 更新脚本
用正则替换 HTML 注释标记间的内容，保持模板不变。
调用方式：
  python3 update_dashboard.py                    # 使用内置示例数据
  python3 update_dashboard.py --data data.json   # 从 JSON 文件加载
  python3 update_dashboard.py --push             # 更新后自动 git push
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ============ 路径配置 ============
HERE = Path(__file__).parent
DASHBOARD_HTML = HERE / "dashboard.html"
SCRIPT_DIR = HERE / "scripts"

# ============ 注释标记常量 ============
MARKERS = {
    "stats":      ("STATS_START",      "STATS_END"),
    "positions":  ("POSITIONS_START",  "POSITIONS_END"),
    "cron":       ("CRON_START",       "CRON_END"),
    "watchlist":  ("WATCHLIST_START",  "WATCHLIST_END"),
    "memory":     ("MEMORY_START",     "MEMORY_END"),
    "api":        ("API_START",        "API_END"),
}


def replace_section(html: str, section: str, content: str) -> str:
    """替换 HTML 中两个注释标记之间的内容"""
    start_tag, end_tag = MARKERS[section]
    pattern = rf'<!-- {start_tag} -->.*?<!-- {end_tag} -->'
    replacement = f'<!-- {start_tag} -->\n{content}<!-- {end_tag} -->'
    return re.sub(pattern, replacement, html, flags=re.DOTALL)


# ============ 各模块 HTML 生成器 ============

def render_stats(d: dict) -> str:
    p = d.get("portfolio", {})
    total = p.get("total", 0)
    pnl = p.get("totalPnl", 0)
    cron = d.get("cronTasks", [])
    watch = d.get("watchlist", [])
    ok_tasks = sum(1 for t in cron if t.get("status") == "active")
    pnl_cls = "green" if pnl >= 0 else "red"
    pnl_str = f"+{pnl:.2f}%" if pnl >= 0 else f"{pnl:.2f}%"
    return f"""  <div class="stat-card">
    <div class="value blue">${total:,}</div>
    <div class="label">💰 总资产</div>
  </div>
  <div class="stat-card">
    <div class="value {pnl_cls}">{pnl_str}</div>
    <div class="label">📈 总盈亏</div>
  </div>
  <div class="stat-card">
    <div class="value" style="color:var(--green)">{ok_tasks}/{len(cron)}</div>
    <div class="label">✅ 任务正常</div>
  </div>
  <div class="stat-card">
    <div class="value yellow">{len(watch)}</div>
    <div class="label">🔍 预警信号</div>
  </div>"""


def render_positions(d: dict) -> str:
    accounts = d.get("portfolio", {}).get("accounts", [])
    if not accounts:
        return '    <tr><td colspan="5" class="dim" style="text-align:center;">暂无持仓数据</td></tr>\n'
    rows = ""
    for a in accounts:
        name = a.get("name", "未知")
        value = a.get("value", 0)
        pnl = a.get("pnl", 0)
        pnl_cls = "green" if pnl >= 0 else "red"
        pnl_str = f"+{pnl:.2f}%" if pnl >= 0 else f"{pnl:.2f}%"
        holdings = a.get("holdings", 0)
        cash = a.get("cash", 0)
        rows += f'    <tr><td>{name}</td><td>${value:,}</td><td class="{pnl_cls}">{pnl_str}</td><td>{holdings} 只</td><td class="dim">${cash:,}</td></tr>\n'
    return rows


def render_cron(d: dict) -> str:
    tasks = d.get("cronTasks", [])
    if not tasks:
        return '    <tr><td colspan="5" class="dim" style="text-align:center;">暂无定时任务</td></tr>\n'
    rows = ""
    for t in tasks:
        name = t.get("name", "未知")
        cron = t.get("cron", "--")
        status = t.get("status", "pending")
        last_run = t.get("lastRun", "--")
        cost = t.get("cost", 0)

        if status == "active":
            tag = '<span class="tag active">活跃</span>'
        elif status == "error":
            tag = '<span class="tag error">' + t.get("error", "错误") + '</span>'
        else:
            tag = '<span class="tag pending">待执行</span>'

        cost_str = f"${cost:.3f}" if isinstance(cost, (int, float)) else str(cost)
        rows += f'    <tr><td>{name}</td><td class="mono dim">{cron}</td><td>{tag}</td><td class="dim">{last_run}</td><td class="dim">{cost_str}</td></tr>\n'
    return rows


def render_watchlist(d: dict) -> str:
    items = d.get("watchlist", [])
    if not items:
        return '    <tr><td colspan="5" class="dim" style="text-align:center;">无接近触发价的标的</td></tr>\n'
    rows = ""
    for w in items:
        ticker = w.get("ticker", w.get("symbol", "???"))
        price = w.get("price", w.get("currentPrice", 0))
        trigger = w.get("trigger", w.get("triggerPrice", 0))
        dtype = w.get("type", w.get("direction", "触发"))
        dist = w.get("distance", 0)
        dist_cls = "red" if dist < 0 else "green"
        # 方向图标
        icon = "🔴" if dist < 0 else "🟢"
        # 类型中文
        type_map = {"stop_loss": "止损", "take_profit": "止盈", "breakout": "突破", "pullback": "回调", "down": "止损", "up": "止盈", "trigger": "触发"}
        dlabel = type_map.get(dtype, str(dtype))
        rows += f'    <tr><td class="mono">{icon} {ticker}</td><td class="mono">${price:,.2f}</td><td class="mono dim">${trigger:,.2f}</td><td>{dlabel}</td><td class="{dist_cls}">{dist:+.1f}%</td></tr>\n'
    return rows


def render_memory(d: dict) -> str:
    memories = d.get("memories", [])
    if not memories:
        return '  <div class="memory-item"><div class="title dim" style="text-align:center;">暂无记忆事件</div></div>\n'
    items = ""
    for m in memories:
        time = m.get("time", m.get("date", "--"))
        title = m.get("title", m.get("summary", "")[:40])
        summary = m.get("summary", "")
        items += f"""  <div class="memory-item">
    <div class="time">{time}</div>
    <div class="title">{title}</div>
    <div class="summary">{summary}</div>
  </div>
"""
    return items


def render_api(d: dict) -> str:
    apis = d.get("apis", d.get("apiStatus", []))
    if not apis:
        return '    <tr><td colspan="4" class="dim" style="text-align:center;">暂无 API 数据</td></tr>\n'
    rows = ""
    for a in apis:
        name = a.get("name", "未知")
        icon = a.get("icon", "🔌")
        status = a.get("status", "unknown")
        latency = a.get("latency")
        note = a.get("note", a.get("description", ""))

        if status in ("ok", "available"):
            tag = '<span class="tag active">可用</span>'
        elif status in ("error", "unavailable"):
            tag = '<span class="tag error">不可用</span>'
        elif status in ("limited", "warning", "low"):
            tag = '<span class="tag pending">' + (a.get("note", "受限") or "受限") + '</span>'
        else:
            tag = '<span class="tag pending">未知</span>'

        lat_str = f"{latency}ms" if latency else "--"
        rows += f'    <tr><td>{icon} {name}</td><td>{tag}</td><td class="mono dim">{lat_str}</td><td class="dim">{note}</td></tr>\n'
    return rows


# ============ 渲染器注册表 ============
RENDERERS = {
    "stats":     render_stats,
    "positions": render_positions,
    "cron":      render_cron,
    "watchlist": render_watchlist,
    "memory":    render_memory,
    "api":       render_api,
}


# ============ 主函数 ============

def update_dashboard(data: dict, html_path: Path = None) -> str:
    """更新 HTML 中所有标记区域，返回更新后的 HTML"""
    if html_path is None:
        html_path = DASHBOARD_HTML

    html = html_path.read_text(encoding="utf-8")

    # 更新更新时间
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = re.sub(
        r'(?<=<span id="updateTime">).*?(?=</span>)',
        now, html
    )
    html = re.sub(
        r'(?<=<span id="footerTime">).*?(?=</span>)',
        f"上次更新: {now}", html
    )

    # 替换所有模块
    for section, renderer in RENDERERS.items():
        content = renderer(data)
        html = replace_section(html, section, content)

    return html


def load_data(data_path: str = None) -> dict:
    """从 JSON 文件加载数据，或使用内置示例"""
    if data_path:
        return json.loads(Path(data_path).read_text(encoding="utf-8"))
    return _mock_data()


def _mock_data() -> dict:
    return {
        "portfolio": {
            "total": 148386,
            "totalPnl": -1.08,
            "accounts": [
                {"name": "🏦 大机构",   "value": 37481, "pnl": 6.18,  "holdings": 3, "cash": 13640},
                {"name": "⚡ 激进交易", "value": 56457, "pnl": 26.93, "holdings": 5, "cash": 26026},
                {"name": "🦞 蓝虾交易", "value": 56813, "pnl": -1.00, "holdings": 3, "cash": 39002},
            ]
        },
        "cronTasks": [
            {"name": "🌅 早间情报",      "cron": "0 9 * * *",   "status": "active", "lastRun": "09:00", "cost": 0.024},
            {"name": "🔥 10点深度推送",  "cron": "0 10 * * *",  "status": "active", "lastRun": "10:00", "cost": 0.022},
            {"name": "📊 持仓扫描",      "cron": "0 10 * * *",  "status": "active", "lastRun": "10:00", "cost": 0.020},
            {"name": "💼 ClawWork",      "cron": "0 8 * * *",   "status": "error",  "lastRun": "08:00", "cost": 0.030, "error": "E2B 404"},
            {"name": "🔄 策略扫描",      "cron": "0 */6 * * *", "status": "active", "lastRun": "16:00", "cost": 0.080},
            {"name": "📖 学城日报",      "cron": "47 23 * * *", "status": "pending","lastRun": "--",    "cost": 0.010},
        ],
        "watchlist": [
            {"ticker": "UPXI", "price": 1.26, "trigger": 0.75, "type": "stop_loss",  "distance": -40.5},
            {"ticker": "ROLR", "price": 5.44, "trigger": 3.20, "type": "stop_loss",  "distance": -41.2},
            {"ticker": "CVNA", "price": 315.00, "trigger": 350.00, "type": "take_profit", "distance": +11.1},
            {"ticker": "SOFI", "price": 15.29, "trigger": 16.00, "type": "trigger",   "distance": -4.5},
        ],
        "memories": [
            {"time": "2026-05-29 09:00", "title": "早间情报推送完成",      "summary": "Claude Code Channels · Graph Memory · Replit $4亿 · MCP 漏洞 ×3"},
            {"time": "2026-05-29 10:30", "title": "深度推送 — Sapiom/CZ", "summary": "Sapiom $1500万融资 · CZ 加密支付宣言 · OpenClaw 3.2 Bug"},
            {"time": "2026-05-29 14:00", "title": "深度推送 — OpenAI三合一", "summary": "OpenAI 统一App · Meta 内容审核 Agent · 三星 $730亿 AI芯片"},
            {"time": "2026-05-29 16:05", "title": "三账户持仓扫描",        "summary": "总 $147,724 (-1.52%) · CVNA +8.2% · UPXI ⚠️ -12.1%"},
            {"time": "2026-05-29 19:00", "title": "晚间深度推送",          "summary": "Morgan Stanley MSBT ETF · ORCL Q3 +9.2% · 美股蒸发 $8200亿"},
        ],
        "apis": [
            {"icon": "🤖", "name": "AISA LLM",     "status": "limited",    "latency": 320, "note": "余额 -$0.003"},
            {"icon": "🐦", "name": "AISA Twitter",  "status": "unavailable","latency": None, "note": "余额耗尽"},
            {"icon": "🔍", "name": "Tavily",         "status": "available", "latency": 180, "note": "免费额度内"},
            {"icon": "🏛️", "name": "SEC EDGAR",     "status": "available", "latency": 420, "note": "零成本"},
            {"icon": "📊", "name": "Yahoo Finance",  "status": "available", "latency": 95,  "note": "实时行情"},
            {"icon": "💼", "name": "ClawWork",       "status": "available", "latency": 60,  "note": "余额 $290"},
            {"icon": "🔬", "name": "E2B Sandbox",    "status": "unavailable","latency": None, "note": "模板 404"},
        ]
    }


# ============ 推送辅助 ============

def git_push(repo_dir: str = None):
    """git add + commit + push"""
    cwd = repo_dir or str(HERE)
    msg = f"📊 Dashboard 更新 {__import__('datetime').datetime.now():%Y-%m-%d %H:%M}"
    try:
        subprocess.run(["git", "-C", cwd, "add", "-A"], check=True, capture_output=True)
        r = subprocess.run(["git", "-C", cwd, "diff", "--cached", "--quiet"],
                           capture_output=True)
        if r.returncode == 0:
            print("ℹ️ 无变更，跳过 commit")
            return
        subprocess.run(["git", "-C", cwd, "commit", "-m", msg], check=True, capture_output=True)
        subprocess.run(["git", "-C", cwd, "push", "origin", "gh-pages" if "gh-pages" in subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"], capture_output=True, text=True).stdout else "main"],
            check=True, capture_output=True)
        print(f"✅ 已推送: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作失败: {e.stderr.decode() if e.stderr else e}")


# ============ CLI ============

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="🦞 龙虾 Dashboard 更新")
    parser.add_argument("--data", help="数据 JSON 文件路径")
    parser.add_argument("--output", help="输出 HTML 路径（默认覆盖原文件）")
    parser.add_argument("--push", action="store_true", help="更新后自动 git push")
    args = parser.parse_args()

    data = load_data(args.data)
    html = update_dashboard(data)

    out_path = Path(args.output) if args.output else DASHBOARD_HTML
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Dashboard HTML 已更新 -> {out_path}")

    if args.push:
        git_push(str(out_path.parent))
