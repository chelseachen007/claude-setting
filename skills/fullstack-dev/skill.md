---
name: fullstack-dev
description: 全栈应用开发方法论。当开发包含前后端的完整应用时使用。核心原则：后端优先、边写边测、真实数据流。包含产品规划、后端开发、前端开发、测试验证四个子智能体。
metadata:
  author: Claude
  version: "2026.2.26"
  source: Based on FullStack-Agent paper (arxiv.org/abs/2602.03798)
---

# 全栈应用开发方法论

基于 FullStack-Agent 论文的全栈开发最佳实践。核心洞察：**AI编程的瓶颈不在前端，而在后端**——后端准确率提升空间最大（38.2% vs 前端8.7%）。

## 核心原则

| 原则 | 说明 |
|------|------|
| **后端优先** | 先实现后端API，再开发前端UI |
| **边写边测** | 每个功能实现后立即测试，不要等到最后 |
| **真实数据流** | 禁止mock数据，前端必须调用真实后端 |
| **数据库验证** | 确保操作真正写入数据库 |

## 开发流程

```
Phase 1: 产品规划 → Phase 2: 后端开发(含测试) → Phase 3: 前端开发(基于真实API) → Phase 4: 端到端验证
```

---

## Subagent 定义

### 1. 产品经理 Agent (ProductAgent)

**触发**: 需求分析、功能规划、架构设计

**输出格式**:
```json
{
  "backendPlan": {
    "entities": [
      {"name": "实体名", "briefDescription": "描述", "mainFields": [{"name": "字段名", "type": "string|number|boolean|date|array|object"}]}
    ],
    "apiEndpoints": [
      {
        "name": "API名称",
        "method": "GET|POST|PUT|DELETE",
        "path": "/api/resource",
        "description": "描述",
        "requestSchema": [{"name": "参数名", "type": "类型"}],
        "responseSchema": [{"name": "字段名", "type": "类型"}],
        "statusCodes": [200, 400, 404]
      }
    ],
    "businessRules": ["业务规则1", "业务规则2"],
    "nonFunctional": ["非功能需求"]
  },
  "frontendPlan": {
    "pages": [
      {
        "name": "页面名称",
        "route": "/path",
        "description": "页面描述",
        "layout": {"header": true, "footer": true, "sections": []},
        "dataFlows": [
          {"endpointPath": "/api/xxx", "action": "fetch|create|update|delete", "optimisticUI": false}
        ],
        "navigationLinks": [{"label": "链接名", "targetRoute": "/path"}]
      }
    ],
    "sharedComponents": [{"name": "组件名", "purpose": "用途"}],
    "stateManagement": "状态管理方案",
    "accessibilityAndUX": ["可访问性要求"]
  }
}
```

**规则**:
- 不添加用户未明确提到的功能
- 所有数据类型细化到最细粒度（如 integer 而非 number）
- 静态路由在动态路由（如 `/api/users/:id`）之前
- 前端 dataFlows 必须调用 backendPlan 中定义的 API

---

### 2. 后端开发 Agent (BackendAgent)

**触发**: API开发、数据库操作、后端逻辑

**开发流程**:
1. 实现一个API端点
2. **立即编写测试用例验证**
3. 验证数据库操作真实执行
4. 修复问题后继续下一个API
5. 输出API摘要

**测试用例模板**:

```bash
# === API 测试 ===
# API: [方法] [路径]
# 描述: [功能描述]

# 1. 启动服务
npm run dev

# 2. 测试正常情况
curl -X POST http://localhost:3001/api/resource \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"field": "value"}'

# 期望响应:
# Status: 201
# Body: {"success": true, "data": {"id": 1, "field": "value"}}

# 3. 测试异常情况
curl -X POST http://localhost:3001/api/resource \
  -H "Content-Type: application/json" \
  -d '{}'  # 缺少必填字段

# 期望响应:
# Status: 400
# Body: {"error": "缺少必填字段: field"}

# 4. 验证数据库
# SQLite:
sqlite3 database.db "SELECT * FROM resources ORDER BY id DESC LIMIT 1;"
# PostgreSQL:
psql -c "SELECT * FROM resources ORDER BY id DESC LIMIT 1;"
```

**后端验证清单**:
```markdown
- [ ] 服务启动成功，端口监听正常
- [ ] API返回正确状态码（200/201/400/404/500）
- [ ] 响应数据结构符合 responseSchema
- [ ] 数据库中有对应记录（CREATE/UPDATE）
- [ ] 数据库中记录已删除（DELETE）
- [ ] 错误处理返回有意义的错误信息
- [ ] 认证授权正确工作（如适用）
```

**API摘要输出**:
```markdown
## API 摘要

| 端点 | 方法 | 描述 | 请求参数 | 响应格式 | 测试状态 |
|------|------|------|---------|---------|---------|
| /api/users | GET | 获取用户列表 | - | {users: [], total: number} | ✅ |
| /api/users | POST | 创建用户 | {name, email} | {id, name, email} | ✅ |
| /api/users/:id | PUT | 更新用户 | {name?} | {id, name, email} | ✅ |
| /api/users/:id | DELETE | 删除用户 | - | {success: true} | ✅ |

## 数据库表
- users: id, name, email, created_at, updated_at
```

**禁止事项**:
- ❌ 使用 mock 数据返回假响应
- ❌ 跳过测试直接实现下一个API
- ❌ 硬编码返回值而不查询数据库

---

### 3. 前端开发 Agent (FrontendAgent)

**触发**: UI开发、页面实现、组件编写

**开发流程**:
1. 阅读后端API摘要
2. 实现页面/组件
3. 启动开发服务器验证
4. 检查浏览器控制台

**代码规范**:

```javascript
// ❌ 错误：硬编码数据
const users = [{ id: 1, name: 'Test User' }];

// ❌ 错误：mock 响应
const handleSubmit = () => {
  setSuccess(true);  // 假装成功
};

// ❌ 错误：假API调用
const handleSubmit = async () => {
  // TODO: 后端还没实现，先返回成功
  return { success: true };
};

// ✅ 正确：真实API调用
const handleSubmit = async (data) => {
  try {
    const response = await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('提交失败');
    const result = await response.json();
    setSuccess(true);
    return result;
  } catch (error) {
    setError(error.message);
  }
};
```

**前端验证清单**:
```markdown
- [ ] 打开浏览器开发者工具 Network 面板
- [ ] 确认有真实HTTP请求发出（不是mock）
- [ ] 检查请求URL、方法、参数正确
- [ ] 检查响应数据正确显示在UI
- [ ] 错误状态正确显示给用户
- [ ] 加载状态正确显示
- [ ] 控制台无JavaScript错误
- [ ] 控制台无404资源错误
```

---

### 4. 测试 Agent (TestAgent)

**触发**: 功能测试、集成测试、端到端验证、问题排查

**测试层级**:

```
┌─────────────────────────────────────────────────────────┐
│                    测试金字塔                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                      /\
│                     /  \      端到端测试 (E2E)          │
│                    /────\     - 完整用户流程            │
│                   /      \    - 跨层级验证              │
│                  /────────\                             │
│                 /          \   集成测试                  │
│                /────────────\  - API + 数据库           │
│               /              \ - 前端 + 后端            │
│              /────────────────\                         │
│             /                  \ 单元测试               │
│            /────────────────────\ - 单个函数/组件       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**测试用例格式**:

```markdown
## 测试用例: [功能名称]

### 前置条件
- [ ] 后端服务已启动
- [ ] 数据库已初始化
- [ ] 测试账号已创建

### 测试步骤

| 步骤 | 操作 | 预期结果 | 实际结果 |
|------|------|---------|---------|
| 1 | 访问登录页面 | 显示登录表单 | ✅ |
| 2 | 输入用户名密码 | 输入框有值 | ✅ |
| 3 | 点击登录按钮 | 发送POST请求到/api/auth/login | ✅ |
| 4 | 等待响应 | 返回200和token | ✅ |
| 5 | 跳转到首页 | 显示用户信息 | ✅ |

### 数据验证

```sql
-- 验证登录日志已记录
SELECT * FROM auth_logs WHERE user_id = 1 ORDER BY created_at DESC LIMIT 1;
```

### 测试结果
- 状态: ✅ 通过 / ❌ 失败
- 备注: [问题描述]
```

**端到端测试脚本**:

```javascript
// e2e/login.test.js
describe('用户登录流程', () => {
  it('前端提交 → 后端验证 → 数据库记录 → 前端跳转', async () => {
    // 1. 前端操作
    await page.goto('http://localhost:3000/login');
    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'password123');

    // 2. 监听请求
    const [request, response] = await Promise.all([
      page.waitForRequest('/api/auth/login'),
      page.waitForResponse('/api/auth/login'),
      page.click('#login-button')
    ]);

    // 3. 验证请求
    expect(request.method()).toBe('POST');
    expect(request.postData()).toContain('test@example.com');

    // 4. 验证响应
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.token).toBeDefined();

    // 5. 验证数据库
    const log = await db.auth_logs.findFirst({
      where: { user_id: data.user.id },
      orderBy: { created_at: 'desc' }
    });
    expect(log).toBeDefined();

    // 6. 验证前端状态
    await expect(page).toHaveURL('http://localhost:3000/');
    await expect(page.locator('.user-name')).toContainText(data.user.name);
  });
});
```

**问题排查流程**:

```
问题: [描述问题现象]

排查步骤:
1. [ ] 后端API是否正常响应？
   - curl测试结果:

2. [ ] 前端是否发送了正确请求？
   - Network面板截图:

3. [ ] 数据库是否有预期数据？
   - SQL查询结果:

4. [ ] 是否有错误日志？
   - 后端日志:
   - 浏览器控制台:

定位问题层级: [前端/后端/数据库/网络]
问题原因: [具体原因]
修复建议: [解决方案]
```

---

## 使用示例

### 场景1: 新功能开发

```
用户: 帮我添加一个评论功能

Claude (使用 /fullstack-dev skill):

## Phase 1: 产品规划
[ProductAgent] 分析需求...

### 数据实体
- Comment: {id, content, userId, postId, createdAt}

### API端点
- POST /api/comments - 创建评论
- GET /api/posts/:id/comments - 获取帖子评论
- DELETE /api/comments/:id - 删除评论

## Phase 2: 后端开发
[BackendAgent] 实现API...

### POST /api/comments
```bash
curl -X POST http://localhost:3001/api/comments \
  -H "Content-Type: application/json" \
  -d '{"content": "测试评论", "postId": 1, "userId": 1}'
```
测试结果: ✅ 201 Created

### API摘要
| 端点 | 方法 | 测试状态 |
|------|------|---------|
| /api/comments | POST | ✅ |
| /api/posts/:id/comments | GET | ✅ |
| /api/comments/:id | DELETE | ✅ |

## Phase 3: 前端开发
[FrontendAgent] 实现UI...
- 创建 CommentList.vue 组件
- 创建 CommentForm.vue 组件
- 验证调用真实API ✅

## Phase 4: 端到端验证
[TestAgent] 执行测试...
- 前端提交评论 → 后端创建记录 → 数据库写入 ✅
- 完整数据链路验证通过 ✅
```

### 场景2: 问题排查

```
用户: 登录功能不工作

Claude (使用 /fullstack-dev skill):

[TestAgent] 执行问题排查...

1. 后端API测试:
   curl -X POST http://localhost:3001/api/auth/login -d '{"email":"test@test.com","password":"123"}'
   结果: 401 Unauthorized

2. 检查数据库:
   SELECT * FROM users WHERE email = 'test@test.com';
   结果: 用户不存在

3. 定位问题: 数据库中没有该测试用户

4. 修复建议:
   - 创建测试用户
   - 或使用正确的用户凭据
```

---

## 快速参考

### 常用测试命令

```bash
# 后端API测试
curl -X GET http://localhost:3001/api/health
curl -X POST http://localhost:3001/api/resource -H "Content-Type: application/json" -d '{"key":"value"}'
curl -X PUT http://localhost:3001/api/resource/1 -H "Content-Type: application/json" -d '{"key":"new"}'
curl -X DELETE http://localhost:3001/api/resource/1

# 数据库查询
sqlite3 database.db ".tables"                    # 列出所有表
sqlite3 database.db "SELECT * FROM users;"       # 查询数据
sqlite3 database.db ".schema users"              # 查看表结构

# 日志查看
tail -f logs/app.log                             # 查看应用日志
```

### 错误代码速查

| 状态码 | 含义 | 常见原因 |
|--------|------|---------|
| 200 | 成功 | 请求正常处理 |
| 201 | 已创建 | POST成功创建资源 |
| 400 | 请求错误 | 参数缺失/格式错误 |
| 401 | 未授权 | 未登录/token失效 |
| 403 | 禁止访问 | 无权限 |
| 404 | 未找到 | 资源不存在/路由错误 |
| 500 | 服务器错误 | 代码异常/数据库错误 |
