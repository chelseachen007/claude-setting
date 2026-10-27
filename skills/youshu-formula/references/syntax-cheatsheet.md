# 有数BI 公式语法速查表

> 来源：官方文档 https://study.sf.163.com/documents/read/manual/ + 实战踩坑

## 一、IF 语句

```
IF 条件 THEN 值 ELSE IF 条件 THEN 值 ELSE 值
```

**注意：是 `ELSE IF`（两个词），不是 `ELSEIF`！**

不写 ELSE 时，不满足条件返回 NULL。不支持 `ELSE NULL` 写法（会报"字段不存在: null"），直接省略 ELSE 即可。

**⚠️ 所有场景都不要写 NULL：**
- `ELSE NULL` → 报错，直接省略 ELSE
- `IIF(条件, 值, NULL)` → 报错，改用两参数 `IIF(条件, 值)`
- `IF 条件 THEN 值 ELSE NULL` → 报错，省略 ELSE
- IF 语句中需要返回"无值"时，省略整个 ELSE 子句即可，系统自动返回 NULL
- `ISNULL()` 函数本身可以正常使用（判断是否为空）

## 二、CASE 语句

**支持的是值匹配写法，不支持 CASE WHEN 条件写法：**

```
-- ✅ 支持：按值匹配
CASE [产品ID] WHEN 1 THEN "家具" WHEN 2 THEN "电器" ELSE STR([产品ID])

-- ❌ 不支持：条件判断
CASE WHEN [金额] > 100 THEN "大" END
```

条件判断场景用 IF/ELSE IF 替代。

## 三、NULL 处理

| 函数 | 语法 | 说明 |
|------|------|------|
| `ISNULL(expr)` | `ISNULL([字段])` | 判断是否为 NULL |
| `IFNULL(expr1, expr2)` | `IFNULL([字段], 0)` | 为 NULL 时返回替代值 |
| `ZN(expr)` | `ZN([字段])` | 为 NULL 时返回 0 |

## 四、日期函数

### 提取部分
| 函数 | 语法 | 返回 |
|------|------|------|
| `YEAR(date)` | `YEAR([日期])` | 年份（整数） |
| `MONTH(date)` | `MONTH([日期])` | 月份（1-12） |
| `DAY(date)` | `DAY([日期])` | 天（1-31） |
| `DATEPART(part, date)` | `DATEPART("quarter", [日期])` | 日期指定部分 |
| `DATETRUNC(part, date)` | `DATETRUNC("month", [日期])` | 截断到指定粒度 |

### 日期运算
| 函数 | 语法 | 说明 |
|------|------|------|
| `DATEADD` | `DATEADD("month", -1, [日期])` | 日期加减 |
| `DATEDIFF` | `DATEDIFF("day", [开始], [结束])` | 日期差值（⚠️单位在第1参数） |
| `TODAY()` | `TODAY()` | 当前日期 |
| `NOW()` | `NOW()` | 当前日期时间 |

### 类型转换
| 函数 | 语法 | 说明 |
|------|------|------|
| `DATE(expr)` | `DATE("2022-10-12")` | 转为日期 |
| `DATETIME(expr)` | `DATETIME("2022-10-12")` | 转为日期时间 |
| `DATEPARSE(fmt, str)` | `DATEPARSE("yyyy-mm-dd", "2022-10-12")` | 按格式解析字符串为日期 |
| `DATEFORMAT(fmt, date)` | `DATEFORMAT("yyyy/mm/dd", [日期])` | 日期转为格式化字符串 |

> **关键：** 对 Date 类型用 LEFT/MID/RIGHT 会报错，必须用 YEAR()/MONTH()/DAY()。
> String 类型的日期才用 LEFT/MID/RIGHT 截取。
>
> **⚠️ 实战踩坑：** 有数BI中日期字段**默认是 Date 类型**，不要假设是 String。写公式前先确认字段类型。
> - Date 类型：用 `YEAR([日期])`、`DATEDIFF("day", [开始], [结束])`、`[日期] < TODAY()` 等日期函数
> - String 类型：才用 `LEFT([日期], 4)`、`DATEPARSE("yyyy-MM-dd", [日期])` 等字符串函数转换

## 五、聚合函数

| 函数 | 语法 | 说明 |
|------|------|------|
| `COUNT` | `COUNT([字段])` | 计数（不含 NULL） |
| `COUNTD` | `COUNTD([字段])` | 去重计数（不含 NULL） |
| `SUM` | `SUM([字段])` | 求和（仅数字） |
| `AVG` | `AVG([字段])` | 平均值（仅数字） |
| `MAX` | `MAX([字段])` | 最大值（数字/日期） |
| `MIN` | `MIN([字段])` | 最小值（数字/日期） |
| `MEDIAN` | `MEDIAN([字段])` | 中位数 |
| `ATTR` | `ATTR([字段])` | 所有行值相同返回该值，否则 NULL |
| `WEIGHTED_AVG` | `WEIGHTED_AVG([值], [权重])` | 加权平均 |
| `GROUP_CONCAT_DISTINCT` | `GROUP_CONCAT_DISTINCT([字段], ",")` | 去重拼接 |
| `ISTOP` | `ISTOP(SUM([字段]), "DESC", 5)` | 排名是否前 N |

### 聚合规则

行级字段和聚合函数**不能混用**：

```
-- ❌ 混用报错
[日期] = MAX([日期])

-- ✅ 两侧都聚合
ATTR([日期]) = MAX([日期])
```

除法防零：
```
IF SUM([分母]) = 0 THEN NULL ELSE (SUM([分子]) - SUM([基准])) / SUM([基准])
```

## 六、LOD 表达式

| 函数 | 语法 | 受筛选器影响 |
|------|------|-------------|
| Fixed | `{ FIXED [维度] : 聚合表达式 }` | ❌ 不受 |
| L-fixed | `{ L_FIXED [维度] : 聚合表达式 }` | ✅ 优先级低于维度筛选器 |
| Include | `{ INCLUDE [维度] : 聚合表达式 }` | ✅ 视图维度基础上额外加入 |
| Exclude | `{ EXCLUDE [维度] : 聚合表达式 }` | ✅ 从视图维度中排除 |

**典型场景 — 按公司去重汇总（粒度是地块，字段是公司级）：**
```
SUM({INCLUDE [公司] : MAX([收储目标])})
```

## 七、字符串函数

| 函数 | 语法 | 说明 |
|------|------|------|
| `CONCAT` | `CONCAT("a", "b")` | 拼接 |
| `CONTAINS` | `CONTAINS([字段], "子串")` | 包含判断 |
| `FIND` | `FIND([字段], "子串", [起始])` | 查找位置（0=未找到） |
| `LEFT` | `LEFT([字段], 4)` | 左取 N 字符 |
| `RIGHT` | `RIGHT([字段], 2)` | 右取 N 字符 |
| `SUBSTR` | `SUBSTR([字段], 1, 3)` | 截取子串 |
| `LENGTH` | `LENGTH([字段])` | 字符串长度 |
| `REPLACE` | `REPLACE([字段], "旧", "新")` | 替换 |
| `UPPER` / `LOWER` | `UPPER([字段])` | 大小写转换 |
| `LTRIM` / `RTRIM` | `LTRIM([字段])` | 去空格 |
| `SPLIT` | `SPLIT("a/b/c", "/", 1)` | 按分隔符取位 |
| `STARTSWITH` / `ENDSWITH` | `STARTSWITH([字段], "前缀")` | 前后缀判断 |
| `REGEXP_REPLACE` | `REGEXP_REPLACE([字段], "\\d", "")` | 正则替换 |
| `REGEXP_EXTRACT_NTH` | `REGEXP_EXTRACT_NTH([字段], "(\\d+)", 1)` | 正则提取第 N 组 |
| `JSON_EXTRACT` | `JSON_EXTRACT("[0].name", [JSON字段])` | JSON 提取 |
| `STR` | `STR(200)` | 转字符串 |
| `STRIFNULL` | `STRIFNULL([字段], "空")` | NULL 转字符串 |

## 八、类型转换

| 函数 | 语法 | 说明 |
|------|------|------|
| `INT(expr)` | `INT(200.6)` = 200 | 转整数（截断） |
| `FLOAT(expr)` | `FLOAT("3")` = 3.0 | 转浮点 |
| `STR(expr)` | `STR(200)` = "200" | 转字符串 |
| `DATE(expr)` | `DATE("2022-10-12")` | 转日期 |
| `DATETIME(expr)` | `DATETIME("2022-10-12 04:30:15")` | 转日期时间 |
| `DATEPARSE(fmt, str)` | `DATEPARSE("yyyy-mm-dd", [字符串])` | 按格式解析 |
| `DATEFORMAT(fmt, date)` | `DATEFORMAT("yyyy-mm-dd", [日期])` | 日期格式化 |
| `DURATION_PARSE(unit, fmt, str)` | `DURATION_PARSE("second", "mi.ss", "10.10")` | 时长解析 |

## 九、逻辑函数

| 函数 | 语法 | 说明 |
|------|------|------|
| `IF ... THEN ... ELSE IF ... THEN ... ELSE` | 条件分支 | 关键词是 ELSE IF 两词 |
| `CASE expr WHEN v1 THEN r1 ELSE default` | 值匹配 | 只支持值匹配，不支持条件 |
| `IIF(cond, true, false)` | `IIF([利润] > 0, "盈", "亏")` | 简单条件 |
| `AND` / `OR` / `NOT` | 逻辑运算 | 标准布尔运算 |
| `IFNULL(expr, default)` | `IFNULL([字段], 0)` | NULL 替代 |
| `ISNULL(expr)` | `ISNULL([字段])` | NULL 判断 |
| `ZN(expr)` | `ZN([字段])` | NULL 返回 0 |
| `MAXIMUM(a, b)` | `MAXIMUM([A], [B])` | 行级最大值 |
| `MINIMUM(a, b)` | `MINIMUM([A], [B])` | 行级最小值 |
| `MEMBER_CALC(度量, 布尔)` | `MEMBER_CALC(SUM([销售]), [地区]="东北")` | 按条件聚合 |

## 十、参数与筛选

### 参数默认值
返回具体字符串值，不返回布尔：
```
STR(YEAR(TODAY())) + "年Q" + STR(INT((MONTH(TODAY()) - 1) / 3) + 1)
```

### 季度计算
```
-- 季度编号
INT((MONTH([日期]) - 1) / 3) + 1

-- 累计季度（2026年Q1-Q2）
STR(YEAR([日期])) + "年Q1-Q" + STR(INT((MONTH([日期]) - 1) / 3) + 1)
```

### 参数联动筛选
根据参数值动态过滤（如参数值为 "2026年Q1-Q3"）：
```
YEAR([日期]) = INT(LEFT([参数], 4)) AND MONTH([日期]) <= INT(RIGHT([参数], 1)) * 3
```

## 十一、区间分类

```
IF [金额] < 500000 THEN "50万以下"
ELSE IF [金额] < 1000000 THEN "50万-100万"
ELSE IF [金额] < 2000000 THEN "100万-200万"
ELSE "200万以上"
```

## 十二、交叉表 vs 普通表格

| | 普通表格 | 交叉表 |
|--|---------|--------|
| 结构 | 行=记录，列=字段 | 行=维度A，列=维度B，交叉=度量 |
| 适合 | 明细查看 | 多维对比 |

## 十三、实战踩坑补充

### COUNTD + IIF 聚合问题

`COUNTD(IIF(条件, [字段]))` 在表格中聚合时可能不生效。解决：

```
-- 方案 A：不匹配的行返回空字符串而非省略
COUNTD(IIF(YEAR([日期]) = YEAR(TODAY()), [ID], ""))

-- 方案 B：用 FIXED 先聚合再 COUNTD
COUNTD({ FIXED [ID] : MIN(IIF(条件, [ID], "")) })

-- 方案 C：改用 SUM+IIF 计数（不去重场景）
SUM(IIF(条件, 1, 0))
```

### 文本组件 vs 图表组件的筛选器作用域

文本组件**不继承**面板/页面级筛选器，参数筛选在文本组件中可能不生效。

解决：把筛选条件写进公式内部：
```
-- ✅ 正确：筛选逻辑在公式内部，不依赖外部筛选器
SUM(IIF([日期] >= DATETRUNC("year", [参数]) AND [日期] <= [参数], [度量], 0))

-- ❌ 问题：依赖外部筛选器，文本组件中不生效
SUM([度量])
```

### 多状态分类（同一实体同时属于多个状态）

用 IF/ELSE IF 只会返回第一个匹配的状态。正确做法是为每个状态建独立的布尔标记：

```
-- 状态A标记
IIF([条件A], 1, 0)

-- 状态B标记
IIF([条件B], 1, 0)
```

然后用 SUM 聚合，一个实体可以在多个状态列同时为 1。

### 字符串日期格式转换

```
-- "202607" → 2026-07-01
DATEPARSE("yyyyMM", [字段])

-- "20260715" → 2026-07-15
DATEPARSE("yyyyMMdd", [字段])
```
