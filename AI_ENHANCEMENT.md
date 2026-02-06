# AI Enhancement - Technical Details

## 技术实现

### 模型选择
- **模型**: 智谱 AI GLM-4-Flash
- **等效**: OpenCode 的 `opencode/glm-4.7-free`（相同底层模型）
- **调用方式**: 智谱 AI Python SDK (`zhipuai`)
- **成本**: 完全免费

### 为什么不直接使用 OpenCode CLI？
OpenCode CLI 适合交互式使用，但在自动化脚本中集成复杂：
- `opencode run` 启动交互式会话，难以捕获输出
- 需要额外的进程管理和超时控制
- 直接使用智谱 SDK 更简单、稳定

**结论**: 使用 OpenCode 推荐的免费模型（GLM-4），通过官方 SDK 调用。

---

## 工作流程

```
1. fetch_trending.py 获取 X Trending 数据
   ↓
2. 对每条数据调用 enhance_with_ai()
   ↓
3. 智谱 SDK → GLM-4-Flash API
   ↓
4. 生成 40-60 字中文摘要
   ↓
5. 添加到 topic['ai_summary_zh']
   ↓
6. create_digest_html() 渲染 HTML
   ↓
7. 输出到 RSS feed（trending.xml）
```

---

## 性能考虑

### 并发控制
- **串行处理**: 逐条调用 API（避免限流）
- **超时设置**: 每次调用最多 15 秒
- **错误隔离**: 单条失败不影响其他条目

### 处理时间
- 每条 trending: 1-3 秒
- 20 条总计: 30-60 秒
- 如需加速: 减少 `TRENDING_COUNT` 或禁用 AI 功能

---

## 故障排查

### 问题：`ModuleNotFoundError: No module named 'zhipuai'`
**解决**: 
```bash
pip install zhipuai
```

### 问题：AI 摘要为空
**可能原因**:
1. API Key 未设置或无效
2. API 配额用尽
3. 网络连接问题

**检查步骤**:
```bash
# 1. 验证 API Key 已设置
echo $ZHIPUAI_API_KEY

# 2. 手动测试 AI 功能
python3 -c "
from fetch_trending import enhance_with_ai
topic = {'headline': 'Bitcoin Price Surge', 'category': 'Business'}
print(enhance_with_ai(topic))
"

# 3. 查看智谱控制台配额
# 访问 https://open.bigmodel.cn/usercenter/apikeys
```

### 问题：AI 调用超时
**正常现象**: 网络波动或 API 响应慢时会超时，程序会自动跳过该条目。

**如果频繁超时**:
1. 检查网络连接
2. 尝试更换网络环境
3. 临时禁用 AI 功能（不设置 `ZHIPUAI_API_KEY`）

---

## 自定义配置

### 修改 AI 提示词
编辑 `fetch_trending.py` 第 67-75 行：

```python
prompt = f"""请为以下 X (Twitter) 热门话题生成一段简短的中文描述（40-60字）...

{context}

要求：直接输出中文描述，不要其他说明。"""
```

可自定义：
- 输出语言（英文、日文等）
- 描述长度（20-80 字）
- 描述风格（严肃、幽默等）

### 禁用 AI 功能
三种方式：
1. **不安装** `zhipuai` 库
2. **不设置** `ZHIPUAI_API_KEY` 环境变量
3. **代码禁用**: 修改 `fetch_trending.py` 第 449 行：
   ```python
   trending_data = get_trending_data(auth_token, ct0, trending_count, enable_ai=False)
   ```

---

## 与 OpenCode 的关系

此实现使用的 GLM-4-Flash 模型与 OpenCode 的 `opencode/glm-4.7-free` **完全等效**：

| 对比项 | OpenCode CLI | 本实现 |
|--------|-------------|--------|
| 底层模型 | 智谱 GLM-4 | 智谱 GLM-4 |
| API 提供方 | 智谱 AI | 智谱 AI |
| 调用方式 | opencode run -m ... | 智谱 Python SDK |
| 成本 | 免费 | 免费 |
| 集成复杂度 | 高（CLI 交互） | 低（直接 API） |

**结论**: 功能完全相同，只是选择了更适合自动化脚本的集成方式。

---

## 许可证

遵循项目主许可证（MIT License）
