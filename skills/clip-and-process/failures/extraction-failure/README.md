# 反模式：提取失败但未降级

## 症状（Symptom）

Layer 1 直取失败（如返回 403/空内容），但没有尝试 Layer 2 CDP，直接告知用户"提取失败，请手动粘贴"。

用户看到的现象：
- 收到提示："提取失败，请手动粘贴内容"
- 没有尝试其他提取方式
- 用户需要自己复制粘贴全文

## 反模式（Anti-Pattern）

错误处理逻辑过于简单——Layer 1 失败就放弃，没有执行 SKILL.md 中定义的三层降级策略。

错误行为链：
1. 收到 URL：`https://www.wsj.com/articles/xxx`
2. Layer 1: web_reader → 返回 403 或部分内容
3. 直接判定"提取失败"
4. 告知用户手动粘贴

正确行为链：
1. 收到 URL：`https://www.wsj.com/articles/xxx`
2. Layer 1: web_reader → 返回 403 或部分内容
3. 检测到付费墙信号（403、"subscribe"、"login"）
4. Layer 1.5: 尝试付费墙绕过（如 Google Cache、Archive.org）
5. 失败则 Layer 2: CDP 浏览器自动化
6. 失败则 Layer 3: 缓存镜像
7. 全部失败才告知用户

## 示例 Prompt

### Case 1：付费墙文章
```
输入：剪藏 https://www.wsj.com/articles/ai-agents-future

错误行为：
- Layer 1 web_reader → 403 Forbidden
- 直接告知"提取失败"

正确行为：
- Layer 1 失败
- 检测付费墙信号
- Layer 1.5 尝试绕过
- Layer 2 CDP 尝试
- Layer 3 缓存镜像
- 全部失败才告知用户
```

### Case 2：JavaScript 渲染页面
```
输入：保存 https://www.notion.so/xxx

错误行为：
- Layer 1 web_reader → 空内容（JS 未渲染）
- 直接告知"提取失败"

正确行为：
- Layer 1 返回空内容
- 判断可能是 JS 渲染问题
- Layer 2 CDP 打开并等待渲染
- 提取完整内容
```

### Case 3：反爬虫机制
```
输入：提取 https://www.zhihu.com/question/xxx

错误行为：
- Layer 1 web_reader → 返回验证码页面
- 直接告知"提取失败"

正确行为：
- Layer 1 返回异常内容
- 检测到反爬信号
- Layer 2 CDP + Cookie 模拟登录态
- 提取完整内容
```

## 为什么失败（Why It Fails）

### 根因分析

1. **降级逻辑未严格执行**
   - SKILL.md 定义了三层降级，但执行时没有严格遵循
   - AI 的"默认行为"是失败就放弃，不是尝试降级

2. **付费墙检测逻辑缺失**
   - 没有明确的付费墙信号检测规则
   - 不知道什么情况下应该触发 Layer 1.5

3. **降级条件不明确**
   - Layer 1 返回什么状态码需要降级？
   - 返回多少内容算"部分成功"？
   - 这些边界条件没有定义清楚

4. **超时处理不当**
   - Layer 2 CDP 可能耗时较长
   - 超时后没有 fallback 到 Layer 3

## 修复方案（Fix）

### 1. 明确降级触发条件

在 `strategies/layer1-direct-fetch.md` 中添加：

```markdown
## 降级触发条件

以下情况必须降级到 Layer 1.5/2/3：

### HTTP 状态码
- 403 Forbidden
- 401 Unauthorized
- 402 Payment Required
- 429 Too Many Requests

### 内容异常
- 返回内容 < 100 字（疑似空页面）
- 包含 "subscribe"、"login"、"paywall"、"premium" 关键词
- 包含验证码（CAPTCHA）相关元素

### 技术异常
- 返回内容全是 JavaScript 代码
- 返回 "Access Denied" 或 "Blocked"
- 超时（>30s）
```

### 2. 实现付费墙检测

在 `strategies/layer1.5-paywall-bypass.md` 中添加：

```python
def detect_paywall(content, status_code):
    """检测是否遇到付费墙"""

    # HTTP 状态码检测
    if status_code in [401, 402, 403]:
        return True

    # 关键词检测
    paywall_keywords = [
        'subscribe', 'login required', 'paywall',
        'premium content', 'members only', '付费',
        '请登录', '开通会员'
    ]
    content_lower = content.lower()
    for keyword in paywall_keywords:
        if keyword in content_lower:
            return True

    # 内容长度检测
    if len(content.strip()) < 100:
        return True

    return False
```

### 3. 强制降级逻辑

在 Step 1.3 的通用网页处理中添加：

```python
def extract_with_fallback(url):
    """三层降级提取"""

    # Layer 1: 直取
    result = layer1_direct_fetch(url)
    if result.success and not detect_paywall(result.content, result.status_code):
        return result

    # Layer 1.5: 付费墙绕过
    if detect_paywall(result.content, result.status_code):
        result = layer1_5_paywall_bypass(url)
        if result.success:
            return result

    # Layer 2: CDP
    result = layer2_cdp(url)
    if result.success:
        return result

    # Layer 3: 缓存镜像
    result = layer3_cache_mirror(url)
    if result.success:
        return result

    # 全部失败
    return ExtractionResult(
        success=False,
        message="所有提取方式都失败了，请手动粘贴内容。"
    )
```

### 4. 超时和错误处理

```python
# Layer 2 CDP 超时设置
CDP_TIMEOUT = 30  # 秒

def layer2_cdp(url):
    try:
        result = cdp_extract(url, timeout=CDP_TIMEOUT)
        return result
    except TimeoutError:
        # CDP 超时，fallback 到 Layer 3
        return layer3_cache_mirror(url)
    except Exception as e:
        # CDP 异常，fallback 到 Layer 3
        return layer3_cache_mirror(url)
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **付费墙文章（WSJ）**
   ```
   输入：剪藏 https://www.wsj.com/articles/ai-agents-future
   断言：
   - Layer 1 失败后尝试 Layer 1.5
   - 最终使用 Layer 2 或 Layer 3
   - 不直接告知"提取失败"
   ```

2. **JS 渲染页面（Notion）**
   ```
   输入：保存 https://www.notion.so/xxx
   断言：
   - Layer 1 返回空内容后尝试 Layer 2
   - 使用 CDP 等待 JS 渲染
   - 提取完整内容
   ```

3. **反爬虫页面（知乎）**
   ```
   输入：提取 https://www.zhihu.com/question/xxx
   断言：
   - Layer 1 返回异常后尝试 Layer 2
   - 使用 CDP 模拟浏览器
   - 提取完整内容
   ```

4. **正常页面（不应降级）**
   ```
   输入：剪藏 https://www.example.com/article
   断言：
   - Layer 1 成功后直接返回
   - 不触发降级逻辑
   ```

## 监控指标

- **降级触发率**：每周统计，目标 <20%（大部分应该 Layer 1 成功）
- **Layer 2 成功率**：每周统计，目标 ≥80%
- **最终提取成功率**：每周统计，目标 ≥95%
- **用户手动粘贴率**：每周统计，目标 <5%

## 相关案例

- `wrong-platform-routing/`：平台识别错误
- `empty-or-truncated/`：内容为空或截断

## 最后更新

2026-07-15
