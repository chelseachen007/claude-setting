# 反模式：强行关联不相关卡片

## 症状（Symptom）

连接章节推荐了与文章内容不相关的卡片，关联原因泛泛（如"主题相关"、"都是知识管理"）。用户看到后觉得 AI 在凑数。

用户看到的现象：
- 文章讲的是"番茄工作法"
- 推荐了"量子物理"卡片
- 关联原因："都是科学方法"
- 用户困惑：这有什么关系？

## 反模式（Anti-Pattern）

AI 为了达到推荐数量（3-12 条），强行关联不相关的卡片。

错误做法：
1. 搜索到一些卡片
2. 不够 3 条
3. 降低相关性阈值，强行凑数
4. 用泛泛的理由解释关联

正确做法：
1. 搜索相关卡片
2. 严格验证相关性
3. 只推荐真正相关的卡片
4. 宁缺毋滥

## 示例 Prompt

### Case 1：时间管理文章
```
输入：处理这篇关于时间管理的剪藏

错误输出：
## 连接

### 已有卡片
- [[番茄工作法]] — 时间管理方法
- [[量子物理]] — 科学方法论（关联原因：都是科学方法）
- [[经济学原理]] — 资源分配（关联原因：时间也是资源）
- [[哲学思考]] — 思维方式（关联原因：需要深度思考）

正确输出：
## 连接

### 已有卡片
- [[番茄工作法]] — 25 分钟专注工作法
- [[心流状态]] — 深度专注的心理状态
- [[深度工作]] — 卡尔·纽波特的深度工作理论

### 可建新卡片
- [[时间块管理]] — 按时间块规划一天的方法
```

### Case 2：AI Agent 文章
```
输入：处理这篇关于 AI Agent 的剪藏

错误输出：
## 连接

### 已有卡片
- [[Claudian]] — Claude AI 插件
- [[Python]] — 编程语言（关联原因：AI 用 Python）
- [[数据结构]] — 计算机基础（关联原因：AI 是计算机科学）
- [[机器学习]] — AI 基础（关联原因：Agent 用到 ML）

正确输出：
## 连接

### 已有卡片
- [[Claude Code]] — 用户正在使用的 AI 工具
- [[Prompt Engineering]] — 与 AI 交互的方法
- [[MCP]] — 模型上下文协议

### 可建新卡片
- [[AI Agent 架构]] — AI Agent 的设计模式
- [[ReAct 框架]] — 推理-行动循环框架
```

## 为什么失败（Why It Fails）

### 根因分析

1. **数量压力**
   - SKILL.md 要求"已有卡片 3-12 条"
   - AI 为了达到数量，降低相关性阈值

2. **相关性判断过于宽松**
   - 只看主题词是否出现，不看上下文
   - "科学方法"出现在两个不同领域，就算相关

3. **缺乏质量门禁**
   - 没有验证关联原因是否具体
   - 没有检查关联是否真正有价值

4. **搜索策略问题**
   - 搜索范围太广
   - 没有按相关性排序

## 修复方案（Fix）

### 1. 调整数量要求

在 SKILL.md 中修改：

```markdown
#### 连接 — 已有卡片（3-12 条）
- 每条用 `[[卡片名]]` 格式
- 每条后面用破折号简短说明关联原因（10-20 字）
- **只推荐真正相关的，宁缺毋滥**
- 如果相关卡片不足 3 条，可以少于 3 条
- **禁止为了凑数强行关联**
```

### 2. 实现严格的相关性验证

```python
def validate_connection_relevance(card, article, min_relevance=0.5):
    """验证卡片关联是否真正相关"""

    # 提取卡片和文章的核心概念
    card_concepts = extract_core_concepts(card.content)
    article_concepts = extract_core_concepts(article.content)

    # 计算概念重叠度
    overlap = card_concepts & article_concepts
    overlap_ratio = len(overlap) / len(article_concepts) if article_concepts else 0

    # 检查关联原因是否具体
    reason = generate_relevance_reason(card, article)
    is_specific = len(reason) > 10 and not is_generic_reason(reason)

    # 综合判断
    is_relevant = overlap_ratio >= min_relevance and is_specific

    return is_relevant, reason

def is_generic_reason(reason):
    """判断是否是泛泛的关联原因"""
    generic_phrases = [
        "主题相关", "都是", "相关领域", "类似",
        "有关系", "有关联", "涉及", "包含"
    ]
    return any(phrase in reason for phrase in generic_phrases)
```

### 3. 宁缺毋滥原则

```python
def generate_connections(article, user_anchor, min_count=0, max_count=12):
    """生成连接（宁缺毋滥）"""

    # 搜索候选卡片
    candidates = search_relevant_cards(article)

    # 严格验证相关性
    validated = []
    for candidate in candidates:
        is_relevant, reason = validate_connection_relevance(candidate, article)
        if is_relevant:
            validated.append({
                "card": candidate,
                "reason": reason,
                "relevance_score": calculate_relevance(candidate, article)
            })

    # 按相关性排序
    validated.sort(key=lambda x: x["relevance_score"], reverse=True)

    # 取前 max_count 个，但不少于 min_count
    connections = validated[:max_count]

    # 如果不足 min_count，不强行补充
    if len(connections) < min_count:
        # 记录日志，但不报错
        log_warning(f"相关卡片不足 {min_count} 条，只有 {len(connections)} 条")

    return connections
```

### 4. 添加关联原因验证

```python
def validate_connection_reason(reason):
    """验证关联原因是否具体"""

    # 泛泛的原因
    generic_patterns = [
        r"都是.*",
        r"相关.*",
        r"类似.*",
        r"有关系.*",
        r"有关联.*",
        r"涉及.*",
        r"包含.*"
    ]

    for pattern in generic_patterns:
        if re.match(pattern, reason):
            return False, f"关联原因太泛泛: {reason}"

    # 检查长度
    if len(reason) < 10:
        return False, f"关联原因太短: {reason}"

    # 检查是否包含具体信息
    if not has_specific_info(reason):
        return False, f"关联原因缺乏具体信息: {reason}"

    return True, "OK"

def has_specific_info(reason):
    """检查是否包含具体信息"""
    # 具体信息的特征
    specific_indicators = [
        "因为", "用于", "基于", "通过", "实现",
        "解决", "处理", "分析", "研究", "应用"
    ]
    return any(indicator in reason for indicator in specific_indicators)
```

### 5. 添加负面示例

在 SKILL.md 的输出格式示例中添加：

```markdown
## 连接

### ❌ 错误示例（强行关联）
- [[量子物理]] — 科学方法论（关联原因：都是科学方法）
- [[经济学原理]] — 资源分配（关联原因：时间也是资源）
- [[哲学思考]] — 思维方式（关联原因：需要深度思考）

### ✅ 正确示例（真正相关）
- [[番茄工作法]] — 25 分钟专注工作法（文章核心方法）
- [[心流状态]] — 深度专注的心理状态（专注力原理的基础）
- [[深度工作]] — 卡尔·纽波特的深度工作理论（时间管理进阶）
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **时间管理文章**
   ```
   输入：处理这篇关于时间管理的剪藏
   断言：
   - 不推荐不相关的卡片（如量子物理、经济学）
   - 关联原因具体（不是"都是科学方法"）
   - 宁缺毋滥：可以少于 3 条
   ```

2. **AI Agent 文章**
   ```
   输入：处理这篇关于 AI Agent 的剪藏
   断言：
   - 不推荐不相关的卡片（如 Python、数据结构）
   - 关联原因具体
   ```

3. **投资心理学文章**
   ```
   输入：处理这篇关于投资心理学的剪藏
   断言：
   - 不推荐不相关的卡片（如宏观经济学）
   - 关联原因具体
   ```

## 监控指标

- **关联相关性得分**：每周统计，目标 ≥0.5
- **泛泛关联出现率**：目标 0%
- **用户满意度**：每月统计，目标 ≥4/5

## 相关案例

- `non-existent-cards/`：推荐不存在的卡片
- `ignore-user-anchor/`：忽略入库思考

## 最后更新

2026-07-15
