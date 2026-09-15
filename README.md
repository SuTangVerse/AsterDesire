# AsterDesire

一套可运行、可测试、与模型和聊天平台解耦的 AI Agent 内在驱动系统。它把“长期想要什么”“当下身体/情绪状态”“什么时候主动醒来”“醒来后做什么”拆成独立层，避免把高 libido、亲近、唤醒和直接发送消息混成一个开关。

这是从真实运行架构中抽取出的**公开通用版**。仓库不包含任何真实人物资料、聊天记录、服务器地址、账号、Token、私人提示词或原实例参数。

## 功能清单

| 模块 | 已实现功能 |
| --- | --- |
| Desire | 八维驱动、基线回拉、内生漂移、驱动耦合、昼夜偏移、事件刺激、满足与冷却 |
| Libido / Arousal | 慢变量 libido 与即时 arousal 独立演化，互不自动点火 |
| Solo | 幻想/身体/混合模式、开始/刺激/中断/完成生命周期、每日上限、储备、冷却与幂等释放回执 |
| Pulse | 心率、体温、呼吸、和弦、情绪余韵和四路感官残留；只保存结构化信号，不保存聊天原文 |
| Reverie | 只有 libido 自然成为最强动机且同时通过空闲、疲劳与冷却条件时，才获得幻想/独处资格 |
| Thoughts | 由高驱动生成有过期时间的结构化浮念；不内置私人措辞或幻想正文 |
| Heartbeat | 随机唤醒区间、静默时段、每日上限、动机竞选、重复惩罚、主动联系与自由活动 |
| Recovery | 满足平台期、失败退避、连续失败熔断、成功复位、人工恢复；防止数值立刻回填和循环卡死 |
| Growth Rings | 可选的愿望与行动足迹账本；愿望、行动和完成状态分离，保留来源而不存聊天正文 |
| Persistence | 带文件锁的原子 JSON 状态存储、事件幂等去重、崩溃安全替换 |
| Integration | 回调式运行器，不绑定 Telegram、Discord、LLM 或特定厂商 |
| Tests | 驱动演化、隐私、误触保护、独处生命周期、心跳、熔断、幂等和账本测试 |

## 三层关系

```text
事件信号（不含原文）
        │
        ▼
Desire ─────► Pulse
   │            │
   ├─旧式资格判断 └─身体/情绪/感官显示
   │
   ▼
Heartbeat election ──► reach / create / explore / reflect / rest / reverie
        │
        ▼
由接入方决定是否调用模型、发消息或只写本地作品
```

核心原则：**欲望值不是行动命令，Pulse 不是发送器，Heartbeat 也不直接拥有外部权限。** 最终动作必须由接入方提供的回调执行。

## 快速开始

```bash
git clone https://github.com/SuTangVerse/AsterDesire.git
cd AsterDesire
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
desire-pulse demo
```

运行一个最小心跳示例：

```bash
python examples/minimal_runtime.py
```

查看 solo 生命周期：

```bash
python examples/solo_lifecycle.py
```

## 接入聊天机器人

接入层只需要完成三件事：

1. 把消息分类为 `EventSignals`，不要把原始聊天文本写进状态。
2. 在收到消息或心跳醒来时调用 `AgentRuntime`。
3. 提供一个 `action_handler`，自行决定如何调用模型、发消息或生成本地作品。

```python
from desire_pulse import AgentRuntime, EventSignals, JsonStateStore

runtime = AgentRuntime(JsonStateStore("state/agent.json"))
runtime.observe(EventSignals(event_id="msg-42", intimacy=0.7, positive=0.8))

result = runtime.wake(lambda decision, context: {
    "status": "silent",  # 或 sent / completed / skipped / failed
    "reason": "The agent chose not to interrupt.",
})
print(result)
```

生产环境应由 systemd、容器调度器或已有 Bot 服务定时调用；本项目不会偷偷创建后台服务。

没有现成调度器时，可以使用 `HeartbeatLoop` 提供的可取消异步轮询；已有 Bot 调度器则只调用 `heartbeat_due()` 与 `wake()`，不要重复创建第二个循环。

## 配置

所有默认值都是演示参数，不对应任何真实 Agent。复制 [`examples/config.example.json`](examples/config.example.json)，使用 `load_config(path)` 读取后再调节。建议先改唤醒频率和每日上限，再逐步调基线、漂移和阈值。

## 文档

- [架构与数据流](docs/ARCHITECTURE.md)
- [功能与调参说明](docs/CONFIGURATION.md)
- [隐私与脱敏说明](docs/PRIVACY.md)
- [接入与部署建议](docs/INTEGRATION.md)

## 开源许可

MIT License。可以用于个人 Agent、机器人、研究原型和商业项目；保留许可证即可。
