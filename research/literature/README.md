# 文献研究产物中心

论文原件、主书目数据、集合和批注统一放在 Zotero；这里不再保存 PDF 副本，只保存 Zotero 索引快照与可审计的阅读成果。

| 目录 | 含义 |
| --- | --- |
| `00-index/` | `zotero:sync` 生成的可移植文献目录 |
| `.local/` | 本机 Zotero PDF 路径解析结果；不提交版本库 |
| `10-queue/` | Zotero 新条目生成的待处理阅读包 |
| `20-active/` | 正在双语翻译或精读 |
| `30-review/` | 等待来源、数字、术语与结论终审 |
| `40-library/<topic>/` | 已完成、按方向归档的阅读成果；不是 PDF 仓库 |
| `90-hold/` | 无全文、损坏、版本不明或暂缓材料 |

## 日常入口

1. 在 Zotero 中把论文及 PDF 加到对应项目集合。
2. 保持 Zotero 运行，双击项目根目录 `sync-zotero.cmd`，或运行 `npm run zotero:sync`。
3. 在 Codex 中说“处理 Zotero 中的未读论文”，并给出标题、item key 或研究方向。
4. 阅读包中的 `02-translation.html` 用于原文—中文左右对照。

集合映射和连接规则见 [`F-003 Zotero 关联桥`](../../features/F-003-zotero-bridge/README.md)，精读交付物和质量门槛见 [`F-002 文献流水线`](../../features/F-002-literature-pipeline/README.md)。

同步只负责发现、去重、索引和生成模板。Codex 不是后台常驻服务；全文研究在活跃会话中进行，完成状态必须经过来源核验与终审。
