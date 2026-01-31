# X (Twitter) Trending RSS Feed

自动生成每日 X (Twitter) 热门话题的 RSS 订阅源。

## 功能

- 每天自动抓取 X 的热门话题
- 生成 RSS 2.0 格式的订阅源
- 通过 GitHub Actions 自动运行
- 支持多个地区的热门话题

## 使用方法

### 订阅 RSS

订阅地址：`https://raw.githubusercontent.com/YOUR_USERNAME/xTrendingRSS/main/trending.xml`

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
创建 `.env` 文件并添加你的 Twitter cookies：
```
TWITTER_AUTH_TOKEN=your_auth_token
TWITTER_CT0=your_ct0_token
```

3. 运行脚本：
```bash
python fetch_trending.py
```

### GitHub Actions 设置

1. Fork 此仓库
2. 在仓库设置中添加以下 Secrets：
   - `TWITTER_AUTH_TOKEN`: 你的 Twitter auth_token cookie
   - `TWITTER_CT0`: 你的 Twitter ct0 cookie

GitHub Actions 会每天自动运行并更新 `trending.xml` 文件。

## License

MIT
