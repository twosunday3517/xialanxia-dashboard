#!/bin/bash
# push_dashboard.sh — 🦞 更新 Dashboard → 推送到 GitHub Pages
# 在 portfolio_scanner.py 末尾调用:
#   subprocess.run(["bash", "dashboard/push_dashboard.sh"])

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

echo "📝 从 data.json 更新 HTML..."
node update_dashboard.js --data data.json 2>/dev/null

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
