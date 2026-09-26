# 项目工作方法

## 一条需求如何流转

```text
想法 → BACKLOG 登记 → 建立工作流 → 拆分任务 → 实施与核验 → 交付 → 归档
```

先判断需求属于哪一类：可被多个课题复用的工具或能力进入 `features/`；有明确研究目标和交付结果的课题进入 `workstreams/`。

### 1. 登记

所有尚未开始的想法先写入 `BACKLOG.md`。每项任务使用稳定编号，如 `T-001`。只有近期确实要做的事项才进入 `PROJECT.md`。

### 2. 建立工作流

每个相对独立的课题或功能建立一个 `workstreams/WS-###-slug/` 目录。它的 `README.md` 说明目标、范围、完成标准、任务和关键产物。

创建命令：

```powershell
node planning/scripts/new-workstream.mjs WS-002 literature-review "某课题文献综述"
```

`slug` 只使用小写字母、数字和连字符。命令只创建目录，不会自动修改总览和任务池；创建后把链接补到 `PROJECT.md` 或 `BACKLOG.md`。

新增可复用功能：

```powershell
node planning/scripts/new-feature.mjs F-002 literature-search "文献检索"
```

### 3. 执行

- Codex 负责拆分、实施、核验和最终整合。
- 只有边界清楚且能独立检查的任务才交给 DSH。
- 原始资料、分析过程和最终成果分开保存。
- 每个重要结论必须能够追溯到来源、数据或代码。

### 4. 决策

影响多个工作流、改变技术路线或难以撤销的决定，写入 `DECISIONS.md`。普通实现细节保留在对应工作流中。

### 5. 完成与归档

完成前检查工作流中的完成标准。结果放入 `outputs/`，可复现材料保留在工作流或 `research/` 中。结束后把状态改为 `done`；停止维护的内容改为 `archived`，并写明原因。

## 文件应该放在哪里

| 内容 | 位置 |
| --- | --- |
| 当前重点和整体状态 | `PROJECT.md` |
| 中长期阶段目标 | `planning/ROADMAP.md` |
| 全部待办和执行任务 | `planning/BACKLOG.md` |
| 跨模块的重要决定 | `planning/DECISIONS.md` |
| 可复用功能 | `features/F-###-slug/` |
| 单个课题或结果导向工作流 | `workstreams/WS-###-slug/` |
| 共享数据、实验说明和文献研究产物 | `research/` |
| 论文原件、主元数据、集合与批注 | Zotero（项目通过 `F-003` 只读同步） |
| 报告、论文、图表等正式成果 | `outputs/` |
| DSH 输入任务 | `features/F-001-deepseek-worker/tasks/` |
| DSH 自动运行记录 | `features/F-001-deepseek-worker/.runtime/runs/`，不提交版本库 |

## 维护节奏

- 开始一项工作前：更新工作流状态和下一步。
- 开始处理新论文前：在 Zotero 中归入映射集合并运行 `npm run zotero:sync`；不要把 PDF 复制进项目。
- 完成一个可交付结果后：更新任务池，并记录验证方式。
- 出现方向变化时：记录决策及原因。
- 每周或每个阶段结束时：清理已完成任务，确认下一阶段优先级。
