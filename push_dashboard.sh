#!/bin/bash
# push_dashboard.sh — 更新 Dashboard 并推送到 GitHub Pages
# 在 portfolio_scanner.py 等脚本末尾调用:
#   subprocess.run(["bash", "/path/to/push_dashboard.sh"])
#
# 首次使用前需配置:
#   git remote add origin https://github.com/YOUR_USERNAME/xialanxia-dashboard.git
#   git checkout -b gh-pages

DASHBOARD_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$DASHBOARD_DIR" || { echo "❌ 无法进入目录 $DASHBOARD_DIR"; exit 1; }

# 如果 Python 脚本存在，先更新数据
if [ -f "update_dashboard.py" ]; then
    echo "📝 执行 update_dashboard.py..."
    python3 update_dashboard.py 2>/dev/null || python update_dashboard.py 2>/dev/null || echo "⚠️  Python 更新跳过"
fi

# Git 提交推送
echo "📤 提交到 Git..."
git add -A

# 检查是否有变更
git diff --cached --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo "ℹ️  无变更，跳过 commit"
else
    git commit -m "📊 Dashboard update $(date '+%Y-%m-%d %H:%M')"
    git push origin gh-pages 2>&1 || git push origin main 2>&1
    echo "✅ 推送完成"
fi

# 输出访问地址（替换为你的实际 GitHub 用户名）
echo "🔗 https://YOUR_USERNAME.github.io/xialanxia-dashboard/"
