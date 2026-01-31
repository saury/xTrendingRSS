# RSS 订阅行为说明

## 📱 在 RSS 阅读器中的表现

### ✅ 改进后的行为（当前版本）

使用 Reeder 或其他 RSS 阅读器订阅后：

**第一天（首次运行）：**
- 显示 20 条"新文章"（当天的所有 trending）
- 每个 trending 话题都是一条独立的文章

**第二天：**
- 假设有 15 个 trending 与昨天重复，5 个是新的
- RSS 阅读器只显示 **5 条新文章**（新出现的 trending）
- 之前的 15 个 trending 不会重复显示为"新文章"

**第三天：**
- 继续只显示真正新出现的 trending 话题
- RSS feed 中会保留最近 3 天的所有 trending（可以查看历史）

### 🔑 关键特性

1. **独立文章**：每个 trending 话题都是一条独立的 RSS 文章
2. **去重机制**：已经出现过的 trending 不会重复推送
3. **时间戳追踪**：每个 trending 的发布时间是它首次出现的时间
4. **历史保留**：保留 3 天内的 trending，可以看到变化趋势

### 📊 实现原理

#### 数据结构

**trending_history.json** 文件记录每个 trending 的首次出现时间：
```json
{
  "twitter://trending/123456": "2026-01-31T09:36:02+00:00",
  "twitter://trending/789012": "2026-01-31T15:20:45+00:00"
}
```

#### RSS Feed 生成逻辑

1. **抓取新数据**：从 X 获取当前 20 个 trending
2. **对比历史**：检查 `trending_history.json`
3. **标记新旧**：
   - 已存在 → 使用历史时间戳（不会被视为新文章）
   - 首次出现 → 使用当前时间戳（RSS 阅读器显示为新）
4. **生成 RSS**：所有条目都包含在 feed 中，但只有新条目的 `<pubDate>` 是最新的
5. **清理历史**：删除 3 天前的记录

#### RSS 阅读器识别逻辑

RSS 阅读器（如 Reeder）通过两个字段判断文章是否已读：

1. **`<guid>`**：唯一标识符
   - 格式：`x-trending-{trending_id}`
   - 相同 guid = 同一篇文章

2. **`<pubDate>`**：发布时间
   - 新 trending：当前时间
   - 旧 trending：首次出现时间（不变）

**判断逻辑：**
- 如果 RSS 阅读器之前见过某个 `guid`，不会再次标记为"新"
- 只有从未见过的 `guid` 才显示为新文章

### 🎯 用户体验

**优点：**
- ✅ 不会每天收到重复的 20 条推送
- ✅ 只关注真正新出现的热门话题
- ✅ 可以在 feed 中查看最近 3 天的所有 trending
- ✅ 看到 trending 的演变趋势

**示例场景：**

假设今天的 trending：
- 10 个是昨天就在的（持续热门）
- 5 个是前天的（继续trending）
- 5 个是今天新出现的

RSS 阅读器表现：
- **未读/新文章**：5 条（今天新增的）
- **Feed 总数**：20 条（包含所有当前 trending）
- **已读但可见**：15 条（昨天和前天的，可以查看但不会推送通知）

### ⚙️ 配置参数

可以在代码中调整：

```python
HISTORY_DAYS = 3  # 保留历史天数（默认 3 天）
```

- 增加天数 = 更长的历史记录，更少的"新文章"
- 减少天数 = 更短的历史记录，可能有重复

### 🔧 技术细节

**第一次运行：**
```bash
✓ Fetched 20 trending topics
  → New: 话题 A
  → New: 话题 B
  ...（20 个全是 New）
✓ Found 20 new trending topics
```

**第二次运行：**
```bash
✓ Loaded history with 20 items
✓ Fetched 20 trending topics
  → New: 话题 X（只有这一个是新的）
✓ Found 1 new trending topics
```

**RSS Feed 中的时间戳：**
```xml
<!-- 旧的 trending（昨天首次出现） -->
<item>
  <title>话题 A</title>
  <guid>x-trending-123</guid>
  <pubDate>Thu, 30 Jan 2026 09:00:00 +0000</pubDate>  <!-- 保持不变 -->
</item>

<!-- 新的 trending（今天首次出现） -->
<item>
  <title>话题 X</title>
  <guid>x-trending-789</guid>
  <pubDate>Fri, 31 Jan 2026 09:00:00 +0000</pubDate>  <!-- 最新时间 -->
</item>
```

### ❓ FAQ

**Q: 如果一个话题消失几天后重新 trending，会显示为新文章吗？**
A: 会的。如果超过 3 天（`HISTORY_DAYS`），历史记录会被清理，重新出现时会被视为新话题。

**Q: 为什么不直接只显示新增的 trending？**
A: 保留历史可以让你看到完整的当前 trending 列表，以及哪些话题持续热门。

**Q: 会占用多少存储空间？**
A: `trending_history.json` 文件非常小（< 5KB），GitHub 仓库完全可以承受。

**Q: 如果手动删除 trending_history.json 会怎样？**
A: 下次运行时所有 trending 都会被视为新话题，重新建立历史记录。
