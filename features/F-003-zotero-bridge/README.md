# F-003 Zotero 关联桥

## 目的

把 Zotero 设为论文原件、书目元数据、集合和批注的唯一管理入口；项目只保存可复现的元数据快照、处理状态、翻译、证据与研究综合，不再复制 PDF。

连接使用 Zotero 桌面端只读本地 API（默认 `http://127.0.0.1:23119/api`）。它不需要 Zotero API Key，不向云端写入，也不直接读取或修改 `zotero.sqlite`。

## 本地集合配置

公共模板只提交 [`config/collections.example.json`](config/collections.example.json)。运行 `npm run setup` 后会创建被忽略的 `config/collections.local.json`；每位使用者在其中填写自己的 collection key、集合名称、工作流和主题。

列出 Zotero 本机集合：

```powershell
npm run zotero:list
```

配置使用固定 collection key 建立关联，同时校验集合名称，防止映射到错误集合。一个条目可同时放入多个已映射集合；项目会合并其归属，不复制阅读包。

## 使用

1. 运行 `npm run setup` 并编辑 `collections.local.json`。
2. 在 Zotero 中把论文父条目及 PDF 放进对应集合。
3. 保持 Zotero 桌面端运行，双击项目根目录 `sync-zotero.cmd`，或运行：

```powershell
npm run zotero:check
npm run zotero:sync
```

若本机 `npm` 启动器仍报 `npm-cli.js` 路径错误，双击 `sync-zotero.cmd`，或直接运行：

```powershell
node features/F-003-zotero-bridge/scripts/zotero-sync.mjs --check
node features/F-003-zotero-bridge/scripts/zotero-sync.mjs --sync
```

同步后：

- `research/literature/00-index/catalog.json`：可机器读取的可移植元数据快照；
- `research/literature/00-index/catalog.md`：便于人读的索引；
- `research/literature/.local/zotero-resolved.json`：本机 PDF 绝对路径，仅供 Codex 读取，已忽略版本控制；
- `research/literature/10-queue/<title>--<itemKey>/`：新条目的阅读包，不含 PDF 副本。

Zotero item key 是论文在项目中的稳定身份。改标题或移动集合不会创建第二份阅读包；同一条目被多个集合引用也只生成一个阅读包。

## 双语对照

阅读包内 `02-translation.md` 是结构化的分段翻译源文件。更新它后运行：

```powershell
npm run literature:render -- "research/literature/20-active/<paper>/02-translation.md"
```

本机 `npm` 不可用时，直接把同一路径传给 `node features/F-002-literature-pipeline/scripts/render-translation.mjs`。

脚本生成同目录的 `02-translation.html`，原文和中文并排显示，可在浏览器中搜索、打印或作为 PDF 保存。HTML 是派生产物；内容修改以 Markdown 为准。

## 边界与故障处理

- 同步是只读 Zotero、写入项目；不会删除 Zotero 条目、附件或批注。
- Zotero 未运行、本地 API 不可用、集合 key/name 不一致、条目无 PDF 时均明确报告。
- 没有 PDF 的条目仍会排队，但目录索引会标记 `0 PDF`，正式精读前必须补齐全文或记录例外。
- 本机路径只写入 `.local/`，不会进入可移植 manifest 或正式输出。
- `collections.local.json`、索引和全部阅读包默认被 `.gitignore` 排除；公共仓库不会暴露个人文库结构和研究内容。
