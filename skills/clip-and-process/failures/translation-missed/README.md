# 反模式：英文内容未翻译

## 症状（Symptom）

Medium/Substack 等英文站点的文章被提取后直接保存，没有触发 baoyu-translate 翻译，用户拿到的是纯英文剪藏。

用户看到的现象：
- 剪藏文件中只有英文原文
- 没有"## 译文"章节
- frontmatter 中没有 `language: en` 标记
- 用户需要自己翻译才能阅读

## 反模式（Anti-Pattern）

Step 2 的语言检测逻辑被跳过，或者检测为"非英文"。可能是域名启发列表不全，或者内容采样逻辑有 bug。

错误行为链：
1. 收到 URL：`https://medium.com/@xxx/how-to-build-ai-agents`
2. Layer 1 提取成功
3. 跳过语言检测（或检测失败）
4. 直接保存英文原文
5. 没有调用 baoyu-translate

正确行为链：
1. 收到 URL：`https://medium.com/@xxx/how-to-build-ai-agents`
2. Layer 1 提取成功
3. 域名启发：`medium.com` → 高概率英文
4. 内容采样确认：前 200 词英文 > 60%
5. 调用 baoyu-translate 翻译全文
6. 保存双语版本（原文 + 译文）

## 示例 Prompt

### Case 1：Medium 文章
```
输入：剪藏 https://medium.com/@xxx/how-to-build-ai-agents

错误行为：
- 提取成功
- 直接保存英文原文
- 没有翻译

正确行为：
- 提取成功
- 域名启发：medium.com → 英文
- 内容采样确认
- 调用 baoyu-translate
- 保存双语版本
```

### Case 2：Substack Newsletter
```
输入：保存 https://xxx.substack.com/p/ai-agents-2026

错误行为：
- 提取成功
- 直接保存英文原文
- 没有翻译

正确行为：
- 提取成功
- 域名启发：*.substack.com → 英文
- 内容采样确认
- 调用 baoyu-translate
- 保存双语版本
```

### Case 3：技术博客（.dev 域名）
```
输入：提取 https://blog.xxx.dev/article

错误行为：
- 提取成功
- 直接保存英文原文
- 没有翻译

正确行为：
- 提取成功
- 域名启发：*.dev → 英文
- 内容采样确认
- 调用 baoyu-translate
- 保存双语版本
```

### Case 4：中英混合文章
```
输入：剪藏 https://medium.com/@xxx/bilingual-article

错误行为：
- 提取成功
- 直接保存（认为是中文，因为有中文字符）

正确行为：
- 提取成功
- 内容采样：英文占比 > 60%（即使有中文）
- 调用 baoyu-translate
- 保存双语版本
```

## 为什么失败（Why It Fails）

### 根因分析

1. **域名启发列表不全**
   - 只列出了 `medium.com`，没覆盖 `*.medium.com` 子域名
   - `substack.com`、`*.dev`、`*.io` 等域名未注册
   - 新增的英文站点（如 `substack.com`）未及时添加

2. **内容采样逻辑有 bug**
   - 采样范围不正确（取了中文引用块）
   - 英文词识别算法有问题（把拼音当英文）
   - 阈值设置不合理（>60% 太高）

3. **语言检测被跳过**
   - 提取失败后的 fallback 路径跳过了语言检测
   - 某些错误处理分支没有调用 Step 2

4. **翻译调用失败**
   - baoyu-translate 超时或异常
   - 翻译失败后没有重试
   - 翻译失败后直接保存原文

## 修复方案（Fix）

### 1. 扩展域名启发列表

在 Step 2 中更新：

```python
ENGLISH_DOMAIN_PATTERNS = [
    # 通用英文平台
    r'medium\.com',
    r'[^.]+\.medium\.com',  # towardsdatascience.medium.com
    r'substack\.com',
    r'[^.]+\.substack\.com',

    # 技术博客
    r'[^.]+\.dev',
    r'[^.]+\.io',
    r'[^.]+\.co',
    r'blog\.[^.]+\.(com|org|net)',

    # 英文媒体
    r'nytimes\.com',
    r'wsj\.com',
    r'bbc\.com',
    r'reuters\.com',
    r'techcrunch\.com',
    r'wired\.com',
    r'theverge\.com',

    # 社交平台（英文内容为主）
    r'twitter\.com',
    r'x\.com',
    r'reddit\.com',
]

def is_likely_english_domain(url):
    """域名启发：判断是否大概率是英文内容"""
    domain = extract_domain(url)
    for pattern in ENGLISH_DOMAIN_PATTERNS:
        if re.match(pattern, domain):
            return True
    return False
```

### 2. 改进内容采样逻辑

```python
def detect_language_by_content(content, sample_size=200):
    """通过内容采样检测语言"""

    # 取前 200 词（排除引用块和代码块）
    lines = content.split('\n')
    sample_lines = []
    for line in lines:
        # 跳过引用块和代码块
        if line.startswith('>') or line.startswith('```'):
            continue
        sample_lines.append(line)
        if len(' '.join(sample_lines).split()) >= sample_size:
            break

    sample_text = ' '.join(sample_lines)

    # 统计英文词占比
    words = sample_text.split()
    english_words = 0
    for word in words:
        # 简单判断：包含英文字母且不是拼音
        if re.search(r'[a-zA-Z]', word) and not is_pinyin(word):
            english_words += 1

    english_ratio = english_words / len(words) if words else 0

    # 阈值：>50% 判定为英文
    return english_ratio > 0.5

def is_pinyin(word):
    """判断是否是拼音（简单规则）"""
    # 常见拼音模式
    pinyin_patterns = [
        r'^[bpmfdtnlgkhjqxzhchshrzcsyw]?[aeiouü]{1,2}[ng]*$',
        r'^[bpmfdtnlgkhjqxzhchshrzcsyw]?h?[aeiouü]{1,2}[ng]*$',
    ]
    word_lower = word.lower()
    for pattern in pinyin_patterns:
        if re.match(pattern, word_lower):
            return True
    return False
```

### 3. 强制语言检测

在所有提取路径中强制调用语言检测：

```python
def extract_and_save(url):
    """提取并保存（强制语言检测）"""

    # Step 1: 提取内容
    content = extract_content(url)
    if not content:
        return error("提取失败")

    # Step 2: 语言检测（强制）
    language = detect_language(url, content)

    # Step 3: 翻译（如果是英文）
    if language == 'en':
        translation = baoyu_translate(content)
        content = format_bilingual(content, translation)

    # Step 4: 保存
    save_to_clip(url, content, language)
```

### 4. 翻译失败重试

```python
def baoyu_translate_with_retry(content, max_retries=3):
    """带重试的翻译"""

    for attempt in range(max_retries):
        try:
            translation = baoyu_translate(content)
            return translation
        except TimeoutError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                # 全部失败，返回 None
                return None
        except Exception as e:
            # 其他异常，不重试
            return None

    return None
```

## 回归用例（Regression Prompts）

### 必须通过的测试

1. **Medium 文章**
   ```
   输入：剪藏 https://medium.com/@xxx/how-to-build-ai-agents
   断言：
   - 域名启发识别为英文
   - 内容采样确认
   - 调用 baoyu-translate
   - 保存双语版本（原文 + 译文）
   - frontmatter 包含 language: en
   ```

2. **Substack Newsletter**
   ```
   输入：保存 https://xxx.substack.com/p/ai-agents-2026
   断言：
   - 域名启发识别为英文
   - 调用 baoyu-translate
   - 保存双语版本
   ```

3. **技术博客（.dev 域名）**
   ```
   输入：提取 https://blog.xxx.dev/article
   断言：
   - 域名启发识别为英文
   - 调用 baoyu-translate
   - 保存双语版本
   ```

4. **中文文章（不应翻译）**
   ```
   输入：剪藏 https://mp.weixin.qq.com/s/xxx
   断言：
   - 识别为中文
   - 不调用 baoyu-translate
   - 保存原文
   ```

5. **中英混合文章**
   ```
   输入：剪藏 https://medium.com/@xxx/bilingual-article
   断言：
   - 内容采样：英文占比 > 50%
   - 调用 baoyu-translate
   - 保存双语版本
   ```

## 监控指标

- **英文域名识别率**：每周统计，目标 100%
- **英文内容检测准确率**：每周统计，目标 ≥95%
- **翻译执行率**：每周统计，目标 100%（检测到英文必须翻译）
- **翻译成功率**：每周统计，目标 ≥98%（允许 2% 重试失败）
- **用户反馈"未翻译"次数**：目标 0

## 相关案例

- `wrong-platform-routing/`：平台识别错误
- `extraction-failure/`：提取失败但未降级

## 最后更新

2026-07-15
