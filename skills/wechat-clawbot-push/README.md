# wechat-clawbot-push

通过 WorkBuddy 已绑定的「微信 ClawBot」(腾讯 iLink bot) 把**文本主动推送**到用户自己的个人微信。

当你想让一个 AI 助手 / 自动化任务 / 定时脚本，**把消息、日报、提醒直接发到你个人微信**（而不是只停留在 WorkBuddy App 内）时，用这个 skill。

- ✅ 个人微信，非企业微信、非公众号
- ✅ 纯 Python 标准库，零第三方依赖
- ✅ 跨平台（macOS / Linux / Windows）
- ✅ 跨宿主：WorkBuddy 自动读配置；Codex / Claude Code 用环境变量或独立配置文件
- ✅ 源码不含任何凭据，开箱即用、可安全开源

---

## 核心机制（本 skill 的精华）

微信个人号没有官方群发 API。但 WorkBuddy 的「微信 ClawBot」是一个**绑定到你本人账号**的 iLink 机器人：

> 对「用户自己绑定的 ClawBot」，`POST /ilink/bot/sendmessage` 携带 `botToken`、按 `userId`，
> **用空 `context_token` 即可直接推送本人**，不需要先让用户在微信给 ClawBot 发一条 inbound 消息来"种"令牌。

社区里常见的 clawbot-notify 脚本坚持要先 `getupdates` harvest `context_token`，那一步在本场景下**是多余的**——因为 ClawBot 是用户自有 channel，bot 对自己的绑定用户有推送权限；`context_token` 只在"给任意陌生用户回消息"时才必须。

---

## 安装 / 加载

把整个 `wechat-clawbot-push/` 目录放到你的 agent skills 目录下即可（各平台写法见下方）。无需 `pip install`。

- WorkBuddy：`~/.workbuddy/skills/wechat-clawbot-push/`
- Codex：`~/.codex/skills/wechat-clawbot-push/`
- Claude Code：`~/.claude/skills/wechat-clawbot-push/`
- 其它遵循 Agent Skills 规范的工具：对应 `skills/` 目录

（常见做法是把真实目录放在 `~/.agents/skills/`，再软链到上面各处。）

## 前置条件

必须先在 **WorkBuddy App** 里绑定并启用微信 ClawBot（设置 → 通道）。未绑定时 `status` 会明确报错。

## 凭据来源（按优先级自动发现，源码不含任何密钥）

1. **环境变量**（适合 Codex / Claude Code / 容器 / CI）：
   `CLAWBOT_BOT_TOKEN`、`CLAWBOT_BASE_URL`、`CLAWBOT_USER_ID`（可选 `CLAWBOT_CHANNEL_ID`）。
2. **WorkBuddy 宿主**：自动读 `~/.workbuddy/settings.json` 的
   `claw.users[legacyOwnerUid].channels.weixinClawBot`。
3. **独立配置文件** `~/.clawbot/config.json`：`{"botToken":..., "baseUrl":..., "userId":...}`。

三者之一齐备即可。在 WorkBuddy 上通常**什么都不用配**。

## 用法

```bash
# macOS / Linux
python3 scripts/send_wechat.py send "你的消息内容"      # 发文本（超长自动分条）
python3 scripts/send_wechat.py send --file 报告.md     # 读文件全文发送（自动分条）
python3 scripts/send_wechat.py status                  # 查看绑定/凭据状态（只读，已脱敏）
python3 scripts/send_wechat.py refresh                 # 可选：轮询取 context_token（多数情况不需要）

# Windows（PowerShell / CMD）：用 py 或 python 代替 python3
py scripts/send_wechat.py send "你的消息内容"
```

`status` 输出中的 `userId` / `channelId` 已被脱敏（仅显示首尾），避免误贴到公开渠道泄露标识。`botToken` 永不打印。

## 在自动化里集成（示例）

```
报告生成后，用 wechat-clawbot-push 技能把报告推到用户微信：
  python3 <skill_dir>/scripts/send_wechat.py send --file ./日报.md
若发送失败（返回非 0），回退到其他通道（如飞书 bot）推送，确保不丢报告。
```

## 局限与注意

- **仅文本**：不发文件加密上传（iLink 文件上传需 AES+CDN，易碎且非必要）。长文会自动拆成多条微信消息。
- **需要 WorkBuddy 在线 + 机器不休眠**：定时自动化触发时，宿主进程必须运行。
- **冷启动**：空 token 直发在 WorkBuddy App 有活跃会话时稳定；长期无交互后的"首条"若失败，脚本会自动回退空串重试一次。极端情况下可让用户给 ClawBot 发任意一条消息"激活"会话。
- **合规**：只推用户本人，不群发、不骚扰；用于个人提醒/报告场景。

## License

[MIT](LICENSE)
