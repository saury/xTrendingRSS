# X (Twitter) Trending RSS Feed

自动生成每日 X (Twitter) 热门话题的 RSS 订阅源，**每天一篇精美的摘要文章**。

## ✨ 特色功能

- 📊 **每日摘要** - 所有 trending 整合到一篇文章
- 🤖 **AI 增强** - 使用 OpenCode GLM-4 模型生成中文描述（可选）
- 🗂️ **分类整理** - 按类别自动分组（AI·News, Politics, Sports 等）
- 📈 **趋势追踪** - 保留 7 天历史
- 🔔 **通知友好** - 每天 1 篇文章，而非 20 条推送
- ⚡ **自动更新** - GitHub Actions 每天 UTC 00:00 运行

## 🎯 AI 增强功能（NEW！）

开启 AI 增强后，每条 trending 会附带：
- 🤖 40-60 字的中文摘要
- 突出关键亮点和潜在影响
- 使用 OpenCode 的免费 GLM-4 模型（`opencode/glm-4.7-free`）

**示例效果：**
```
📂 Business · Trending

1. Bitcoin Price Surge
   🤖 AI 摘要：比特币价格突破历史新高，市场情绪高涨，投资者密切关注其对全球金融市场的影响...
   62,000 posts • Updated: 2 hours ago
```

详细配置请查看 [AI_ENHANCEMENT.md](./AI_ENHANCEMENT.md)

## 📱 使用效果

**RSS 阅读器中每天收到 1 篇文章：**
```
🆕 X Trending Topics - 2026-01-31 (20 topics)

📂 AI · News (3 topics)
1. Moltbook Draws 147,000 AI Agents...
   🤖 AI 摘要：Moltbook平台吸引大量AI智能体，展示人工智能应用的爆发式增长趋势...
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
- 添加 secrets：
  - `TWITTER_AUTH_TOKEN` - 你的 X auth_token cookie
  - `TWITTER_CT0` - 你的 X ct0 cookie
  - `ZHIPUAI_API_KEY` - 智谱 AI API Key（可选，用于 AI 增强）

**获取 Cookies 方法：**
1. 浏览器登录 X (Twitter)
2. 打开开发者工具 (F12) → `Application` → `Cookies` → `https://x.com`
3. 复制 `auth_token` 和 `ct0` 的值

**获取智谱 AI API Key（可选）：**
1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册并创建 API Key
3. 添加到 GitHub Secrets（如果不添加，会跳过 AI 增强）

**启用 GitHub Actions：**
- 进入 `Actions` 标签页 → 启用 workflows
- 每天 UTC 00:00 自动运行

**配置 AI 增强（可选）：**

如需启用 AI 生成中文摘要，需添加智谱 AI API Key：

1. **获取 API Key**:
   - 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
   - 注册账号（支持微信/手机号）
   - 控制台创建 API Key（免费额度足够日常使用）

2. **添加到 GitHub Secrets**:
   - `Settings` → `Secrets and variables` → `Actions`
   - 新建 Secret: `ZHIPUAI_API_KEY`
   - 粘贴你的 API Key

**注意**: 不配置 API Key 也能正常运行，只是会跳过 AI 摘要生成。

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
pip install -r requirements.txt  # feedgen, python-dotenv, zhipuai
npm install                      # bird CLI

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入：
#   - TWITTER_AUTH_TOKEN（必需）
#   - TWITTER_CT0（必需）
#   - ZHIPUAI_API_KEY（可选，启用 AI 增强）

# 3. 运行
python fetch_trending.py
```

**预期输出**（启用 AI 时）：
```
============================================================
X Trending RSS Generator (Daily Digest)
============================================================
✓ Loaded history with 7 daily digests
✓ Fetched 20 trending topics
🤖 Generating AI summaries with OpenCode's GLM-4 model...
  [1/20] Processing: Bitcoin Price Surge...
      ✓ 比特币价格突破历史新高，市场情绪高涨...
  [2/20] Processing: AI Regulation News...
      ✓ 各国加强AI监管政策，科技公司面临合规挑战...
✓ Created daily digest for 2026-02-06 with 20 topics
✓ RSS feed generated: trending.xml
============================================================
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
