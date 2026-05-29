#!/bin/bash
# push_dashboard.sh — 🦞 更新 Dashboard → 推送到 GitHub Pages
# 在 portfolio_scanner.py 末尾调用:
#   subprocess.run(["bash", "dashboard/push_dashboard.sh"])

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

echo "📝 生成今日日志..."
node -e "
const fs=require('fs');
const p='data.json';
let d=JSON.parse(fs.readFileSync(p,'utf-8'));
const today=new Date().toISOString().slice(0,10);
const now=new Date().toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit',hour12:false});
if(!d.logs) d.logs=[];
const exist=d.logs.find(l=>l.date===today);
if(!exist){
  d.logs.unshift({date:today,entries:[]});
}
const todayLog=d.logs.find(l=>l.date===today);
todayLog.entries.push({time:now,icon:'📤',action:'Dashboard 自动更新推送',tag:'系统'});
fs.writeFileSync(p,JSON.stringify(d,null,2),'utf-8');
console.log('✅ 日志已记录',today,now);
"

echo "📝 从 data.json 更新 HTML..."
node update_dashboard.js --data data.json 2>/dev/null

echo "🧠 重建 RAG 知识库..."
python3 build_knowledge.py 2>/dev/null || python build_knowledge.py 2>/dev/null || echo "⚠️  知识库跳过（需安装 chromadb）"

echo "📤 推送到 GitHub..."
git add -A

git diff --cached --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo "ℹ️  无变更"
    echo "🔗 https://twosunday3517.github.io/xialanxia-dashboard/dashboard.html"
    exit 0
fi

git commit -m "📊 Dashboard $(date '+%Y-%m-%d %H:%M')"
git push origin gh-pages

echo "✅ 推送完成"
echo "🔗 https://twosunday3517.github.io/xialanxia-dashboard/dashboard.html"
