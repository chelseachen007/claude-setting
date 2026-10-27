# CDP 命令速查

前置检查：
```bash
node "/Users/chenjie/ai/skills/web-access/scripts/check-deps.mjs"
```

## 页面操作

```bash
# 打开页面（新 tab）
curl -s "http://localhost:3456/new?url=URL"
# → {"targetId":"xxx"}

# 截图
curl -s "http://localhost:3456/screenshot?target=ID&file=/tmp/shot.png"

# 滚动（触发懒加载）
curl -s "http://localhost:3456/scroll?target=ID&direction=bottom"
curl -s "http://localhost:3456/scroll?target=ID&y=3000"

# 关闭 tab
curl -s "http://localhost:3456/close?target=ID"
```

## 数据提取

```bash
# 执行任意 JS（读 DOM、提取 computed style、获取数据）
curl -s -X POST "http://localhost:3456/eval?target=ID" -d 'document.title'

# 获取单个元素的 computed style
curl -s -X POST "http://localhost:3456/eval?target=ID" -d '
(() => {
  const el = document.querySelector(".目标选择器");
  const s = window.getComputedStyle(el);
  return JSON.stringify({
    width: s.width, height: s.height,
    padding: s.padding, margin: s.margin,
    bg: s.backgroundColor, color: s.color,
    fontSize: s.fontSize, border: s.border,
    borderRadius: s.borderRadius, display: s.display,
    position: s.position
  });
})()
'

# 批量提取子元素 style
curl -s -X POST "http://localhost:3456/eval?target=ID" -d '
(() => {
  const parent = document.querySelector(".父容器");
  return JSON.stringify(Array.from(parent.querySelectorAll("*")).map(el => {
    const s = window.getComputedStyle(el);
    return { tag: el.tagName, class: el.className, ... };
  }));
})()
'
```

## 交互操作

```bash
# 点击元素
curl -s -X POST "http://localhost:3456/click?target=ID" -d '.选择器'

# 页面内导航（后退）
curl -s "http://localhost:3456/back?target=ID"
```
