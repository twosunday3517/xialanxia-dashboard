# 🦞 小龙虾 Dashboard

实时监控面板，纯静态 HTML，通过 GitHub Pages 部署。

## 🔗 访问地址

**[https://twosunday3517.github.io/xialanxia-dashboard/dashboard.html](https://twosunday3517.github.io/xialanxia-dashboard/dashboard.html)**

## 📊 模块

| 模块 | 说明 |
|------|------|
| 📊 持仓概览 | 三账户市值、盈亏、持仓数、现金 |
| 📋 Cron 任务状态 | 哪些在跑、哪些 error |
| 🔍 Watchlist 信号 | 接近触发价的标的（距离%标注） |
| 🧠 记忆快照 | 最近记忆事件 |
| 📡 API 状态 | 各 API 是否可用 |

## 🔄 自动更新

在自动化脚本末尾加一行：

```python
subprocess.run(["bash", "dashboard/push_dashboard.sh"])
```

数据保存后自动：更新 HTML → 推送 GitHub Pages → 页面刷新。
