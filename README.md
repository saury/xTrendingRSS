# X (Twitter) Trending RSS Feed

自动生成每日 X (Twitter) 热门话题的 RSS 订阅源，**每天一篇精美的摘要文章**。

## ✨ 特色功能

- 📊 **每日摘要** - 所有 trending 整合到一篇文章
- 🗂️ **分类整理** - 按类别自动分组（AI·News, Politics, Sports 等）
- 📈 **趋势追踪** - 保留 7 天历史
- 🔔 **通知友好** - 每天 1 篇文章，而非 20 条推送
- ⚡ **自动更新** - GitHub Actions 每天 UTC 00:00 运行

## 📱 使用效果

**RSS 阅读器中每天收到 1 篇文章：**
```
🆕 X Trending Topics - 2026-01-31 (20 topics)

📂 AI · News (3 topics)
1. Moltbook Draws 147,000 AI Agents...
   62,000 posts • Updated: 1 day ago

📂 Politics · Trending (7 topics)
1. Gaza
2. Britain
...
```

## 🚀 快速开始

### 1️⃣ 部署到 GitHub

**Fork 或创建仓库：**
```bash
git clone https://github.com/YOUR_USERNAME/xTrendingRSS.git
cd xTrendingRSS
```

**配置 GitHub Secrets：**
- 进入仓库 `Settings` → `Secrets and variables` → `Actions`
- 添加两个 secrets：
  - `TWITTER_AUTH_TOKEN` - 你的 X auth_token cookie
  - `TWITTER_CT0` - 你的 X ct0 cookie

**获取 Cookies 方法：**
1. 浏览器登录 X (Twitter)
2. 打开开发者工具 (F12) → `Application` → `Cookies` → `https://x.com`
3. 复制 `auth_token` 和 `ct0` 的值

**启用 GitHub Actions：**
- 进入 `Actions` 标签页 → 启用 workflows
- 每天 UTC 00:00 自动运行

### 2️⃣ 订阅 RSS

订阅地址：
```
https://raw.githubusercontent.com/YOUR_USERNAME/xTrendingRSS/main/trending.xml
```

推荐阅读器：Reeder, NetNewsWire, Feedly, Inoreader

## 🔧 本地开发

### 前置要求
- Python 3.9+
- Node.js 22+ (bird CLI 要求)

### 安装运行
```bash
# 1. 安装依赖
pip install -r requirements.txt
npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 TWITTER_AUTH_TOKEN 和 TWITTER_CT0

# 3. 运行
python fetch_trending.py
```

生成文件：
- `trending.xml` - RSS feed
- `trending_history.json` - 7 天历史记录

## ⚙️ 配置

### 环境变量 (.env)
```bash
TRENDING_COUNT=20        # 抓取数量
OUTPUT_FILE=trending.xml # RSS 文件名
```

### 代码配置 (fetch_trending.py)
```python
HISTORY_DAYS = 7  # 历史保留天数
```

## 📊 技术实现

**技术栈：**
- **Python 3.9+** - 主程序
- **feedgen** - RSS 2.0 生成
- **bird CLI** - X (Twitter) GraphQL 数据抓取
- **GitHub Actions** - 自动化调度

**RSS 文章结构：**
- **标题**: `X Trending Topics - YYYY-MM-DD`
- **GUID**: `x-trending-digest-YYYY-MM-DD`
- **内容**: 分类整理的 HTML 格式摘要
- **历史**: 保留 7 天，自动清理旧数据

**工作流程：**
1. bird CLI 获取 trending → JSON
2. 按类别整理话题 → HTML 摘要
3. feedgen 生成 RSS → trending.xml
4. GitHub Actions 自动提交

## 📁 项目文件

```
xTrendingRSS/
├── fetch_trending.py      # 主程序
├── requirements.txt       # Python 依赖
├── package.json          # Node.js 依赖 (bird CLI)
├── .env.example          # 环境变量模板
├── .github/workflows/
│   └── update-rss.yml    # GitHub Actions 配置
├── trending.xml          # RSS feed (自动生成)
└── trending_history.json # 历史记录 (自动生成)
```

## ⚠️ 注意事项

**Cookie 安全：**
- ✅ `.env` 已在 `.gitignore` 中
- ⚠️ 绝不要提交 cookies 到公开仓库
- 🔐 使用 GitHub Secrets 存储
- 🔄 Cookies 可能过期，需定期更新

**使用限制：**
- 每天运行 1 次（避免速率限制）
- 需要 Node.js 22+ (bird 0.8.0+ 要求)
- Trending 数据实时变化

## 🤝 贡献 & License

欢迎提交 Issues 和 Pull Requests！

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- [bird](https://github.com/steipete/bird) - X CLI 工具
- [feedgen](https://github.com/lkiesow/python-feedgen) - RSS 生成库

---

**⭐ 如果有帮助，请给个 Star！**
