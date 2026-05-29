#!/usr/bin/env node
/**
 * update_dashboard.js — 🦞 小龙虾 Dashboard 更新脚本 (Node.js 版)
 * 用法:
 *   node update_dashboard.js                    # 使用内置示例数据
 *   node update_dashboard.js --data data.json   # 从 JSON 加载
 *   node update_dashboard.js --push             # 更新后 git push
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const HERE = __dirname;
const DASHBOARD_HTML = path.join(HERE, 'dashboard.html');

// ============ 注释标记常量 ============
const MARKERS = {
  stats:     ['STATS_START',     'STATS_END'],
  positions: ['POSITIONS_START', 'POSITIONS_END'],
  cron:      ['CRON_START',      'CRON_END'],
  watchlist: ['WATCHLIST_START', 'WATCHLIST_END'],
  memory:    ['MEMORY_START',    'MEMORY_END'],
  api:       ['API_START',       'API_END'],
};

function replaceSection(html, section, content) {
  const [start, end] = MARKERS[section];
  const pattern = new RegExp(
    `<!-- ${start} -->[\\s\\S]*?<!-- ${end} -->`, 'g'
  );
  return html.replace(pattern,
    `<!-- ${start} -->\n${content}<!-- ${end} -->`
  );
}

// ============ HTML 生成器 ============

function renderStats(d) {
  const p = d.portfolio || {};
  const total = p.total || 0;
  const pnl = p.totalPnl || 0;
  const cron = d.cronTasks || [];
  const watch = d.watchlist || [];
  const okTasks = cron.filter(t => t.status === 'active').length;
  const pnlCls = pnl >= 0 ? 'green' : 'red';
  const pnlStr = pnl >= 0 ? `+${pnl.toFixed(2)}%` : `${pnl.toFixed(2)}%`;
  return `  <div class="stat-card">
    <div class="value blue">$${total.toLocaleString()}</div>
    <div class="label">💰 总资产</div>
  </div>
  <div class="stat-card">
    <div class="value ${pnlCls}">${pnlStr}</div>
    <div class="label">📈 总盈亏</div>
  </div>
  <div class="stat-card">
    <div class="value" style="color:var(--green)">${okTasks}/${cron.length}</div>
    <div class="label">✅ 任务正常</div>
  </div>
  <div class="stat-card">
    <div class="value yellow">${watch.length}</div>
    <div class="label">🔍 预警信号</div>
  </div>`;
}

function renderPositions(d) {
  const accts = (d.portfolio && d.portfolio.accounts) || [];
  if (!accts.length) return '    <tr><td colspan="5" class="dim" style="text-align:center;">暂无持仓数据</td></tr>\n';
  return accts.map(a => {
    const pnlCls = a.pnl >= 0 ? 'green' : 'red';
    const pnlStr = a.pnl >= 0 ? `+${a.pnl.toFixed(2)}%` : `${a.pnl.toFixed(2)}%`;
    return `    <tr><td>${a.name}</td><td>$${a.value.toLocaleString()}</td><td class="${pnlCls}">${pnlStr}</td><td>${a.holdings} 只</td><td class="dim">$${a.cash.toLocaleString()}</td></tr>\n`;
  }).join('');
}

function renderCron(d) {
  const tasks = d.cronTasks || [];
  if (!tasks.length) return '    <tr><td colspan="5" class="dim" style="text-align:center;">暂无定时任务</td></tr>\n';
  return tasks.map(t => {
    let tag;
    if (t.status === 'active') tag = '<span class="tag active">活跃</span>';
    else if (t.status === 'error') tag = `<span class="tag error">${t.error || '错误'}</span>`;
    else tag = '<span class="tag pending">待执行</span>';
    const costStr = `$${(t.cost || 0).toFixed(3)}`;
    return `    <tr><td>${t.name}</td><td class="mono dim">${t.cron}</td><td>${tag}</td><td class="dim">${t.lastRun}</td><td class="dim">${costStr}</td></tr>\n`;
  }).join('');
}

function renderWatchlist(d) {
  const items = d.watchlist || [];
  if (!items.length) return '    <tr><td colspan="5" class="dim" style="text-align:center;">无接近触发价的标的</td></tr>\n';
  return items.map(w => {
    const ticker = w.ticker || w.symbol || '???';
    const price = w.price || w.currentPrice || 0;
    const trigger = w.trigger || w.triggerPrice || 0;
    const dType = w.type || w.direction || '触发';
    const dist = w.distance || 0;
    const distCls = dist < 0 ? 'red' : 'green';
    const icon = dist < 0 ? '🔴' : '🟢';
    const typeMap = { stop_loss: '止损', take_profit: '止盈', breakout: '突破', pullback: '回调', down: '止损', up: '止盈', trigger: '触发' };
    const dLabel = typeMap[dType] || dType;
    return `    <tr><td class="mono">${icon} ${ticker}</td><td class="mono">$${Number(price).toFixed(2)}</td><td class="mono dim">$${Number(trigger).toFixed(2)}</td><td>${dLabel}</td><td class="${distCls}">${dist >= 0 ? '+' : ''}${dist.toFixed(1)}%</td></tr>\n`;
  }).join('');
}

function renderMemory(d) {
  const mems = d.memories || [];
  if (!mems.length) return '  <div class="memory-item"><div class="title dim" style="text-align:center;">暂无记忆事件</div></div>\n';
  return mems.map(m => {
    const time = m.time || m.date || '--';
    const title = m.title || (m.summary || '').slice(0, 40);
    const summary = m.summary || '';
    return `  <div class="memory-item">
    <div class="time">${time}</div>
    <div class="title">${title}</div>
    <div class="summary">${summary}</div>
  </div>\n`;
  }).join('');
}

function renderApi(d) {
  const apis = d.apis || d.apiStatus || [];
  if (!apis.length) return '    <tr><td colspan="4" class="dim" style="text-align:center;">暂无 API 数据</td></tr>\n';
  return apis.map(a => {
    let tag;
    if (a.status === 'ok' || a.status === 'available') tag = '<span class="tag active">可用</span>';
    else if (a.status === 'error' || a.status === 'unavailable') tag = '<span class="tag error">不可用</span>';
    else if (a.status === 'limited' || a.status === 'warning') tag = `<span class="tag pending">${a.note || '受限'}</span>`;
    else tag = '<span class="tag pending">未知</span>';
    const latStr = a.latency ? `${a.latency}ms` : '--';
    return `    <tr><td>${a.icon || '🔌'} ${a.name}</td><td>${tag}</td><td class="mono dim">${latStr}</td><td class="dim">${a.note || ''}</td></tr>\n`;
  }).join('');
}

// ============ 渲染器注册表 ============
const RENDERERS = {
  stats:     renderStats,
  positions: renderPositions,
  cron:      renderCron,
  watchlist: renderWatchlist,
  memory:    renderMemory,
  api:       renderApi,
};

// ============ 主函数 ============

function updateDashboard(data, htmlPath) {
  htmlPath = htmlPath || DASHBOARD_HTML;
  let html = fs.readFileSync(htmlPath, 'utf-8');

  // 更新时间
  const now = new Date().toLocaleString('zh-CN', { hour12: false });
  html = html.replace(/(?<=<span id="updateTime">).*?(?=<\/span>)/, now);
  html = html.replace(/(?<=<span id="footerTime">).*?(?=<\/span>)/, `上次更新: ${now}`);

  // 替换所有模块
  for (const [section, renderer] of Object.entries(RENDERERS)) {
    const content = renderer(data);
    html = replaceSection(html, section, content);
  }
  return html;
}

function mockData() {
  return {
    portfolio: {
      total: 148386, totalPnl: -1.08,
      accounts: [
        { name: '🏦 大机构',   value: 37481, pnl: 6.18,  holdings: 3, cash: 13640 },
        { name: '⚡ 激进交易', value: 56457, pnl: 26.93, holdings: 5, cash: 26026 },
        { name: '🦞 蓝虾交易', value: 56813, pnl: -1.00, holdings: 3, cash: 39002 },
      ]
    },
    cronTasks: [
      { name: '🌅 早间情报',     cron: '0 9 * * *',   status: 'active',  lastRun: '09:00', cost: 0.024 },
      { name: '🔥 10点深度推送', cron: '0 10 * * *',  status: 'active',  lastRun: '10:00', cost: 0.022 },
      { name: '📊 持仓扫描',     cron: '0 10 * * *',  status: 'active',  lastRun: '10:00', cost: 0.020 },
      { name: '💼 ClawWork',     cron: '0 8 * * *',   status: 'error',   lastRun: '08:00', cost: 0.030, error: 'E2B 404' },
      { name: '🔄 策略扫描',     cron: '0 */6 * * *', status: 'active',  lastRun: '16:00', cost: 0.080 },
      { name: '📖 学城日报',     cron: '47 23 * * *', status: 'pending', lastRun: '--',    cost: 0.010 },
    ],
    watchlist: [
      { ticker: 'UPXI', price: 1.26,  trigger: 0.75,  type: 'stop_loss',  distance: -40.5 },
      { ticker: 'ROLR', price: 5.44,  trigger: 3.20,  type: 'stop_loss',  distance: -41.2 },
      { ticker: 'CVNA', price: 315.00, trigger: 350.00, type: 'take_profit', distance: 11.1 },
      { ticker: 'SOFI', price: 15.29, trigger: 16.00, type: 'trigger',    distance: -4.5 },
    ],
    memories: [
      { time: '2026-05-29 09:00', title: '早间情报推送完成',        summary: 'Claude Code Channels · Graph Memory · Replit $4亿 · MCP 漏洞 ×3' },
      { time: '2026-05-29 10:30', title: '深度推送 — Sapiom/CZ',   summary: 'Sapiom $1500万融资 · CZ 加密支付宣言 · OpenClaw 3.2 Bug' },
      { time: '2026-05-29 14:00', title: '深度推送 — OpenAI三合一', summary: 'OpenAI 统一App · Meta 内容审核 Agent · 三星 $730亿 AI芯片' },
      { time: '2026-05-29 16:05', title: '三账户持仓扫描',          summary: '总 $147,724 (-1.52%) · CVNA +8.2% · UPXI ⚠️ -12.1%' },
      { time: '2026-05-29 19:00', title: '晚间深度推送',            summary: 'Morgan Stanley MSBT ETF · ORCL Q3 +9.2% · 美股蒸发 $8200亿' },
    ],
    apis: [
      { icon: '🤖', name: 'AISA LLM',     status: 'limited',     latency: 320, note: '余额 -$0.003' },
      { icon: '🐦', name: 'AISA Twitter',  status: 'unavailable', latency: null, note: '余额耗尽' },
      { icon: '🔍', name: 'Tavily',         status: 'available',  latency: 180, note: '免费额度内' },
      { icon: '🏛️', name: 'SEC EDGAR',     status: 'available',  latency: 420, note: '零成本' },
      { icon: '📊', name: 'Yahoo Finance',  status: 'available',  latency: 95,  note: '实时行情' },
      { icon: '💼', name: 'ClawWork',       status: 'available',  latency: 60,  note: '余额 $290' },
      { icon: '🔬', name: 'E2B Sandbox',    status: 'unavailable', latency: null, note: '模板 404' },
    ]
  };
}

// ============ CLI ============
const args = process.argv.slice(2);
let dataPath = null;
let outPath = null;
let doPush = false;

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--data' && i + 1 < args.length) dataPath = args[++i];
  else if (args[i] === '--output' && i + 1 < args.length) outPath = args[++i];
  else if (args[i] === '--push') doPush = true;
}

let data;
if (dataPath) {
  data = JSON.parse(fs.readFileSync(path.resolve(dataPath), 'utf-8'));
} else {
  data = mockData();
}

const html = updateDashboard(data);
const dest = outPath || DASHBOARD_HTML;
fs.writeFileSync(dest, html, 'utf-8');
console.log(`✅ Dashboard HTML 已更新 -> ${dest}`);

if (doPush) {
  const cwd = path.dirname(dest);
  try {
    execSync('git add -A', { cwd });
    try { execSync('git diff --cached --quiet', { cwd, stdio: 'pipe' }); }
    catch (e) {
      const msg = `📊 Dashboard update ${new Date().toISOString().slice(0, 16)}`;
      execSync(`git commit -m "${msg}"`, { cwd });
      execSync('git push', { cwd });
      console.log('✅ 已推送');
    }
  } catch (e) {
    console.error('❌ Git 操作失败:', e.message);
  }
}
