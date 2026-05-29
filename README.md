# 📡 电子信息工程 Dashboard

学业/实验/竞赛一站式监控面板，纯静态 HTML，通过 GitHub Pages 部署。

## 🔗 访问地址

**[https://twosunday3517.github.io/xialanxia-dashboard/dashboard.html](https://twosunday3517.github.io/xialanxia-dashboard/dashboard.html)**

## 📊 模块

| 模块 | 说明 |
|------|------|
| 📊 学业概览 | GPA、已修学分、课程成绩 |
| 📋 实验/项目进度 | 实验任务、竞赛进度、作业状态 |
| ⚠️ 竞赛/证书倒计时 | 电赛、四六级、考研、实习截止 |
| 🧠 知识库快照 | 模电/数电/嵌入式/信号处理笔记 |
| 💻 开发环境状态 | MATLAB/Keil/Altium/Vivado 工具链 |

## 🔄 自动更新

在自动化脚本末尾加一行：

```python
subprocess.run(["bash", "dashboard/push_dashboard.sh"])
```

数据保存后自动：更新 HTML → 推送 GitHub Pages → 页面刷新。
