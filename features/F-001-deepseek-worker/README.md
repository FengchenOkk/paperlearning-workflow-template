# F-001 DeepSeek 任务执行器

## 目的

让 Codex 可以通过 DeepSeek Harness 将边界清楚的科研子任务交给 DeepSeek，并保留可检查的运行记录。

## 目录

| 路径 | 用途 |
| --- | --- |
| `config/dsh.patch.yml` | DeepSeek 模型路由 |
| `scripts/dsh-task.mjs` | headless 调用脚本 |
| `tasks/` | 手工编写的 DSH 任务文件 |
| `templates/task.txt` | DSH 任务模板 |
| `.dsh-home/` | DSH 本地配置和会话，自动生成、不提交 |
| `.runtime/runs/` | 每次调用的答案、事件与日志，自动生成、不提交 |

## 使用

DSH 是可选功能。不使用它时无需配置任何 DeepSeek 凭据。需要使用时：

1. 复制 `.env.example` 为被忽略的 `.env`，填写 `DEEPSEEK_API_KEY`。
2. 从 `templates/task.txt` 创建一个本机任务文件；`tasks/` 默认被忽略。
3. 先检查 Harness，再执行任务：

```powershell
node features/F-001-deepseek-worker/scripts/dsh-task.mjs --check
node features/F-001-deepseek-worker/scripts/dsh-task.mjs --task-file features/F-001-deepseek-worker/tasks/<task>.txt
```

成功时终端会打印 `answer.md` 的位置。不要把真实密钥放进本目录或任务文件；任务和运行记录可能包含私有材料，也不会进入公共模板。

## 版本策略

- `package.json` 和 `package-lock.json` 固定 DSH 版本，不自动跟随预发布版本。
- 默认使用 npm `latest`；`alpha` 和 `next` 仅在明确需要新功能并得到用户确认后采用。
- 升级前阅读发布说明，升级后至少运行启动检查和一个不含敏感材料的本地 smoke task。
- DSH 仍处于开发者预览期，跨版本可能需要调整配置或脚本。

## 模板默认值

- DSH 版本：`0.1.7-rc.2`，由锁文件固定。
- 模型路由：`deepseek-official / deepseek-flash`。
- 每位使用者必须在自己的环境中完成启动检查和真实 API 验证。
