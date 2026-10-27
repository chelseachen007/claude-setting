---
name: workbuddy-internals-debug
description: 排查 WorkBuddy 自身内置功能（资料库/Library、连接器、Open Platform 换票、claw 推送等）报错时的诊断套路。当用户报「资料库鉴权失败」「connect_open_platform 404」「XX 功能用不了」这类产品内部错误，且需要判断是用户环境问题还是产品侧 bug 时使用。
agent_created: true
---

# WorkBuddy 内部功能排障

目标：在**不动用户环境**的前提下，把「用户配置问题 / 网络问题 / 产品侧部署缺口」三者区分开。

## 核心思路

Electron 应用的前端逻辑全在 `app.asar` 里。**报错文案 → 定位代码 → 拿到接口路径常量 → 探测候选域名 → 用 401 vs 404 判定后端是否部署了该接口。**

`401 = 接口存在但未鉴权` / `404 = 接口根本不存在`。这一个区分就能定案。

## 步骤

### 1. 复现并记录原始报错

先在**本机**复现（而不是只听用户转述），确认是不是全局问题。

```bash
# 例：Open Platform 换票
ToolSearch(tool_names: ["connect_open_platform"])
DeferExecuteTool(toolName: "connect_open_platform", params: {})
```

### 2. 从 app.asar 提取报错文案定位代码

```bash
APP="/Applications/WorkBuddy AI.app/Contents/Resources"
LC_ALL=C strings -a "$APP/app.asar" > /tmp/wb_asar_strings.txt
wc -l /tmp/wb_asar_strings.txt
grep -n -i "<报错文案的关键词>" /tmp/wb_asar_strings.txt | head -5
# 用 sed -n 'A,Bp' 读前后文，拿常量定义
sed -n '1828160,1828260p' /tmp/wb_asar_strings.txt
```

**坑**：BSD grep 的 BRE **不支持 `\|` 做或运算**，整个 pattern 会被当字面量。必须用 `-E`。
（同一个坑犯过两次，务必记住。）

注意 asar 是打包文件，`strings` 出来的代码被压平了，缩进和换行会丢——只看逻辑不纠结格式。

### 3. 找实际生效的配置值

配置不一定在 settings.json，很多在缓存的远程产品配置里：

```bash
ls -la ~/.workbuddy-ai/local_storage/
grep -o -h -E "\"[a-zA-Z]*[Ee]ndpoint\":\"[^\"]*\"" ~/.workbuddy-ai/local_storage/*.info | sort -u
```

内置 skill 的硬编码常量在：

```bash
APP/SKILLS="$APP/app.asar.unpacked/resources/plugins/workbuddy-builtin/skills"
grep -n -E "https://|_BASE|API_BASE" "$SKILLS/<skill>/_common.py"
```

### 4. 探测候选域名（决定性一步）

```bash
for h in https://www.codebuddy.ai https://www.workbuddy.cn https://www.codebuddy.cn \
         https://copilot.tencent.com https://www.workbuddy.link; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Content-Type: application/json" -d '{}' --max-time 8 \
    "$h/<接口路径>" 2>/dev/null)
  echo "$h -> $code"
done
```

### 5. 排除代理与网络

```bash
grep -n -E "http.proxy" ~/.workbuddy-ai/settings.json
env | grep -i proxy
curl -s -o /dev/null -w "%{http_code}\n" --max-time 8 https://www.workbuddy.cn
```

### 6. 检查有没有逃生舱（通常没有）

```bash
grep -n -E "resolveEndpointOverride|isDevEnvOverrideEnabled|isDevEnvSwitchBuildEnabled" /tmp/wb_asar_strings.txt
```

`dev-env.json`（`$WORKBUDDY_CONFIG_DIR/dev-env.json`）的端点覆盖在 **release 构建被关死**
（`isDevEnvSwitchBuildEnabled() { return false; }`）。别承诺用户能靠改配置解决。

### 7. 清理

```bash
rm -f /tmp/wb_asar_strings.txt   # 几百 MB，别留着
```

## 已知结论（2026-09-23 实测）

- **资料库 / Library 鉴权 404 是产品侧 bug**：海外构建（配置目录 `~/.workbuddy-ai`）
  的 `productManager.getEndpoint()` = `https://www.codebuddy.ai`，而
  `/openapi/v2/skill-token` 在该域名 **404**；在 `www.workbuddy.cn` / `www.codebuddy.cn` /
  `copilot.tencent.com` 上都是 **401**（存在）。
  同时资料库 skill 自己硬编码指向 `www.workbuddy.cn` —— **前后端不是同一个后端**。
  本地无干净解法，只能报腾讯（workbuddy@tencent.com）。
- 相关常量：`SKILL_TOKEN_API_PATH = "/openapi/v2/skill-token"`，
  实现文件 `packages/workbuddy-server/src/mcp/builtin-tools/tools/connect-open-platform-tool.ts`。

## 汇报原则

- 明确告诉用户「我这边也复现了同样的错」——区分全局问题 vs 个人环境问题，这是最有价值的一句话。
- 产品侧 bug 就直说产品侧 bug，不要编一个用户能「照着改」的方案。逃生舱被关死时如实说。
