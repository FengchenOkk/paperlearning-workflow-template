# Zotero 接入与只读同步

Zotero 是可选的入库来源。它管理书目与原始附件，工作流管理翻译、精读、结构化分析与知识网络。不开启 Zotero 时，`new paper`、模型任务和本地图谱照常使用。

## 五分钟接入

先在仓库根目录执行 `python tools/wf.py bootstrap`。它创建缺失的 `config/zotero.local.yaml`，不覆盖已有模型配置、Zotero 配置或 `.env`。随后选择下面一种模式，只编辑本地配置中的对应字段。

### 离线导出：适合首次试用

在 Zotero 导出所选集合为 **Better BibTeX JSON**，保存到项目的 `00_inbox/private/zotero-export.json`。需要安装 Better BibTeX；不使用该插件也可导出 CSL JSON。导出不包含附件文件，优先保留附件路径。

```yaml
zotero:
  enabled: true
  mode: export
  export:
    path: projects/my-research/00_inbox/private/zotero-export.json
    format: better-bibtex-json
```

CSL JSON 使用 `format: csl-json`。配置相对路径从仓库根目录解析，绝对路径也可用。CSL 的 `id` 用作 citekey；没有 Zotero item key 时生成稳定的 EXPORT 标识，并在 meta 中标明是合成标识。

### 本地 API：适合日常使用

启动 Zotero，在 **Settings → Advanced** 启用 **Allow other applications on this computer to communicate with Zotero**。只读请求无需 Key，个人库使用用户 ID `0`。[Zotero 官方本地 API 说明](https://www.zotero.org/support/dev/web_api/v3/local_api)。

```yaml
zotero:
  enabled: true
  mode: local
  local:
    base_url: http://127.0.0.1:23119/api/users/0
    timeout_seconds: 10
```

群组库改用 `/api/groups/<group-id>`。本工具只允许本机 loopback 地址，并仅发送 GET 请求；不会申请写权限或修改 Zotero 数据库。优先使用条目中的 `citationKey` 或 Extra 的 `Citation Key:`；标准 API 不一定暴露 Better BibTeX 自动生成的 citekey，必须保持这些键时优先使用 Better BibTeX JSON 导出。

本地附件通过 `/file/view/url` 获取原文件路径，不下载 PDF。端点不可用时保留 Zotero 打开链接；工作流仍可入库和生成图谱。

### Web API：适合读取在线库

```yaml
zotero:
  enabled: true
  mode: web
  web:
    library_type: user
    library_id: "你的数字用户ID"
    api_key_env: ZOTERO_API_KEY
```

群组库使用 `library_type: group` 和群组 ID。Key 只放本机 `.env` 的 `ZOTERO_API_KEY=自己的值` 或同名系统环境变量；系统值优先。Key 变量名可自定。申请 Key 时仅授予所需库的读取权限。[Zotero 官方 Web API 说明](https://www.zotero.org/support/dev/web_api/v3/basics)。

Web 模式读取元数据和附件链接，不下载附件。没有 Key、服务不可用或导出损坏时报告原因，保留项目文件，使用手动入库或 export 接力。

## 预览与执行

将 `my-research` 换成已创建的项目名：

```powershell
python tools/wf.py zotero doctor
python tools/wf.py zotero status my-research
python tools/wf.py zotero sync my-research --dry-run
python tools/wf.py zotero sync my-research --apply
python tools/wf.py validate my-research
```

`zotero doctor/status` 会读取所选来源；普通 `doctor --offline` 始终不访问网络。新配置默认 `dry_run_default: true`：普通 `sync` 也是预览，用 `--apply` 明确执行。`sync --dry-run` 可以读取数据，但不写项目、日志或配置。实际同步后在 `00_inbox/zotero-sync-report.yaml` 查看新建、更新、疑似重复、损坏条目与附件缺失报告。旧 Python 调用 `zotero.sync(..., dry_run=False)` 保留原来的实际同步行为；传 `None` 时采用配置默认值。

## 集合、分类与标签

在项目 `project.yaml` 配置：

```yaml
zotero:
  collections: [COLLECTION_KEY]
  category_map:
    COLLECTION_KEY: [综述, 我的方向]
  tag_filter: [待读]
  ignore_tags: [不纳入]
```

空数组表示不限制；`tag_filter` 要求全部指定标签，`ignore_tags` 命中任一标签即排除。collection key/name 映射到 categories，未映射时使用集合名称或 key；tags 映射到 topic_tags，保持中文标签。

## 更新边界

- 先通过 `INDEX.json.aliases` 将带库范围的 `zotero:<library-type>:<library-id>:<item-key>` 解析为稳定论文 ID，然后交叉核对 DOI/item key；无索引时保留旧 DOI/item key 匹配。标题＋年份只给疑似重复建议。
- 同一批数据出现重复 DOI/item key，或匹配到多个本地论文时，报告并跳过，不自动合并。
- 已有 citekey 保持不变，Zotero 改键不会重命名论文或打断 claim 关联。大小写、下划线及安全的 Unicode 文件名保留；不安全文件名改用稳定后备键。
- `meta.id` 一旦创建就不改变；远端改 citekey 时保存 `citekey:<旧键>`、`citekey:<新键>` 和 Zotero 旧别名。移目录后通过索引解析 ID，不使用 citekey 作为连接主键。
- collection key 转为稳定 `topic:zotero-<库>-collection-<key>`；集合改显示名不改变该 ID。标签转为带文本指纹的 topic ID，中文标签可用。关系写入 meta 的 `links`，证据定位到 `zotero.collection_keys/tags`，自动关系为 candidate；知识图谱从这些源 links 生成。
- 默认 `preserve_manual: true`：只补空字段或更新上次由 Zotero 写入且尚未被人工改动的字段；分类与标签保留人工值。`zotero.synced_fields` 记录上次输入值，用于判断字段归属。
- 只更新 meta.yaml 和 01_source/source-links.yaml；不写翻译、精读、分析、临时笔记，不自动推进阅读状态。
- `attachment_mode: link` 默认仅记录路径；缺失附件明确报告。`copy` 是用户显式选择的可选模式，仅复制本地已有文件到 01_source/attachments，目标冲突不覆盖，不改 Zotero 原附件。
- `create_missing_papers` 控制是否入库新论文；`update_metadata` 控制已有身份字段更新；`direction` 必须为 read_only。
- `use_index_json/preserve_aliases` 默认开启；collections 与 tags 各自可用 `link_collections_to_topics/link_tags_to_topics` 关闭自动 topic 连接。`update_hash: true` 在同步后生成 INDEX.json、人类索引与图谱；显式设为 false 时只同步源记录，报告 `index_update_pending: true`，必须随后运行 `wf.py index <project>` 才能派发依赖新输入的任务。

切换库/来源时遇到已绑定另一库的相同 DOI，会报告冲突；请核对 item key 和 library_id 后手工确认绑定。删除 Zotero 条目不会删除本地论文。

## 模板分享

`.env`、`config/models.local.yaml`、`config/zotero.local.yaml`、`.runs/`、原文及 private/ 保持忽略。上传前执行 `python tools/wf.py doctor --offline --share-check`，检查 Git 跟踪状态和明显密钥模式，输出不显示 Key。

误上传 Key 时先在服务后台撤销并重新生成，再清理公开文件和历史；仅删除文件不能使泄露 Key 失效。真实元数据、附件路径可能包含私人信息，实际研究使用自己的私有仓库。

测试只使用 `tests/fixtures/zotero/` 的 mock JSON 和模拟 HTTP，不证明真实 Zotero 已连接；真实连接按上述 doctor/status 验证。

## 统一连接与核验

`INDEX.json.artifacts` 保存稳定 ID 到路径/锚点/哈希的解析结果，`aliases` 保存旧 citekey 与 Zotero key 映射。它可删除后从核心文件重建；`knowledge-graph.json` 是从 `INDEX.json.links` 派生的视图，不能作为第二个人工关系源。源记录的 `links` 是关系的唯一维护位置。

新证据优先使用 ArtifactRef，例如 `evidence: [{id: "paper:Example2025", anchor: null}]`；历史 `{file, field}` 和文件路径字符串仍兼容。图谱通过索引归一化为当前文件与字段位置，并保留原 `source_ref` 追踪引用。不存在的 ID、文件或锚点会报告，不生成缺证据的边。

图谱覆盖论文、概念、第一性原理、公式、claim、topic、task、attempt 和被连接的 artifact；不存在于索引的节点或证据不足的边会报告并跳过。相似算法仍使用 Jaccard/IDF 与第一性原理、综述候选比较，但结果先写回源 `links`，自动状态为 candidate。主模型/verifier 或用户核验后修改源 link 为 verified，保留评审者和说明；证据输入变化时降回 candidate，历史意见留在源 `audit/link_audit`。知识地图只重建 GENERATED 标记内的正文。

为保留上一版已有的人工图谱核验，带 human/main/verifier 评审标记且输入/证据一致的旧关系允许一次性迁入源 links，记录 `legacy_graph_review_imported`；迁入后以源 links 为准，不再直接编辑图谱核验状态。
