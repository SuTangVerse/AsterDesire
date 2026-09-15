# 接入与部署建议

## 与 LLM 解耦

把 `HeartbeatDecision` 和经过裁剪的状态作为上下文交给任意模型。模型返回的结果应先解析成结构化状态，再交给 `record_result`。不要允许模型直接修改状态文件或心跳调度配置。

建议结果协议：

```json
{
  "status": "sent | completed | silent | skipped | failed",
  "reason": "bounded human-readable note"
}
```

`silent` 是正常选择；`skipped` 表示暂时不想做当前动作；`failed` 只用于真实执行错误。

## 与 Bot 解耦

发送器应独立实现：

- 私聊与群聊权限检查；
- 接收者白名单；
- 发送频率限制；
- 消息去重；
- Markdown/媒体转义；
- 平台失败重试。

本引擎不接受 Token，也不直接访问 Telegram、Discord 或邮件。

## 调度

可以每分钟由现有服务检查 `next_wake_at`，到期后调用 `AgentRuntime.wake()`。如果系统已有调度器，不要再创建第二套重复定时器。

多进程部署需要把 `JsonStateStore` 换成支持事务的数据库；当前文件锁适合单机、少量进程。

## 权限

推荐拆分为三个身份：

1. 状态服务：只读写 Desire/Pulse 状态；
2. Agent runner：读取裁剪后的上下文，不能读取凭据；
3. Sender：只接受审核后的目标和消息，持有最小发送权限。

这样 libido、Pulse 或模型输出都不能自行越权成为外部动作。
