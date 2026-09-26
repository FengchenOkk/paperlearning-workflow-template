# PaperLearning Workflow Template

一个可复用的 Zotero—Codex 科研工作流模板。Zotero 管理论文原件、书目数据、集合和批注；项目管理双语翻译、证据、概念、复现过程和研究综合。DeepSeek Harness（DSH）是可选的外部任务执行器，不影响核心 Zotero 流程。

公共仓库只包含通用代码、说明、模板和测试。`PROJECT.md`、实际工作流、论文索引、阅读包、研究笔记、结果和个人 Zotero 配置默认由 `.gitignore` 留在本机。

## 初始化个人实例

```powershell
git clone <your-repository-url>
cd PaperLearning
npm install
npm run setup
```

若本机 `npm` 启动器不可用，可直接执行 `node planning/scripts/setup-local.mjs`；其他命令也可按 `package.json` 中的脚本改为直接调用 Node。

`setup` 从公开示例创建本机私有文件，已存在的文件不会被覆盖：

- `PROJECT.md`
- `planning/BACKLOG.md`、`DECISIONS.md`、`ROADMAP.md`
- `features/F-003-zotero-bridge/config/collections.local.json`

然后启动 Zotero，列出本机集合并填写 `collections.local.json`：

```powershell
npm run zotero:list
npm run zotero:check
npm run zotero:sync
```

Windows 也可以双击 `sync-zotero.cmd`。详细连接方法见 [F-003 Zotero 关联桥](features/F-003-zotero-bridge/README.md)，精读规则见 [F-002 文献流水线](features/F-002-literature-pipeline/README.md)。

## 从一篇论文开始

1. 在 Zotero 中保存论文父条目、PDF 和完整元数据，并放入已映射集合。
2. 运行 Zotero 同步，生成不含 PDF 副本的阅读包。
3. 让 Codex 按“原文—中文对照翻译 → 证据化精读 → 概念网络 → 终审 → 综合”处理。
4. 打开阅读包中的 `02-translation.html`，左右对照原文与中文。

## 分工

| 角色 | 负责 |
| --- | --- |
| Codex/GPT（主控） | 明确问题与方法、任务拆分、原始来源核验、代码与实验、证据整合、最终结论 |
| DSH/DeepSeek（任务执行者） | 候选文献线索、给定资料的信息提取、替代假设、独立质疑与遗漏检查 |

DSH 通过项目脚本作为外部进程运行。它只适合边界清楚、可独立检查的任务；Codex/GPT 对研究设计、来源核验、代码验证和最终判断负责。不使用 DSH 时无需配置 DeepSeek API Key。

## 安装与检查

需要 Node.js 和 Zotero 桌面端。核心检查：

```powershell
npm test
npm run zotero:list
```

可选的 DeepSeek API 密钥可设为当前终端的 `DEEPSEEK_API_KEY`，或保存在被忽略的 `.env`。不要把密钥写入任务文件或提交到仓库。

```powershell
$env:DEEPSEEK_API_KEY = "你的密钥"
```

## 可选：交给 DSH

先在 `features/F-001-deepseek-worker/tasks/` 创建任务文件；该目录默认忽略，因为任务可能包含私有研究材料。配置密钥后运行：

```powershell
node features/F-001-deepseek-worker/scripts/dsh-task.mjs --task-file features/F-001-deepseek-worker/tasks/<task>.txt
```

运行记录保存在被忽略的 `.runtime/runs/`。模型输出只是待核验线索，不是科研证据。

## 公共与私有边界

公共模板提交 `features/`、通用脚本、模板、测试、示例配置和说明。默认不提交：

- `PROJECT.md` 和规划状态文件；
- `workstreams/WS-*/`、实际研究材料和正式成果；
- Zotero 索引、阅读包和本机附件路径；
- DSH 任务、运行记录、`.env`、PDF 和大型数据。

发布前仍应人工检查暂存区。完整规则见 [`.gitignore`](.gitignore) 和 [公共模板发布检查](SHARING.md)。通用代码与模板采用 [MIT License](LICENSE)；第三方论文、图表、数据和完整翻译不包含在该授权中。

## 接入边界

- 本项目不修改用户级 `~/.codex/config.toml`，Codex 默认仍由 GPT 驱动。
- DSH 的工作区是项目目录，拥有其自身的工具能力；涉及未公开资料、外部发送或文件修改时，先明确范围。
- 论文、DOI、数据和引用都须由 Codex 回到原始来源核验；模型回答本身不是科研证据。

参考：[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)、[DSH headless 模式](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/bundle/headless/README.md)、[DeepSeek 模型](https://api-docs.deepseek.com/quick_start/pricing/)、[Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)。
