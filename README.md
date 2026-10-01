# 论文阅读与复现工作流

组织文献精读与综合、复现可行性分析和实验规划。主模型负责计划与验收（commander-reviewer），子模型按契约执行（primary-executor）；模型厂商独立选择，沿用 Codex 会话、接入 API/CLI 或人工接力。真实实验功能待配置。

## 五分钟开始

在仓库根目录执行（Python 3.11+）：

```powershell
python -m pip install -r requirements.txt
python tools/wf.py bootstrap
python tools/wf.py doctor --offline
python tools/wf.py demo
python tools/wf.py init my-research --title "我的研究"
python tools/wf.py new paper my-research first-paper
python tools/wf.py new concept my-research first-concept
python tools/wf.py new claim my-research first-paper main-result
python tools/wf.py validate my-research
```

随后填写项目 `research-profile.yaml`，将论文归档至对应 `01_source/`，按项目内 `README.md` 的文件职责进行阅读。模型选择只修改 `config/models.local.yaml`；密钥只放环境变量或本地 `.env`。

## 常用命令

```powershell
python tools/wf.py index my-research
python tools/wf.py index my-research --json
python tools/wf.py graph my-research --dry-run
python tools/wf.py run my-research projects/my-research/00_inbox/first-pass.yaml
python tools/wf.py validate --contracts
python tools/wf.py validate --links my-research
python -m unittest discover -s tests
```

旧 run 运行前将 task.yaml 的 task_id、objective、inputs 和 source_refs 填好；推荐将实际任务包保存在项目 `00_inbox/`，运行时提供相对于仓库的路径。旧 inputs/source_refs 相对于项目；新任务用下述 ArtifactRef。manual 保留人工接力，响应还需整理提交和真实评审。

任务包示例见 [文献工作流](workflow/literature.md#最小任务示例)，共用接口与文件规则见 [工作流说明](workflow/README.md)。

想快速读懂一篇论文，先看该论文的 `06_synthesis/summary.md`，再对照 `concept-guide.md` 学习底层原理、概念和公式；全文译文与精读仍在原目录。新增成果的任务规划和逐段覆盖命令见 [论文通读与概念学习手册](workflow/study-guide.md)，项目 INDEX.md 会提供直接入口。

## 计划、执行和评审

项目 `INDEX.json` 统一解析论文、概念、公式、claim、任务和产物的稳定 ID；`INDEX.md` 保留人类视图。新任务由 [task-contracts.yaml](workflow/task-contracts.yaml) 声明输入/输出 ArtifactRef、职责、验收标准与最多3次子模型尝试；子模型一次返修仍失败时主模型接手，默认另有1次修复，修复草稿仍走单独验收。对象移动不改变 ID，统一 `links` 是关系来源。

```powershell
python tools/wf.py task run my-research projects/my-research/00_inbox/verify-paper-id.yaml
python tools/wf.py task status my-research verify-paper-id
# 真实结果提交后构建评审包
python tools/wf.py task review my-research verify-paper-id --attempt 1
# 在当前会话中完成真实审核后导入
python tools/wf.py task review my-research verify-paper-id --attempt 1 --review projects/my-research/00_inbox/verify-paper-id-review.yaml
python tools/wf.py task accept my-research verify-paper-id --attempt 1
```

先填写新格式任务包，再预览执行；真实外部调用按授权加 `--execute`。子模型只读最小 context bundle、提交 attempt 草稿；主模型只读 review bundle 并按需核对证据，保存真实审核决定。最后一条只会应用符合条件的 accept，不自动创造科学通过记录。任务状态、索引和图谱随正式应用更新；返修只传问题与必要增量材料。完整 ArtifactRef、任务包及人工接力说明见 [模型分工与闭环手册](workflow/task-orchestration.md)。旧 `run` 命令保留兼容。

## Zotero 与论文知识网络

可选只读接入 Zotero 本地 API、Web API 或 Better BibTeX/CSL JSON 导出，操作见 [Zotero 手册](workflow/zotero.md)。同步只更新书目和附件引用，保护人工内容；不开启也能手动阅读。

论文统一编号目录，`index` 自动生成知识地图和 `knowledge-graph.json`；第一性原理、综述及概念相似关系都是带证据的待核验候选。算法、生成区和 `migrate --dry-run` 迁移见 [文献工作流](workflow/literature.md)。

## 模型接入

按 [模型接入手册](workflow/model-setup.md) 配置，仅需准备服务地址、模型名、API Key 三项。主模型用 `orchestrator.profile` 选择，子模型用 `settings.default_subagent_profile` 选择，两者可来自不同服务。

`model_profiles` 集中保存连接，`api_key_env` 对应本地 `.env` 中自定义的变量名。支持 Chat Completions、Anthropic Messages 和外部 CLI；提供商名称不限，接入方式取决于服务实际协议。旧 `subagent_profiles` 和逐角色完整配置继续兼容。

当前 Codex/GPT＋DeepSeek 用法也保留；DeepSeek 可以读取 `.env` 中的 `ds_apikey`。没有 Key 时保留人工接力。外部调用先预览，再按授权加 `--execute`；新主模型 API 评审用 `task review --execute`，旧主模型文本接口保留 `run --main`。API 主模型负责给定文本的计划、汇总与审核，由执行器管理本地文件和任务调度。

## 安全分享模板

上传前执行 `python tools/wf.py doctor --offline --share-check`。Git 检查确认 `.env`、`config/models.local.yaml`、`config/zotero.local.yaml` 没有被追踪；明显密钥扫描只显示路径与行号，不显示匹配内容。无 Git 仓库时报告“忽略规则已声明”，不能当作 Git 追踪检查通过。扫描不覆盖 Git 历史或大文件，不能证明所有私密内容都已脱敏。

分享集必须排除 `.env`、`config/models.local.yaml`、`config/zotero.local.yaml`、`.runs/`、真实 PDF/原文、实验原始数据、私密目录、临时大文件和个人认证文件。`.gitignore` 已覆盖这些常见路径；新增私密数据放 `private/` 或补充忽略规则。它只影响 Git 未追踪文件，直接压缩/复制不会自动排除文件。只分享工作流代码和脱敏示例，不整目录打包研究资料。

若曾误上传 Key，立即到相应服务商后台撤销并重新生成，然后清理公开文件与历史；仅删除文件或添加 .gitignore 不会让已泄露 Key 失效。主模型与子模型的认证均由每个人在本机配置。

## 目录导航

- `config/`：主模型、子模型、路由与可选 Zotero 配置。
- `workflow/`：流程、功能地图、角色提示、schema、内部目录定义和已下载 ARS。
- `projects/`：只保存实际研究项目；目录及文件用途见 [projects/README.md](projects/README.md)。
- `tools/`：CLI 和适配器。
- `tests/`：不访问外部服务的验收测试。

每个研究方向建立一个 `projects/<direction-slug>/` 项目，按 `00_inbox → 10_literature → 20_reproduction → 30_outputs` 管理；每篇论文一个独立目录，每个复现 claim 一个独立目录。工具内部使用的文件定义集中在 `workflow/layouts/`，不会作为真实项目出现。

文献综合工作稿按需放 `10_literature/<name>.md`，核验后的交付版本放 `30_outputs/`。文献阅读规范已接入，复现具体功能配置待后续确定，当前结构不依赖研究学科或模型厂商。

## 当前状态

保留五类顶层目录、模型配置与旧命令，新增稳定 ID、机器索引、统一关系、任务契约、最小上下文、结果/评审包和显式接受流程。论文采用 meta.yaml 及 01_source～05_notes 编号目录，四核心文件职责保留；按需增加 06_synthesis/summary.md（综合总结）与 concept-guide.md（概念学习指南），分段翻译可用 study plan/coverage 管理。可选只读 Zotero、阅读清单、候选知识图谱、概念卡和复制迁移继续使用。内置 PDF 解析、自动联网文献检索、实际复现和原生模型启动整合待实现；执行器可另行提取 PDF、查阅来源并人工核验。基础依赖仍只有 PyYAML，离线测试不访问真实外部服务。详细边界见 [通读与学习手册](workflow/study-guide.md)、[模型分工与闭环手册](workflow/task-orchestration.md)，阶段验收见 [升级记录](workflow/upgrade-validation.md)，待确认事项见 [路线图](ROADMAP.md)。
