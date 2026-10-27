---
name: wechat-clawbot-push
description: 通过 WorkBuddy 已绑定的「微信 ClawBot」(iLink bot) 把文本主动推送到用户个人微信。当用户/自动化想把消息、通知、日报、报告等主动送达用户的个人微信（而非仅停留在 WorkBuddy App 内）时使用。支持跨平台：WorkBuddy 自动读取 settings.json；Codex/Claude Code 等无 WB 宿主时用环境变量或 ~/.clawbot/config.json 提供凭据。纯标准库，无需第三方依赖。
agent_created: true
---

# wechat-clawbot-push（微信 ClawBot 主动推送）

把文本主动推送到**用户自己的个人微信**，通过 WorkBuddy 内置的「微信 ClawBot」通道（腾讯 iLink 机器人接口）。

## 什么时候用

- 自动化/定时任务产出的报告、提醒、摘要，需要**直接进用户微信**（而不是只在 App 里）。
- 任何需要"从程序主动发一条微信给用户"的场景。
- 注意：这是**个人微信**推送，走的是 WorkBuddy 绑定的 ClawBot，不是企业微信、不是公众号。

## 核心机制（重要，省掉一个坑）

微信个人号没有官方群发 API。但 WorkBuddy 的 ClawBot 是一个**绑定到用户账号**的 iLink 机器人：
通过 `POST /ilink/bot/sendmessage` 携带 `botToken`，按 `userId` 即可把消息推到该用户本人的微信。

**关键实测结论（本 skill 的精华）：**
> 对「用户自己绑定的 ClawBot」，`sendmessage` 用**空 `context_token`** 就能直接推送本人，
> **不需要**先让用户在微信给 ClawBot 发一条 inbound 消息来"种"令牌。
> 社区里常见的 clawbot-notify 脚本坚持要先 harvest `context_token`，那一步在本场景下是多余的。

为什么空 token 能发：ClawBot 是用户自有 channel，bot 对自己的绑定用户有推送权限；`context_token` 只在"bot 给任意陌生用户回消息"时才必须。

## 凭据来源（按优先级，跨平台）

1. **环境变量**（适合 Codex / Claude Code / 容器 / CI）：
   `CLAWBOT_BOT_TOKEN`、`CLAWBOT_BASE_URL`、`CLAWBOT_USER_ID`（可选 `CLAWBOT_CHANNEL_ID`）。
2. **WorkBuddy 宿主**：自动读 `~/.workbuddy/settings.json` 的
   `claw.users[legacyOwnerUid].channels.weixinClawBot`（含 baseUrl/botToken/userId/enabled）。
3. **独立配置文件** `~/.clawbot/config.json`：`{"botToken":..., "baseUrl":..., "userId":...}`。

只要三者之一齐备即可。**在 WorkBuddy 上通常什么都不用配**——只要用户在 App 里绑定并启用了 ClawBot。

## 用法

```bash
# 发文本（超长自动分条）
python3 <skill_dir>/scripts/send_wechat.py send "你的消息内容"

# 发文件内容（读取 markdown/txt 全文发送，自动分条）
python3 <skill_dir>/scripts/send_wechat.py send --file 报告.md

# 查看凭据/绑定状态（只读）
python3 <skill_dir>/scripts/send_wechat.py status

# 可选：轮询取 context_token（多数情况不需要，空 token 已能发）
python3 <skill_dir>/scripts/send_wechat.py refresh
```

`<skill_dir>` = 本 skill 所在目录。WorkBuddy/Codex/Claude 加载 skill 后可直接引用其绝对路径。

### 跨平台调用

- **macOS / Linux**：`python3 <skill_dir>/scripts/send_wechat.py ...`
- **Windows（PowerShell / CMD）**：Windows 通常没有 `python3` 命令，改用 `py` 或 `python`：
  ```powershell
  py <skill_dir>\scripts\send_wechat.py send "你的消息"
  # 或 python <skill_dir>\scripts\send_wechat.py status
  ```
  脚本本身纯标准库、显式 `encoding="utf-8"`、路径用 `os.path.expanduser`，**不依赖任何 Unix 专有 API**，在 Windows 上可直接运行（已做平台无关处理；欢迎在 Windows 实测后反馈）。


## 在自动化里集成（示例 prompt 片段）

```
报告生成后，用 wechat-clawbot-push 技能把报告推到用户微信：
  python3 <skill_dir>/scripts/send_wechat.py send --file ./日报.md
若发送失败（返回非 0），回退到飞书(lark-im) bot 推送，确保不丢报告。
```

## 局限与注意

- **仅文本**：不发文件加密上传（iLink 文件上传需 AES+CDN，易碎且非必要）。长文会自动拆成多条微信消息。
- **需要 WorkBuddy 在线 + 机器不休眠**：定时自动化触发时，宿主进程必须运行，否则不会执行。
- **冷启动**：空 token 直发在 WorkBuddy App 有活跃会话时稳定；长期无交互后的"首条"若失败，脚本会自动回退空串重试一次。极端情况下可让用户给 ClawBot 发任意一条消息"激活"会话。
- **绑定要求**：必须先在 WorkBuddy App 里绑定并启用微信 ClawBot（设置 → 通道）。未绑定时 `status` 会明确报错。
- **合规**：只推用户本人，不群发、不骚扰；用于个人提醒/报告场景。
