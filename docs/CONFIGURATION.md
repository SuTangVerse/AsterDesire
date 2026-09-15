# 功能与调参说明

## 推荐调参顺序

1. `HeartbeatConfig`：先定唤醒区间、每日上限和静默时段。
2. `DesireConfig.baselines`：决定长期性格底色。
3. `hourly_drift`：决定无人互动时哪些需要会积累。
4. `coupling`：只保留有明确含义的小幅联动。
5. 幻想/独处与冷却门槛。

不要一次同时改变所有参数，否则很难知道行为变化来自哪里。

## 关键参数

- `baseline_pull_hours`：数值偏离基线后回归的速度。
- `libido_threshold`：libido 赢得动机竞选后仍需达到的资格门槛。
- `solo_idle_seconds`：距离伴侣最近出现至少多久才允许私人幻想或独处。
- `solo_fatigue_ceiling`：疲劳超过此值时不进入私人幻想。
- `refractory_seconds`：释放后的冷却时间。
- `solo_daily_limit`：每日最多完成多少次 solo 生命周期。
- `solo_modes`：部署方允许的模式标签；公开版不附带任何私人内容模板。
- `thought_threshold`：驱动达到何种强度时可以形成结构化浮念。
- `plateau_seconds`：某项需要被满足后，多久内禁止正向自动回填。
- `repeat_penalty`：心跳连续选择同一动机时的扣分。
- `circuit_breaker_failures`：连续失败多少次后停止自动尝试。

## 调参验收

至少模拟以下时间线：

- 一整天无人互动；
- 连续技术工作后突然收到亲密消息；
- libido 高但 arousal 低；
- libido 与 arousal 独立变化；
- 刚释放且处于冷却；
- 主动动作被跳过；
- 外部模型连续失败；
- 跨越静默时段和日期边界。

每次变更固定 seed，并把快照作为回归测试保存；不要用生产聊天原文做测试夹具。
