# 反模式：行动项太空泛

## 症状（Symptom）

行动章节出现"深入学习"、"了解更多"、"研究一下"、"继续关注"等空泛的行动项。用户看到后不知道具体要做什么，行动项形同虚设。

用户看到的现象：
- 行动项写着"深入学习时间管理"
- 不知道从哪里开始
- 不知道怎么才算完成
- 最终忽略这个行动项

## 反模式（Anti-Pattern）

AI 没有理解"行动项"的定义——应该是"具体的、可执行的、可验证的"任务。

错误做法：
1. 理解文章主题
2. 生成泛泛的行动建议
3. 没有考虑可执行性

正确做法：
1. 理解文章核心洞见
2. 基于用户入库思考生成具体行动
3. 验证：用户看到后知道具体要做什么吗？

## 示例 Prompt

### Case 1：时间管理文章
```
输入：处理这篇关于时间管理的剪藏

错误输出：
## 行动
- [ ] 深入学习时间管理方法
- [ ] 了解更多关于番茄工作法的内容
- [ ] 继续关注效率提升的技巧

正确输出：
## 行动
- [ ] 明天上午 9-11 点尝试番茄工作法，用手机计时器设置 25 分钟
- [ ] 本周记录 3 天的工作时间分配，找出最大的时间黑洞
- [ ] 在 Obsidian 中创建"时间管理"卡片，记录实验结果
```

### Case 2：AI Agent 文章
```
输入：处理这篇关于 AI Agent 的剪藏

错误输出：
## 行动
- [ ] 深入学习 AI Agent 架构
- [ ] 了解更多关于 ReAct 框架
- [ ] 研究 AI Agent 的应用场景

正确输出：
## 行动
- [ ] 用 Claude Code 创建一个简单的 AI Agent demo，实现"思考-行动"循环
- [ ] 在 Obsidian 中创建"AI Agent 架构"卡片，记录 ReAct 框架的核心原理
- [ ] 找 3 个可以用 AI Agent 自动化的工作流，评估可行性
```

### Case 3：投资心理学文章
```
输入：处理这篇关于投资心理学的剪藏

错误输出：
## 行动
- [ ] 深入学习投资心理学
- [ ] 了解更多关于损失厌恶
- [ ] 继续关注行为金融学

正确输出：
## 行动
- [ ] 回顾最近 3 次亏损的投资决策，分析是否有损失厌恶的影响
- [ ] 在投资笔记中创建"心理偏差检查清单"，每次交易前自检
- [ ] 设定止损规则：单笔亏损超过 10% 必须卖出，写入投资策略文档
```

## 为什么失败（Why It Fails）

### 根因分析

1. **没有理解"可执行"的定义**
   - AI 把"行动项"理解为"学习建议"
   - 没有区分"学习"和"执行"

2. **缺乏具体性**
   - 没有时间（什么时候做？）
   - 没有地点（在哪里做？）
   - 没有方式（怎么做？）
   - 没有标准（怎么算完成？）

3. **没有基于用户锚点**
   - 行动项与用户的入库思考无关
   - 没有考虑用户的当下关联

4. **生成逻辑过于简单**
   - 直接从文章主题生成泛泛建议
   - 没有经过"具体化"处理

## 修复方案（Fix）

### 1. 在 SKILL.md 中明确定义

在 Step 6b 添加：

```markdown
#### 行动（1-3 条）
- 具体的、可执行的行动项
- 用 `- [ ]` 格式
- 只写真正会去做的事，不要写"深入学习"这种空话
- **检验方法**：用户看到后知道具体要做什么吗？
- **必须包含**：
  - 明确的动词（创建、记录、尝试、回顾...）
  - 具体的对象（哪个文件、哪个工具、哪个场景...）
  - 可选的时间（明天、本周、下次...）
- **禁止**：深入学习、了解更多、研究一下、继续关注、后续跟进
```

### 2. 实现具体化逻辑

```python
def generate_specific_action(vague_action, user_anchor):
    """将泛泛建议转化为具体行动"""

    # 泛泛行动的模式
    vague_patterns = {
        "深入学习": "create_card_and_experiment",
        "了解更多": "find_3_specific_examples",
        "研究一下": "create_research_notes",
        "继续关注": "set_up_monitoring",
        "后续跟进": "schedule_follow_up"
    }

    # 检测是否是泛泛建议
    for pattern, action_type in vague_patterns.items():
        if pattern in vague_action:
            # 转化为具体行动
            return convert_to_specific(vague_action, action_type, user_anchor)

    # 如果不是泛泛建议，直接返回
    return vague_action

def convert_to_specific(vague_action, action_type, user_anchor):
    """转化为具体行动"""

    if action_type == "create_card_and_experiment":
        # "深入学习时间管理" → "创建时间管理卡片并实验番茄工作法"
        topic = extract_topic(vague_action)
        return f"在 Obsidian 中创建'{topic}'卡片，记录核心概念和实验结果"

    elif action_type == "find_3_specific_examples":
        # "了解更多关于番茄工作法" → "找 3 个番茄工作法的实际应用案例"
        topic = extract_topic(vague_action)
        return f"找 3 个'{topic}'的实际应用案例，记录到卡片中"

    elif action_type == "create_research_notes":
        # "研究一下 AI Agent" → "创建 AI Agent 研究笔记，记录架构和应用场景"
        topic = extract_topic(vague_action)
        return f"创建'{topic}'研究笔记，记录核心原理和应用场景"

    elif action_type == "set_up_monitoring":
        # "继续关注效率提升" → "每周记录工作效率数据，持续 4 周"
        topic = extract_topic(vague_action)
        return f"每周记录'{topic}'相关数据，持续 4 周，分析趋势"

    elif action_type == "schedule_follow_up":
        # "后续跟进" → "下周三回顾这个剪藏，检查行动项完成情况"
        return "下周三回顾这个剪藏，检查行动项完成情况"
```

### 3. 基于用户锚点生成

```python
def generate_actions_from_anchor(article, user_anchor):
    """基于用户锚点生成行动项"""

    actions = []

    # 从用户打动点生成行动
    if user_anchor.touch_point:
        action = generate_action_from_touch_point(
            user_anchor.touch_point,
            article
        )
        actions.append(action)

    # 从用户当下关联生成行动
    if user_anchor.current_relation:
        action = generate_action_from_current_relation(
            user_anchor.current_relation,
            article
        )
        actions.append(action)

    # 验证具体性
    specific_actions = []
    for action in actions:
        if is_specific(action):
            specific_actions.append(action)
        else:
            # 具体化
            specific = make_specific(action)
            specific_actions.append(specific)

    return specific_actions[:3]  # 最多 3 条

def is_specific(action):
    """判断行动是否具体"""

    # 检查是否包含明确动词
    specific_verbs = ["创建", "记录", "尝试", "回顾", "分析", "设定", "找", "写"]
    has_verb = any(verb in action for verb in specific_verbs)

    # 检查是否包含具体对象
    has_object = len(action) > 15  # 简单启发：足够长

    # 检查是否是泛泛建议
    vague_phrases = ["深入学习", "了解更多", "研究一下", "继续关注"]
    is_vague = any(phrase in action for phrase in vague_phrases)

    return has_verb and has_object and not is_vague
```

### 4. 添加验证断言

在 Step 7 写入前添加：

```python
def validate_actions(actions):
    """验证行动项是否具体"""

    vague_phrases = [
        "深入学习", "了解更多", "研究一下", "继续关注",
        "后续跟进", "进一步", "持续", "不断"
    ]

    for action in actions:
        for phrase in vague_phrases:
            if phrase in action:
                raise ValidationError(f"行动项太空泛: {action}")

    return True
```

### 5. 添加负面示例

在 SKILL.md 的输出格式示例中添加：

```markdown
## 行动

### ❌ 错误示例（空泛）
- [ ] 深入学习时间管理方法
- [ ] 了解更多关于番茄工作法
- [ ] 继续关注效率提升

### ✅ 正确示例（具体）
- [ ] 明天上午 9-11 点尝试番茄工作法，用手机计时器设置 25 分钟
- [ ] 本周记录 3 天的工作时间分配，找出最大的时间黑洞
- [ ] 在 Obsidian 中创建"时间管理"卡片，记录实验结果
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **时间管理文章**
   ```
   输入：处理这篇关于时间管理的剪藏
   断言：
   - 行动项不包含"深入学习"、"了解更多"
   - 行动项有明确动词和具体对象
   - 用户看到后知道具体要做什么
   ```

2. **AI Agent 文章**
   ```
   输入：处理这篇关于 AI Agent 的剪藏
   断言：
   - 行动项不包含"深入学习"、"了解更多"
   - 行动项有明确动词和具体对象
   ```

3. **投资心理学文章**
   ```
   输入：处理这篇关于投资心理学的剪藏
   断言：
   - 行动项不包含"深入学习"、"了解更多"
   - 行动项有明确动词和具体对象
   ```

## 监控指标

- **行动项具体率**：每周统计，目标 ≥90%
- **用户执行率**：每月统计，目标 ≥50%（用户实际执行的比例）
- **空泛行动出现率**：目标 0%

## 相关案例

- `summary-as-evergreen/`：常青笔记变成文章总结
- `ignore-user-anchor/`：忽略入库思考

## 最后更新

2026-07-15
