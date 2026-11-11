# 反模式：平台识别错误

## 症状（Symptom）

小红书 URL 被当作通用网页处理，没有调用 CDP 和 OCR，导致图文帖子只提取到标题，正文和图片全丢。

用户看到的现象：
- 剪藏文件只有标题 "周末vlog"
- 没有图片
- 没有正文内容
- frontmatter 中 `source` 字段为空或错误

## 反模式（Anti-Pattern）

URL 中包含 `xiaohongshu.com`，但 AI 没有识别到是小红书平台，直接走了 Layer 1 直取策略。

错误行为链：
1. 收到 URL：`https://www.xiaohongshu.com/explore/6658a1234567890`
2. 没有匹配到平台策略表
3. fallback 到通用网页处理
4. 调用 `web_reader` 直取
5. 只拿到 HTML title，正文在 JS 渲染的 DOM 中
6. 保存空内容

正确行为链：
1. 收到 URL：`https://www.xiaohongshu.com/explore/6658a1234567890`
2. 正则匹配 `xiaohongshu.com` → 识别为小红书
3. 加载 `strategies/platform-xhs.md`
4. 用 CDP 打开页面
5. 检测内容类型（图文/视频）
6. OCR 提取图片文字
7. 保存完整内容

## 示例 Prompt

### Case 1：标准小红书帖子
```
输入：剪藏 https://www.xiaohongshu.com/explore/6658a1234567890

错误行为：
- 调用 web_reader → 只拿到标题
- 没有调用 CDP
- 没有 OCR

正确行为：
- 识别到 xiaohongshu.com → 加载 platform-xhs.md
- CDP 打开
- OCR 提取图片文字
```

### Case 2：小红书短链接
```
输入：保存 https://xhslink.com/abc123

错误行为：
- 不认识 xhslink.com
- 直接报错"无法解析"

正确行为：
- 识别 xhslink.com 为小红书短链接
- CDP 打开获取重定向 URL
- 继续平台策略流程
```

### Case 3：小红书用户主页
```
输入：提取 https://www.xiaohongshu.com/user/profile/xxx

错误行为：
- 尝试提取用户主页（没有正文内容）
- 保存空文件

正确行为：
- 识别为用户主页
- 询问用户"要剪藏这个用户的哪篇帖子？"
```

## 为什么失败（Why It Fails）

### 根因分析

1. **URL 正则不完整**
   - 只匹配了 `xiaohongshu.com/explore/`，没匹配 `/user/profile/`
   - 没有匹配子域名变体（如 `www.xiaohongshu.com`）

2. **短链接域名未注册**
   - `xhslink.com` 不在短链接解析列表中
   - Step 0 的短链接检测遗漏了这个域名

3. **平台策略表更新滞后**
   - 小红书 URL 格式变化后，策略表没更新
   - 新版 URL 结构（如 `/discovery/item/`）未覆盖

4. **降级逻辑过于激进**
   - 平台识别失败后直接 fallback 到通用网页
   - 没有二次确认机制

## 修复方案（Fix）

### 1. 扩展 URL 正则

```javascript
// 之前
const xhs_pattern = /xiaohongshu\.com\/explore\//;

// 之后
const xhs_pattern = /xiaohongshu\.com\/(explore|discovery|user\/profile|note)\//;
```

### 2. 注册短链接域名

在 Step 0 的短链接列表中添加：
```javascript
const short_link_domains = [
  'xhslink.com',      // 小红书
  'b23.tv',            // B站
  'v.douyin.com',      // 抖音
  't.cn',              // 微博
  'youtu.be',          // YouTube
];
```

### 3. 平台识别二次确认

```python
def identify_platform(url):
    # 第一次匹配
    platform = match_platform_regex(url)

    if not platform:
        # 二次确认：尝试 CDP 解析
        try:
            resolved_url = cdp_resolve_redirect(url)
            platform = match_platform_regex(resolved_url)
        except:
            pass

    return platform or 'generic'
```

### 4. 用户主页特殊处理

在 `platform-xhs.md` 策略文件中添加：
```markdown
## 用户主页处理

如果 URL 匹配 `/user/profile/`：
1. 不提取内容
2. 询问用户："要剪藏这个用户的哪篇帖子？"
3. 等待用户提供具体帖子 URL
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **标准小红书帖子**
   ```
   输入：剪藏 https://www.xiaohongshu.com/explore/6658a1234567890
   断言：
   - 加载 strategies/platform-xhs.md
   - 使用 CDP
   - 调用 OCR
   - 输出有图片内容
   ```

2. **小红书短链接**
   ```
   输入：保存 https://xhslink.com/abc123
   断言：
   - 识别为小红书短链接
   - 先解析重定向
   - 继续平台策略流程
   ```

3. **小红书用户主页**
   ```
   输入：提取 https://www.xiaohongshu.com/user/profile/xxx
   断言：
   - 识别为用户主页
   - 不提取内容
   - 询问用户具体帖子
   ```

4. **新版 URL 格式**
   ```
   输入：剪藏 https://www.xiaohongshu.com/discovery/item/xxx
   断言：
   - 匹配到小红书平台
   - 走平台策略流程
   ```

## 相关案例

- `content-type-misclassification/`：内容类型误判（视频当文章处理）
- `extraction-failure/`：提取失败但未降级

## 监控指标

- **平台识别准确率**：每周统计，目标 100%
- **小红书 URL 提取成功率**：每周统计，目标 ≥95%
- **用户主页误提取次数**：目标 0

## 最后更新

2026-07-15
