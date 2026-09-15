# 隐私与脱敏说明

本仓库只包含通用算法和虚构示例参数。

明确未收录：

- 真实姓名、昵称、关系称谓与人物档案；
- Telegram/Discord 群 ID、用户 ID、用户名与聊天内容；
- API Key、Token、Cookie、密码、邮箱、域名、IP 与服务器目录；
- 私人人格提示词、长期记忆、作品、幻想正文与真实欲望数值；
- 生产数据库、状态快照、日志、审批记录和媒体文件；
- 针对特定个人训练或整理出的敏感词表。

## 接入方责任

`EventSignals` 的分类应尽量在内存中完成，只写入强度、布尔值和不可反查文本的事件 ID。若需要保留证据，把正文放在权限隔离的私有记忆库，仅在 Growth Rings 中保存不透明的 `evidence_id`。

生产状态文件建议使用独立 Unix 用户、目录 `0700`、文件 `0600`；备份同样加密。不要把 `state/`、`.env` 或运行日志提交到 Git。

## 发布前检查

```bash
git grep -nEi '(token|api[_-]?key|password|cookie|BEGIN .*PRIVATE KEY)' -- ':!docs/PRIVACY.md'
git status --short
```

第二条命令用于确认没有误提交状态、媒体或本地配置。
