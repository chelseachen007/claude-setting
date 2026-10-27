# 常见坑点速查

## 布局类

| 坑 | 原因 | 解法 |
|----|------|------|
| 列表项元素重叠 | position: absolute 的 left/top 值不对 | 必须从 computed style 提取精确值 |
| 排序项被挤到下一行 | 右侧工具栏 float 挤占空间 | 右侧改 `position: absolute; right: 0` |
| 文字意外换行 | 容器宽度不够或缺 white-space | `white-space: nowrap` |
| 内容区不居中 | 用 calc(100%-40px) 而非固定宽度+margin auto | 改为 `width: 1200px; margin: 0 auto` |
| **布局结构推断错误** | 仅凭截图推断为两栏布局，实际是单栏上下结构 | **必须先提取 DOM 树确认结构，截图仅作视觉参考** |

## 层级类

| 坑 | 原因 | 解法 |
|----|------|------|
| 状态标签被图片遮盖 | 缺少 z-index | `.state { z-index: 10 }` |
| 下拉菜单被遮挡 | 父容器 overflow: hidden | 检查祖先元素的 overflow 设置 |

## Vue 指令冲突类

| 坑 | 原因 | 解法 |
|----|------|------|
| **v-show 切换无效，Tab 内容全部隐藏** | CSS `> li { display: none }` 优先级高于 v-show 生成的内联样式 | 删除 CSS 中的 display 规则，让 v-show 完全控制显隐 |
| v-if 元素仍占位 | CSS 设置了 `visibility: hidden` 而非 `display: none` | 用 v-show 或确保 CSS 不干扰 |

## 分页器类

| 坑 | 原因 | 解法 |
|----|------|------|
| 边框变粗 | 没有用负 margin 合并相邻边框 | `display: inline-block; margin: 0 -1px 5px 0` |
| inline-block 间隙 | HTML 空白字符产生 4px 间隙 | 父容器 `font-size: 0`，子元素重设 font-size |
| 当前页指示不明显 | 用了整块蓝底，目标是蓝底或底部指示条 | 先提取 computed style 确认再实现 |

## 样式穿透类

| 坑 | 原因 | 解法 |
|----|------|------|
| 子组件样式不生效 | scoped 样式无法穿透 | 用 `::v-deep` 前缀 |
| el-image 对象填充不对 | 默认 object-fit 不符合预期 | `::v-deep .el-image__inner { object-fit: fill }` |

## CSS 命名类

| 坑 | 原因 | 解法 |
|----|------|------|
| **CSS 属性用了驼峰** | 写成 `maxWidth: 1200px` 而非 `max-width: 1200px` | CSS 属性必须用 kebab-case，class 名按项目规范（本项目用小驼峰） |

## 数据/反爬类

| 坑 | 原因 | 解法 |
|----|------|------|
| 目标页面内容为空 | 需要登录态或动态加载 | CDP 带登录态 + scroll 触发懒加载 |
| class 名和目标不一致 | 用了驼峰而目标用下划线 | 以 computed style 为准，不看 class 名 |
| **页面显示"页面未找到"但截图有内容** | 反爬机制拦截自动化访问，截图可能是缓存 | **优先提醒用户在浏览器中完成验证**；不行再换 URL / 找同类页面 |
| **DOM 无元素但截图有内容** | SPA 框架内容未加载完成就截图 | 等待更长时间 / 检查 shadowRoot / 用 eval 确认 DOM 状态 |
