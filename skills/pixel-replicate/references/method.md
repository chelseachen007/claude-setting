# 像素级复刻方法论

## Phase 1: 抓取目标页面（DOM 优先）

### 第一步：提取 DOM 树结构（最重要！）

DOM 结构是唯一真相来源。截图可能被反爬/缓存误导。

```bash
# 打开目标页面
curl -s "http://localhost:3456/new?url=<URL>"

# 等待加载（反爬站点多等几秒）
sleep 5

# 提取主容器 DOM 树（限制深度避免过大）
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d '
(() => {
  function getDomTree(el, depth) {
    if (depth > 6) return null;
    const children = Array.from(el.children).map(c => getDomTree(c, depth + 1)).filter(Boolean);
    const cls = el.className && typeof el.className === "string" ? el.className.trim().substring(0, 60) : "";
    const text = el.children.length === 0 ? el.textContent.trim().substring(0, 50) : "";
    const result = { tag: el.tagName.toLowerCase(), cls: cls };
    if (text && text.length > 0) result.text = text;
    if (children.length > 0) result.children = children;
    return result;
  }
  const main = document.querySelector(".main") || document.querySelector(".content") || document.body.firstElementChild;
  return JSON.stringify(getDomTree(main, 0), null, 2);
})()
'
```

### 第二步：截图（仅作视觉辅助）

```bash
curl -s "http://localhost:3456/screenshot?target=<ID>&file=/tmp/target-full.png"
```

### 第三步：提取关键区域的文本和标签信息

```bash
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d '
(() => {
  const tabs = Array.from(document.querySelectorAll("[class*=tab] li, .monitor_tab li")).map(li => li.textContent.trim());
  const tables = Array.from(document.querySelectorAll("table")).slice(0, 3).map(table => {
    const rows = Array.from(table.querySelectorAll("tr")).slice(0, 5).map(tr =>
      Array.from(tr.querySelectorAll("td")).map(td => td.textContent.trim().substring(0, 40))
    );
    return rows;
  });
  const btns = Array.from(document.querySelectorAll("button, [class*=btn]")).slice(0, 5).map(el => el.textContent.trim().substring(0, 30));
  return JSON.stringify({ tabs, tables, btns }, null, 2);
})()
'
```

### 反爬处理（优先级从高到低）

1. **优先：提醒用户手动处理** — 告知用户"页面触发了反爬验证，请在你的浏览器中完成验证，完成后告诉我继续"。用户完成后刷新页面重新提取。
2. 换 URL 路径 — 如 `/history/prjs/` vs `/prjs/`，有些路径有效有些无效
3. 找同类有效页面 — 用列表页找到一个有效详情页作为参考
4. 利用已有数据 — 如果之前截图/DOM 有内容，从中提取可用信息
5. 问用户提供截图 — 让用户提供他们看到的真实页面截图

## Phase 2: 提取精确 CSS 值

对每个组件，用 `/eval` 提取 computed style。必须提取的属性：

```
width, height, padding, margin, border, border-radius,
background-color, color, font-size, font-weight, line-height,
display, position, top/left/right/bottom, float, z-index,
text-align, text-decoration, overflow, cursor
```

### 按区域提取清单

| 区域 | 选择器示例 | 重点属性 |
|------|-----------|---------|
| 筛选面板 | `.prop_bg`, `.filter_item`, `.filter_item.current` | padding, margin, border, bg, border-radius |
| 排序栏 | `.sort_bar`, `.sort_item`, `.sort_sth` | height, line-height, border, position |
| 列表项 | `.prj_li_cls` 及其所有子元素 | position(absolute!), width, left, top |
| 状态标签 | `.state`, `.state_limite` 等 | border-radius, bg, z-index |
| 价格列 | `.price_start`, `.price_limite`, `.price_num` | position, left, color |
| 分页器 | `.layui-laypage` 及子元素 | display, margin(负边框合并!), border |
| 视图切换 | `.sort_sth_grid`, `.sort_sth_bar` | width, height, SVG icon |

### 批量提取列表项内部结构

```bash
curl -s -X POST "http://localhost:3456/eval?target=<ID>" -d '
(() => {
  const li = document.querySelector(".目标选择器");
  return JSON.stringify(Array.from(li.querySelectorAll("*")).map(el => {
    const s = window.getComputedStyle(el);
    return {
      tag: el.tagName, class: el.className,
      text: el.textContent.trim().substring(0, 30),
      position: s.position, display: s.display, float: s.float,
      width: s.width, height: s.height, top: s.top, left: s.left,
      fontSize: s.fontSize, color: s.color, bg: s.backgroundColor,
      padding: s.padding, margin: s.margin, borderRadius: s.borderRadius
    };
  }));
})()
'
```

## Phase 3: 对比现有代码

1. 读取现有页面文件，理解当前结构
2. **先对比 DOM 树结构**（层级、嵌套关系），再对比 CSS 值
3. 逐项对比，输出差异清单表格：

```
| # | 属性 | 目标值 | 现有值 | 差距说明 |
|---|------|--------|--------|---------|
```

3. **向用户展示差异清单，确认后再动手**

## Phase 4: 实施修改

CSS 修改优先级：
1. DOM 结构（层级、嵌套关系）
2. 布局容器（宽度、居中方式）
3. 主色调变量（SCSS 变量统一管理）
4. 各区域组件
5. 响应式断点

### CSS 注意事项

- CSS 属性用 kebab-case（`max-width`，不是 `maxWidth`）
- class 名按项目规范（本项目用小驼峰）
- Vue 的 `v-show`/`v-if` 不能与 CSS 的 `display` 属性冲突
- scoped 样式穿透子组件用 `::v-deep`

## Phase 5: 验证

1. 编译检查
2. 截图对比（如有 dev server）
3. DevTools 逐项复查 computed style
