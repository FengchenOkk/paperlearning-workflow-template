# 功能模块

`features/` 存放可以被多个科研课题复用的能力。每个功能独占一个 `F-###-slug/` 目录，配置、脚本、模板和运行产物都留在自己的目录中。

| ID | 功能 | 状态 | 入口 |
| --- | --- | --- | --- |
| `F-001` | DeepSeek 任务执行器 | active | [说明](F-001-deepseek-worker/README.md) |
| `F-002` | 文献精读与知识框架流水线 | active | [说明](F-002-literature-pipeline/README.md) |
| `F-003` | Zotero 本地只读关联桥 | active | [说明](F-003-zotero-bridge/README.md) |

新增功能：

```powershell
node planning/scripts/new-feature.mjs F-002 literature-search "文献检索"
```

功能与工作流的区别：功能是可复用工具，如文献检索、PDF 解析和数据清洗；工作流是具体目标，如某个课题的系统综述或一次实验。
