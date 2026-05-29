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
import subprocess
subprocess.run(["bash", "dashboard/push_dashboard.sh"])
```

数据保存后自动：更新 data.json → 生成 HTML → 重建知识库 → 推送 GitHub Pages。

## 🧠 RAG 知识库

把日志、论文、网站、项目、比赛信息建成可检索的知识库。

### 方案 A：关键词搜索（免安装，Node.js）

```bash
node query_knowledge.js "LLC 谐振"        # 搜索相关论文和日志
node query_knowledge.js "电赛 准备" --top 10  # 搜比赛信息
node query_knowledge.js "GaN" --json          # JSON 格式输出
```

### 方案 B：向量语义搜索（需要 Python）

```bash
# 安装依赖（只需一次）
pip install chromadb sentence-transformers

# 构建知识库
python build_knowledge.py

# 查询
python build_knowledge.py --query "LLC 谐振变换器怎么复刻"

# 强制重建
python build_knowledge.py --rebuild
```

每次 `push_dashboard.sh` 会自动重建知识库，保持实时同步。

### 跟 AI 对话

查询结果会输出可直接发给 AI 的**上下文**，复制粘贴到 DeepSeek/Claude 里提问：

```
- [论文] 论文：数字控制 LLC 谐振变换器。摘要：可复刻：STM32F334...
- [日志] [2026-06-02 08:30] 数字控制 LLC 谐振变换器论文精读...
- [网站] 电源网浏览 LLC 谐振变换器文章
```

## 📁 文件结构

| 文件 | 说明 |
|------|------|
| `dashboard.html` | 主页面（侧边栏导航 + Tab 筛选） |
| `data.json` | 所有数据源 |
| `update_dashboard.js` | data.json → HTML 渲染 |
| `push_dashboard.sh` | 一键推送（含知识库重建） |
| `build_knowledge.py` | Python RAG 知识库构建 |
| `query_knowledge.js` | Node.js 关键词搜索 |
