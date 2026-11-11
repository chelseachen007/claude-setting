# 反模式：推荐不存在的卡片

## 症状（Symptom）

连接章节推荐了 `[[卡片名]]`，但 `卡片/` 目录下根本没有这个文件。用户点击链接跳转到空页面，体验极差。

用户看到的现象：
- 点击 `[[卡片名]]` 链接
- Obsidian 显示"创建新笔记"
- 用户困惑：这个卡片不是应该存在吗？

## 反模式（Anti-Pattern）

AI 基于语义猜测卡片名（如"时间管理"），但没有实际搜索验证。

错误做法：
1. 理解文章主题
2. 猜测相关卡片名（如"时间管理"、"效率提升"）
3. 直接推荐，没有验证存在性

正确做法：
1. 理解文章主题
2. 提取 3-5 个核心关键词
3. 在 `卡片/` 目录搜索
4. 读取候选卡片前 10 行验证相关性
5. 只推荐真实存在的卡片

## 示例 Prompt

### Case 1：时间管理文章
```
输入：处理这篇关于时间管理的剪藏

错误输出：
## 连接

### 已有卡片
- [[时间管理]] — 时间管理方法论
- [[效率提升]] — 提升工作效率的技巧
- [[专注力]] — 专注力研究

（假设"时间管理"和"效率提升"卡片不存在）

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
- [[AI Agent]] — AI Agent 架构
- [[大语言模型]] — LLM 技术
- [[ReAct]] — ReAct 框架

（假设"AI Agent"和"ReAct"卡片不存在）

正确输出：
## 连接

### 已有卡片
- [[Claudian]] — Claude AI 集成插件
- [[MCP]] — 模型上下文协议
- [[Prompt Engineering]] — 提示词工程

### 可建新卡片
- [[AI Agent 架构]] — AI Agent 的设计模式
- [[ReAct 框架]] — 推理-行动循环框架
```

## 为什么失败（Why It Fails）

### 根因分析

1. **搜索不够彻底**
   - 只搜了 1-2 个关键词
   - 没有扩展搜索同义词和相关词
   - 搜索范围太窄（只搜文件名，没搜内容）

2. **没有验证存在性**
   - 推荐前没有检查文件是否存在
   - 没有读取卡片内容验证相关性

3. **卡片名猜测过于自信**
   - AI 认为"时间管理"这样的通用词肯定有对应卡片
   - 没有考虑到用户的卡片命名习惯

4. **搜索策略单一**
   - 只用了文件名搜索
   - 没有用内容搜索（grep）

## 修复方案（Fix）

### 1. 强制搜索验证

在 Step 5 中添加：

```python
def search_and_validate_cards(article_keywords):
    """搜索并验证卡片存在性"""

    # Step 1: 核心关键词搜索
    candidates = []
    for keyword in article_keywords:
        # 文件名搜索
        files = glob(f"卡片/*{keyword}*.md")
        candidates.extend(files)

        # 内容搜索
        content_matches = grep(f"卡片/", keyword)
        candidates.extend(content_matches)

    # Step 2: 去重
    candidates = list(set(candidates))

    # Step 3: 读取并验证相关性
    validated = []
    for candidate in candidates:
        # 读取前 10 行
        content = read_first_n_lines(candidate, 10)

        # 验证相关性
        if is_relevant(content, article_keywords):
            validated.append(candidate)

    return validated
```

### 2. 扩展搜索策略

```python
def expanded_search(keywords):
    """扩展搜索策略"""

    all_candidates = []

    # 第一轮：核心关键词
    for keyword in keywords:
        all_candidates.extend(search_keyword(keyword))

    # 第二轮：同义词扩展
    synonyms = get_synonyms(keywords)
    for synonym in synonyms:
        all_candidates.extend(search_keyword(synonym))

    # 第三轮：主题扩展
    related_topics = get_related_topics(keywords)
    for topic in related_topics:
        all_candidates.extend(search_keyword(topic))

    return list(set(all_candidates))

def get_synonyms(keywords):
    """获取同义词"""
    synonym_map = {
        "时间管理": ["时间规划", "时间分配", "日程管理"],
        "效率": ["生产力", "效能", "产出"],
        "专注": ["注意力", "集中", "心流"],
    }
    synonyms = []
    for keyword in keywords:
        if keyword in synonym_map:
            synonyms.extend(synonym_map[keyword])
    return synonyms
```

### 3. 推荐前强制验证

```python
def generate_connections(article, user_anchor):
    """生成连接（强制验证）"""

    # Step 1: 搜索候选卡片
    candidates = search_and_validate_cards(article.keywords)

    # Step 2: 读取并验证相关性
    validated = []
    for candidate in candidates:
        # 读取卡片内容
        content = read_file(candidate)

        # 验证相关性
        relevance_score = calculate_relevance(content, article)
        if relevance_score > 0.3:  # 阈值
            validated.append({
                "name": extract_card_name(candidate),
                "relevance": relevance_score,
                "reason": generate_relevance_reason(content, article)
            })

    # Step 3: 按相关性排序
    validated.sort(key=lambda x: x["relevance"], reverse=True)

    # Step 4: 取前 12 个
    top_cards = validated[:12]

    # Step 5: 验证所有推荐的卡片都存在
    for card in top_cards:
        assert card_exists(card["name"]), f"卡片不存在: {card['name']}"

    return top_cards
```

### 4. 添加验证断言

在 Step 7 写入前添加：

```python
def validate_connections(connections):
    """验证所有推荐的卡片都存在"""

    for card in connections["existing_cards"]:
        card_name = extract_wikilink_name(card)
        card_path = f"卡片/{card_name}.md"

        if not os.path.exists(card_path):
            raise ValidationError(f"推荐的卡片不存在: {card_name}")

    return True
```

### 5. "可建新卡片"章节处理

```markdown
#### 连接 — 可建新卡片（2-6 条）
- 每条用 `[[新卡片名]]` 格式（不存在的卡片）
- 每条后面说明为什么值得建以及建议内容方向
- 标准：文章中提到的有价值概念/方法，但 vault 中没有对应卡片
- **重要**：明确告知用户这些是"建议新建"，不是已存在的卡片
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **时间管理文章**
   ```
   输入：处理这篇关于时间管理的剪藏
   断言：
   - 所有推荐的 [[卡片名]] 在 卡片/ 目录真实存在
   - 不推荐不存在的卡片
   - 可建新卡片章节明确标注为"建议新建"
   ```

2. **AI Agent 文章**
   ```
   输入：处理这篇关于 AI Agent 的剪藏
   断言：
   - 所有推荐的 [[卡片名]] 在 卡片/ 目录真实存在
   - 不推荐不存在的卡片
   ```

3. **投资心理学文章**
   ```
   输入：处理这篇关于投资心理学的剪藏
   断言：
   - 所有推荐的 [[卡片名]] 在 卡片/ 目录真实存在
   - 不推荐不存在的卡片
   ```

## 监控指标

- **推荐卡片存在率**：每周统计，目标 100%
- **用户点击空链接次数**：目标 0
- **搜索覆盖率**：每周统计，目标 ≥80%（相关卡片被搜到的比例）

## 相关案例

- `summary-as-evergreen/`：常青笔记变成文章总结
- `forced-connections/`：强行关联不相关卡片

## 最后更新

2026-07-15
