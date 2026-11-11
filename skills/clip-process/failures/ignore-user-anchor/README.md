# 反模式：忽略入库思考

## 症状（Symptom）

常青笔记和连接与用户的入库思考（打动点+当下关联）完全无关。用户觉得 AI 没有理解自己为什么剪藏这篇文章。

用户看到的现象：
- 用户入库思考："打动点是番茄工作法的专注力原理"
- 常青笔记写的是"时间管理的历史发展"
- 连接推荐的是"效率工具"卡片
- 用户困惑：AI 没理解我为什么收藏这篇文章

## 反模式（Anti-Pattern）

AI 没有以用户的入库思考为锚点，而是独立生成内容。

错误做法：
1. 读取文章内容
2. 独立生成常青笔记和连接
3. 忽略用户的入库思考

正确做法：
1. 读取文章内容
2. 读取用户的入库思考
3. 以入库思考为锚点生成内容
4. 确保常青笔记覆盖打动点，连接呼应当下关联

## 示例 Prompt

### Case 1：时间管理文章
```
输入：处理这篇关于时间管理的剪藏

用户入库思考：
- 打动点：番茄工作法的专注力原理
- 当下关联：最近工作效率下降，想找方法提升

错误输出：
## 常青笔记
### 时间管理的历史发展
从工业时代到信息时代，时间管理理论不断演进...

## 连接
- [[效率工具]] — 各种效率工具对比
- [[历史发展]] — 管理理论发展史

正确输出：
## 常青笔记
### 时间块的专注力原理
25 分钟是人类注意力的一个自然周期。短于 20 分钟进入不了心流，
长于 30 分钟疲劳累积导致效率下降。这个时间窗口是大脑的"甜点区"。

## 连接
- [[心流状态]] — 专注力的心理学研究
- [[工作效率]] — 提升工作效率的方法
- [[疲劳管理]] — 避免过度疲劳的策略
```

### Case 2：AI Agent 文章
```
输入：处理这篇关于 AI Agent 的剪藏

用户入库思考：
- 打动点：ReAct 框架的"思考-行动"循环
- 当下关联：正在用 Claude Code，想了解底层架构

错误输出：
## 常青笔记
### AI 的发展历程
从早期的专家系统到现代的大语言模型...

## 连接
- [[人工智能]] — AI 发展历史
- [[机器学习]] — ML 基础知识

正确输出：
## 常青笔记
### 思考-行动循环的价值
让 AI 先想再做、做完再想，比直接输出结果更可靠。
这个模式适用于所有需要多步骤决策的场景——不只是 AI，
人类决策也应该这样。

## 连接
- [[Claude Code]] — 用户正在使用的 AI 工具
- [[Prompt Engineering]] — 与 AI 交互的方法
- [[MCP]] — 模型上下文协议
```

## 为什么失败（Why It Fails）

### 根因分析

1. **没有读取入库思考**
   - AI 跳过了 Step 4（入库思考）
   - 或者读取了但没有作为锚点

2. **独立生成逻辑**
   - AI 的默认行为是基于文章内容生成
   - 没有强制要求以用户输入为锚点

3. **缺乏锚点验证**
   - 没有检验常青笔记是否覆盖打动点
   - 没有检验连接是否呼应当下关联

4. **入库思考格式不规范**
   - 用户的入库思考可能写得不清楚
   - AI 无法提取有效的锚点信息

## 修复方案（Fix）

### 1. 强制读取入库思考

在 Step 6a 添加：

```python
def analyze_with_anchor(article, user_anchor):
    """以用户入库思考为锚点进行分析"""

    # Step 1: 读取用户入库思考
    touch_point = user_anchor.touch_point
    current_relation = user_anchor.current_relation

    if not touch_point or not current_relation:
        # 如果入库思考不完整，询问用户
        return ask_for_clarification()

    # Step 2: 提取锚点关键词
    anchor_keywords = extract_keywords(touch_point + " " + current_relation)

    # Step 3: 以锚点为重心生成分析
    analysis = {
        "key_entities": extract_entities(article),
        "connection_points": find_connection_points(article, anchor_keywords),
        "knowledge_tension": find_tension(article, anchor_keywords),
        "anchor_analysis": {
            "touch_point_mapping": map_touch_point(touch_point, article),
            "current_relation_implication": analyze_implication(current_relation, article)
        },
        "content_suggestions": {
            "evergreen_notes": suggest_evergreen_with_anchor(article, touch_point),
            "new_cards": suggest_cards_with_anchor(article, anchor_keywords),
            "actions": suggest_actions_with_anchor(article, current_relation)
        }
    }

    return analysis
```

### 2. 生成时强制锚点覆盖

```python
def generate_evergreen_with_anchor(article, touch_point):
    """生成常青笔记（覆盖打动点）"""

    # 从打动点提取核心概念
    touch_concepts = extract_concepts(touch_point)

    # 生成覆盖打动点的常青笔记
    notes = []
    for concept in touch_concepts:
        # 找到文章中与打动点相关的部分
        relevant_content = find_relevant_content(article, concept)

        # 生成常青笔记
        note = generate_note(relevant_content, concept)
        notes.append(note)

    # 验证覆盖度
    coverage = calculate_coverage(touch_point, notes)
    if coverage < 0.7:
        # 覆盖度不足，补充笔记
        additional = generate_additional_notes(article, touch_point, notes)
        notes.extend(additional)

    return notes[:3]  # 最多 3 条
```

### 3. 添加锚点验证

```python
def validate_anchor_alignment(content, user_anchor):
    """验证内容是否与入库思考对齐"""

    # 检查常青笔记是否覆盖打动点
    evergreen_coverage = check_evergreen_coverage(
        content.evergreen_notes,
        user_anchor.touch_point
    )

    # 检查连接是否呼应当下关联
    connection_alignment = check_connection_alignment(
        content.connections,
        user_anchor.current_relation
    )

    # 检查行动是否基于锚点
    action_relevance = check_action_relevance(
        content.actions,
        user_anchor
    )

    return {
        "evergreen_coverage": evergreen_coverage,
        "connection_alignment": connection_alignment,
        "action_relevance": action_relevance,
        "overall_score": (evergreen_coverage + connection_alignment + action_relevance) / 3
    }

def check_evergreen_coverage(notes, touch_point):
    """检查常青笔记是否覆盖打动点"""

    # 提取打动点的关键词
    touch_keywords = extract_keywords(touch_point)

    # 检查常青笔记是否包含这些关键词
    coverage_count = 0
    for keyword in touch_keywords:
        for note in notes:
            if keyword in note:
                coverage_count += 1
                break

    return coverage_count / len(touch_keywords) if touch_keywords else 0
```

### 4. 在 SKILL.md 中强调

在 Step 6b 添加：

```markdown
### Step 6b：生成内容（基于分析）

基于 6a 的分析结果，生成以下章节。**以用户的入库思考为锚点**——
打动用户的点应该在常青笔记和连接中得到呼应：

#### 常青笔记（1-3 条）
- 从文章中提炼的持久洞见
- **优先覆盖 6a 分析中的"用户锚点"**
- 打动用户的点应该在常青笔记中得到体现

#### 连接 — 已有卡片（3-12 条）
- 每条用 `[[卡片名]]` 格式
- **关联原因应呼应用户的当下关联**
- 不是泛泛的"主题相关"，而是"这个卡片跟你的当下关联有关"

#### 行动（1-3 条）
- 具体的、可执行的行动项
- **优先级参考 6a 的"用户锚点分析"中的行动方向**
- 基于用户的当下关联生成行动
```

### 5. 添加锚点覆盖检查

在 Step 7 写入前添加：

```python
def validate_content(content, user_anchor):
    """验证内容是否覆盖入库思考"""

    # 检查常青笔记
    if not covers_touch_point(content.evergreen_notes, user_anchor.touch_point):
        raise ValidationError("常青笔记未覆盖用户打动点")

    # 检查连接
    if not aligns_with_current_relation(content.connections, user_anchor.current_relation):
        raise ValidationError("连接未呼应用户当下关联")

    # 检查行动
    if not based_on_anchor(content.actions, user_anchor):
        raise ValidationError("行动未基于用户锚点")

    return True
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **时间管理文章**
   ```
   输入：处理这篇关于时间管理的剪藏
   用户入库思考：
   - 打动点：番茄工作法的专注力原理
   - 当下关联：最近工作效率下降

   断言：
   - 常青笔记覆盖"专注力原理"
   - 连接呼应"工作效率下降"
   - 行动基于"提升效率"
   ```

2. **AI Agent 文章**
   ```
   输入：处理这篇关于 AI Agent 的剪藏
   用户入库思考：
   - 打动点：ReAct 框架的"思考-行动"循环
   - 当下关联：正在用 Claude Code

   断言：
   - 常青笔记覆盖"思考-行动循环"
   - 连接包含"Claude Code"相关卡片
   - 行动与 Claude Code 使用相关
   ```

## 监控指标

- **锚点覆盖率**：每周统计，目标 ≥70%
- **用户满意度**：每月统计，目标 ≥4/5
- **人工评审得分**：每月 10 篇，目标 ≥70%

## 相关案例

- `summary-as-evergreen/`：常青笔记变成文章总结
- `vague-actions/`：行动项太空泛

## 最后更新

2026-07-15
