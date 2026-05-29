#!/usr/bin/env node
/**
 * query_knowledge.js — 🔍 知识库查询工具（Node.js 版，免安装）
 *
 * 直接基于 data.json 做关键词搜索，不需要装任何依赖。
 * 更精确的语义搜索用 Python 版 (build_knowledge.py)。
 *
 * 用法:
 *   node query_knowledge.js "LLC 谐振"
 *   node query_knowledge.js "电赛 准备" --top 10
 *   node query_knowledge.js "GaN" --json
 */

const fs = require('fs');
const path = require('path');

const DATA_PATH = path.join(__dirname, 'data.json');

function loadData() {
  return JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8'));
}

// ============ 文档构建 ============
function buildDocs(data) {
  const docs = [];

  // 论文
  (data.memories || []).forEach((m, i) => {
    docs.push({
      id: `paper_${i}`,
      text: `论文：${m.title || ''}。摘要：${m.summary || ''}`,
      source: '论文', date: m.time || '',
      url: m.url || '', category: '论文',
      score: 0,
    });
  });

  // 网站
  (data.cronTasks || []).forEach((t, i) => {
    docs.push({
      id: `web_${i}`,
      text: `网站：${t.name}。说明：${t.lastRun}`,
      source: '网站', date: '', url: t.url || '',
      category: '网站', score: 0,
    });
  });

  // 开源项目
  (data.watchlist || []).forEach((w, i) => {
    docs.push({
      id: `oss_${i}`,
      text: `开源：${w.ticker}。特性：${w.price}。方向：${w.trigger}。推荐：${w.direction}`,
      source: '开源', date: '', url: w.url || '',
      category: '开源', score: 0,
    });
  });

  // 日志
  (data.logs || []).forEach(day => {
    (day.entries || []).forEach((e, j) => {
      docs.push({
        id: `log_${day.date}_${j}`,
        text: `[${day.date} ${e.time}] ${e.action}`,
        source: '日志', date: day.date,
        url: '', category: e.tag || '',
        score: 0,
      });
    });
  });

  // 比赛
  const comps = [
    '电赛电源组 8月 报名7月 Buck/Boost拓扑',
    'TI杯电源设计赛 9月 报名8月 TI芯片选型',
    '中国电源学会竞赛 10月 截止9月 论文方向',
    '集成电路双创赛 7月 报名6月 尽快报名',
  ];
  comps.forEach((c, i) => docs.push({
    id: `comp_${i}`, text: `比赛：${c}`,
    source: '比赛', date: '', url: '',
    category: '比赛', score: 0,
  }));

  return docs;
}

// ============ 关键词搜索 ============
function search(docs, query, topK = 5) {
  const keywords = query.toLowerCase().split(/\s+/);

  docs.forEach(d => {
    const text = d.text.toLowerCase();
    // 计算关键词匹配次数
    let score = 0;
    keywords.forEach(kw => {
      const re = new RegExp(kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      const matches = text.match(re);
      if (matches) score += matches.length * 2;
    });
    // 标题/类别额外加分
    if (d.category && keywords.some(k => d.category.includes(k))) score += 3;
    if (d.source && keywords.some(k => d.source.includes(k))) score += 2;
    d.score = score;
  });

  return docs
    .filter(d => d.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

// ============ CLI ============
const args = process.argv.slice(2);
const queryStr = args.filter(a => !a.startsWith('--')).join(' ');
const topKIdx = args.indexOf('--top');
const topK = topKIdx >= 0 ? parseInt(args[topKIdx + 1]) || 5 : 5;
const asJson = args.includes('--json');

if (!queryStr) {
  console.log('用法: node query_knowledge.js "搜索词" [--top 10] [--json]');
  console.log('示例:');
  console.log('  node query_knowledge.js "LLC 谐振"');
  console.log('  node query_knowledge.js "电赛 准备" --top 10');
  console.log('  node query_knowledge.js "GaN" --json');
  process.exit(0);
}

const data = loadData();
const docs = buildDocs(data);
const results = search(docs, queryStr, topK);

if (asJson) {
  console.log(JSON.stringify(results, null, 2));
  process.exit(0);
}

console.log(`\n🔍 搜索: "${queryStr}"`);
console.log(`📚 找到 ${results.length} 条结果:\n`);
results.forEach((r, i) => {
  console.log(`  [${i+1}] (${r.source}) ${r.category ? '['+r.category+']' : ''}`);
  if (r.date) console.log(`       日期: ${r.date}`);
  console.log(`       ${r.text.slice(0, 150)}`);
  if (r.url) console.log(`       🔗 ${r.url}`);
  console.log();
});

// 输出上下文
console.log('='.repeat(50));
console.log('📋 上下文（发给 AI）:\n');
results.forEach(r => console.log(`- [${r.source}] ${r.text}`));
