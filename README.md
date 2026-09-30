# 论文阅读与复现工作流

组织文献精读与综合、复现可行性分析和实验规划。主模型与子模型可独立选择：沿用当前 Codex 会话、接入支持的 API/CLI，或人工接力；真实实验功能待配置。

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

随后填写项目 `research-profile.yaml`，将论文归档至对应 `source/`，按模板阅读。模型选择只修改 `config/models.local.yaml`；密钥只放环境变量或本地 `.env`。

## 常用命令

```powershell
python tools/wf.py index my-research
python tools/wf.py run my-research projects/my-research/00_inbox/first-pass.yaml
python -m unittest discover -s tests
```

运行前将 task.yaml 的 task_id、objective、inputs 和 source_refs 填好；推荐将实际任务包保存在项目 `00_inbox/`，运行时提供相对于仓库的路径。inputs/source_refs 则相对于项目。manual 生成 `.runs/` 的 prompt，人工将模型输出保存为同目录 response.md。

任务包示例见 [文献工作流](workflow/literature.md#最小任务示例)，共用接口与文件规则见 [工作流说明](workflow/README.md)。

## 模型接入

按 [模型接入手册](workflow/model-setup.md) 配置，仅需准备服务地址、模型名、API Key 三项。主模型用 `orchestrator.profile` 选择，子模型用 `settings.default_subagent_profile` 选择，两者可来自不同服务。

`model_profiles` 集中保存连接，`api_key_env` 对应本地 `.env` 中自定义的变量名。支持 Chat Completions、Anthropic Messages 和外部 CLI；提供商名称不限，接入方式取决于服务实际协议。旧 `subagent_profiles` 和逐角色完整配置继续兼容。

当前 Codex/GPT＋DeepSeek 用法也保留；DeepSeek 可以读取 `.env` 中的 `ds_apikey`。没有 Key 时保留人工接力。外部调用先普通 `run` 预览，再按授权加 `--execute`；主模型 API 加 `--main`。API 主模型负责文本计划、汇总与审核，本工具未实现它自主读写文件或循环调用子模型。

## 安全分享模板

上传前执行 `python tools/wf.py doctor --offline --share-check`。Git 检查确认 `.env`、`config/models.local.yaml` 没有被追踪；明显密钥扫描只显示路径与行号，不显示匹配内容。无 Git 仓库时报告“忽略规则已声明”，不能当作 Git 追踪检查通过。扫描不覆盖 Git 历史或大文件，不能证明所有私密内容都已脱敏。

分享集必须排除 `.env`、`config/models.local.yaml`、`.runs/`、真实 PDF/原文、实验原始数据、私密目录、临时大文件和个人认证文件。`.gitignore` 已覆盖这些常见路径；新增私密数据放 `private/` 或补充忽略规则。它只影响 Git 未追踪文件，直接压缩/复制不会自动排除文件。只分享模板目录和脱敏示例，不整目录打包研究资料。

若曾误上传 Key，立即到相应服务商后台撤销并重新生成，然后清理公开文件与历史；仅删除文件或添加 .gitignore 不会让已泄露 Key 失效。主模型与子模型的认证均由每个人在本机配置。

## 目录导航

- `config/`：主模型、子模型和路由配置。
- `workflow/`：流程、功能地图、角色提示、schema、模板、已下载 ARS。
- `projects/`：实际研究项目，`_template/` 是创建来源。
- `tools/`：CLI 和适配器。
- `tests/`：不访问外部服务的验收测试。

每个研究方向建立一个 `projects/<direction-slug>/` 项目，按 `00_inbox → 10_literature → 20_reproduction → 30_outputs` 管理；每篇论文一个目录，每个复现 claim 一个目录。

文献综合工作稿按需放 `10_literature/<name>.md`，核验后的交付版本放 `30_outputs/`。文献阅读规范已接入，复现具体功能配置待后续确定，当前结构不依赖研究学科或模型厂商。

## 当前状态

已实现五类目录、模型配置、创建/索引/校验、manual/mock/command/HTTP 适配器与临时 mock 演示。论文采用 meta/translation/reading/analysis 四文件；阅读清单、分类索引、知识网络和概念卡已接入。PDF 解析、联网文献检索、自动写入已核验译文/综述、实际复现与原生模型启动整合待实现。详细边界见 [工作流说明](workflow/README.md)，待确认事项见 [路线图](ROADMAP.md)。
