# X (Twitter) Trending RSS Feed

自动生成每日 X (Twitter) 热门话题的 RSS 订阅源。

## 功能

- 每天自动抓取 X 的热门话题（AI精选内容）
- 生成 RSS 2.0 格式的订阅源
- 通过 GitHub Actions 自动运行
- 使用 [bird](https://github.com/steipete/bird) CLI 工具获取数据

## 使用方法

### 📡 订阅 RSS

订阅地址：`https://raw.githubusercontent.com/YOUR_USERNAME/xTrendingRSS/main/trending.xml`

将 `YOUR_USERNAME` 替换为你的 GitHub 用户名。

### 🏃 本地运行

1. **克隆仓库**：
```bash
git clone https://github.com/YOUR_USERNAME/xTrendingRSS.git
cd xTrendingRSS
```

2. **安装 Python 依赖**：
```bash
pip install -r requirements.txt
```

3. **安装 Node.js 依赖** (需要 Node.js 22+)：
```bash
npm install
```

4. **配置环境变量**：

复制 `.env.example` 为 `.env` 并填入你的 Twitter cookies：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```
TWITTER_AUTH_TOKEN=your_auth_token_here
TWITTER_CT0=your_ct0_token_here
```

**如何获取 Twitter Cookies：**
1. 在浏览器中登录 X (Twitter)
2. 打开开发者工具 (F12)
3. 进入 Application/存储 → Cookies → https://x.com
4. 找到并复制 `auth_token` 和 `ct0` 的值

5. **运行脚本**：
```bash
python fetch_trending.py
```

生成的 RSS 文件将保存为 `trending.xml`。

### ⚙️ GitHub Actions 设置

1. **Fork 此仓库** 到你的 GitHub 账号

2. **添加 Secrets**：
   - 进入你的仓库设置 → Secrets and variables → Actions
   - 添加以下 secrets：
     - `TWITTER_AUTH_TOKEN`: 你的 Twitter auth_token cookie
     - `TWITTER_CT0`: 你的 Twitter ct0 cookie

3. **启用 GitHub Actions**：
   - 进入 Actions 标签页
   - 如果看到提示，点击启用 workflows

4. **完成！**

GitHub Actions 会：
- 每天 UTC 00:00 (北京时间 08:00) 自动运行
- 抓取最新的热门话题
- 更新 `trending.xml` 文件
- 提交更改到仓库

你也可以在 Actions 标签页手动触发运行。

## 📝 配置选项

在 `.env` 文件中可配置：

```bash
# 抓取的热门话题数量 (默认: 20)
TRENDING_COUNT=20

# RSS 输出文件名 (默认: trending.xml)
OUTPUT_FILE=trending.xml
```

## 🔧 技术栈

- **Python 3.9+**: 主要脚本语言
- **feedgen**: RSS feed 生成库
- **bird CLI**: X (Twitter) 数据抓取工具
- **GitHub Actions**: 自动化定时任务

## 📄 RSS Feed 格式

生成的 RSS feed 包含以下信息：
- 热门话题标题
- 话题分类 (如 AI · Technology, Sports 等)
- 帖子数量
- 更新时间
- 话题链接

## ⚠️ 注意事项

1. **Cookie 有效期**：Twitter cookies 可能会过期，需要定期更新 GitHub Secrets
2. **速率限制**：X 可能会对频繁请求进行限制，建议不要过于频繁地运行脚本
3. **隐私安全**：不要将 cookies 提交到公开仓库，务必使用 GitHub Secrets
4. **Node.js 版本**：bird 0.8.0+ 需要 Node.js 22 或更高版本

## 🤝 贡献

欢迎提交 Issues 和 Pull Requests！

## 📜 License

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [bird](https://github.com/steipete/bird) - 优秀的 X CLI 工具
- [feedgen](https://github.com/lkiesow/python-feedgen) - Python RSS 生成库
