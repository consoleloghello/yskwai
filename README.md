# 综合题库 — 网页版

基于 `题库.txt` 生成的可交互单页题库网页，支持浏览、练习、模拟考试三种模式。

在线浏览地址：<https://consoleloghello.github.io/yskwai/>

## 文件说明

| 文件 | 说明 |
|------|------|
| `题库.txt` | 原始题库（**手动编辑此文件**） |
| `rebuild.py` | 一键重新生成脚本 |
| `index.html` | 生成的网页（浏览器直接打开） |
| `题库.json` | 中间数据（由 rebuild.py 自动生成） |
| `deploy.ps1` | 部署到 GitHub Pages 的脚本 |
| `deploy.conf` | 部署配置文件 |
| `PROJECT_PLAN.md` | 项目需求文档 |

## 修改题库 & 重新生成

1. 用文本编辑器修改 `题库.txt`（保持原有格式结构）
2. 运行:
```
python rebuild.py
```
3. 浏览器打开 `index.html` 确认效果

## 题库格式

`题库.txt` 的格式要求：

```
板块名（独立一行）
选择题
1.	题目内容（A. 正确答案）。          ← 答案填在括号里
2.	另一道题（B. 答案）。              ← 括号前是题目，括号内是答案
填空题
1.	题目包含（答案1）和（答案2）。      ← 多个空用多个括号
判断题
1.	判断题描述（√）                    ← √ 或 × 在括号里
简答题
1.	题目描述。答案全文内容。            ← 句号分隔题目和答案
```

**关键规则**：
- 板块名必须与 `rebuild.py` 中 `SECTIONS` 列表一致（如需增删板块，同步修改脚本）
- 题型名固定为：选择题、填空题、判断题、简答题
- 选择题的答案括号内必须包含字母（A-D）
- 判断题括号内必须是 √ 或 ×

## 部署到 GitHub Pages

**首次部署**：
1. 在 GitHub 创建新仓库（如 `ysk-tiku`）
2. 修改 `deploy.conf`，填入你的仓库地址:
```
REMOTE=git@github.com:你的用户名/仓库名.git
BRANCH=master
```
3. 推送:
```powershell
powershell -ExecutionPolicy Bypass -File .\deploy.ps1
```
4. 在 GitHub 仓库 → Settings → Pages → Source 选 `master` 分支 → Save
5. 等待 1-2 分钟，访问 `git@github.com:你的用户名/仓库名.git/`

**后续更新**：修改 `题库.txt` → `python rebuild.py` → 运行 `deploy.ps1` 即可。

> 如果用 HTTPS 地址：`REMOTE=https://github.com/用户名/仓库名.git`（推送时需输入用户名和个人访问令牌）

## 功能说明

- **浏览模式**：所有答案直接可见，适合背诵
- **练习模式**：点击「显示答案」查看、判断题点 ✓/✗ 判断对错
- **考试模式**：随机抽题（最多 20 题）、限时 30 分钟、自动评分
- **搜索**：顶部搜索框可搜索题目或答案关键词
- **筛选**：上方 Tab 可按板块和题型筛选

## 依赖

- Python 3.6+
- Git
- 浏览器（Chrome / Edge / Safari / Firefox 均可）
