# 模型接入手册

主模型是 commander-reviewer，负责计划、必要综合与最终验收；子模型是 primary-executor，按 literature-reader 等职责完成契约任务。两者可以使用不同厂商，也可以共用一个连接。模型连接与任务职责分离，重新分工不需要替换 API Key。需要 API 接入时，准备服务商提供的 **API 地址、模型名、API Key**，再按下列步骤操作。

子模型返修后仍未通过时，由主模型接手修复。接管沿用 orchestrator Profile 与最小返修包；现有 Codex 会话读取接力 prompt，API/CLI 通过 task revise --execute 调用。主模型修复默认1次（task-contracts.yaml 的 settings.main_repair_max_attempts），修复后仍单独审核，不更改连接或密钥。

## 1. 生成本地配置

在仓库根目录执行（Python 3.11+）：

```powershell
python -m pip install -r requirements.txt
python tools/wf.py bootstrap
```

以后只修改 `config/models.local.yaml` 和 `.env`；它们不应上传 Git。bootstrap 保留已有文件。共享模板默认人工接力，不要求安装 Codex，也不要求 OpenAI 或 DeepSeek 账号。

## 2. 选择主模型和子模型

### 保留当前 Codex/GPT，子模型使用 DeepSeek

保持主模型 `adapter: codex`、`model: inherit`；在 `models.local.yaml` 中设置：

```yaml
settings:
  default_subagent_profile: deepseek
```

在本地 `.env` 填：

```dotenv
ds_apikey=填入自己的DeepSeek密钥
```

内置 DeepSeek Profile 同时支持 `DEEPSEEK_API_KEY`；两者只需填一个。当前会话沿用本机认证，不需要主模型 API Key；首次使用 Codex 的认证步骤见 [官方说明](https://learn.chatgpt.com/docs/auth)。DeepSeek 地址及可用模型以 [官方接入文档](https://api-docs.deepseek.com/zh-cn/) 为准。

### 主模型和子模型都通过 API 接入，厂商自行选择

把 `models.local.yaml` 的 orchestrator/settings 替换为以下内容，并添加或合并 model_profiles；保留原来的 routing、fallback 和角色列表。下面的 `.example` 地址与模型名都是占位，必须换成服务商真实参数：

```yaml
orchestrator:
  profile: my-main
settings:
  default_subagent_profile: my-worker
model_profiles:
  my-main:
    adapter: openai_compatible
    provider: my-main-provider
    base_url: https://main-provider.example/v1
    model: main-model-id
    api_key_env: MAIN_MODEL_KEY
    timeout_seconds: 900
    fallback: manual
  my-worker:
    adapter: openai_compatible
    provider: my-worker-provider
    base_url: https://worker-provider.example/v1
    model: worker-model-id
    api_key_env: WORKER_MODEL_KEY
    timeout_seconds: 900
    fallback: manual
```

在 `.env` 中分别填自己的密钥：

```dotenv
MAIN_MODEL_KEY=填入主模型密钥
WORKER_MODEL_KEY=填入子模型密钥
```

变量名自行命名，只要和对应 `api_key_env` 一致，例如 `api_key_env: my_apikey`。兼容旧变量名可设置 `api_key_aliases: [OLD_WORKER_KEY]`。共享连接时让 orchestrator.profile 和 default_subagent_profile 指向同一 Profile，即可共用一个 Key。进程环境变量优先于本地 `.env`。

子角色保持 `profile: null` 就跟随全局默认；需要单独核验模型时设置 `subagents.verifier.profile: my-verifier`，并添加对应 Profile。旧版逐角色显式 adapter/连接字段仍优先；要改用 Profile，删除该角色的旧连接字段，保留 enabled/profile 等角色设置。不要把密钥直接写入 YAML。

`orchestrator.responsibility: commander-reviewer` 和 `settings.execution_responsibility: primary-executor` 声明分工；它们不改变当前 Codex 模型，也不替代 routing。`settings.task_contracts` 声明任务契约位置；上下文与尝试限制以契约为准。local 未写新声明字段仍兼容默认值，不自动覆盖用户连接；路由 role 与 workflow/task-contracts.yaml 必须一致。详细流程见 [模型分工与任务闭环](task-orchestration.md)。

## 3. 按服务协议选择 adapter

| 服务实际协议 | adapter | base_url 示例与认证 |
|---|---|---|
| Chat Completions | `openai_compatible` | 服务的 API 前缀，例如 `https://host.example/v1`；自动加 `/chat/completions`，Bearer Key |
| Anthropic Messages | `anthropic` | `https://api.anthropic.com/v1`；自动加 `/messages`，x-api-key 与 anthropic-version |
| 其他协议或本地 CLI | `command` | 用命令参数数组调用自行准备的适配程序 |
| 人工使用任意模型界面 | `manual` | 无需 Key，保存 prompt 后人工回填 |

OpenAI-compatible 是协议名称，支持该协议的其他厂商也能使用。API 前缀中的 `/v1` 按服务商说明填写，不要把完整 `/chat/completions` 或 `/messages` 当作 base_url。Anthropic 连接可将上述任一 Profile 改为：

```yaml
adapter: anthropic
base_url: https://api.anthropic.com/v1
model: 填服务商支持的模型ID
api_key_env: ANTHROPIC_API_KEY
request_options:
  max_tokens: 4096
```

协议与参数见 [Anthropic 官方 API 说明](https://platform.claude.com/docs/en/api/overview)。两种 HTTP 适配器均读取最终文本；仅支持其他协议、云平台签名认证或特殊网关时，需自行封装 command，例如 `command: [python, path/to/adapter.py]`。程序从 stdin 读取 prompt、将正文写 stdout、失败时返回非零退出码；程序须自行读取环境变量密钥。服务专有参数仅放该 Profile 的 request_options，不复制其他厂商的参数。

## 4. 检查并运行

```powershell
python tools/wf.py doctor --offline
python tools/wf.py demo
```

doctor 检查配置与 Key 是否存在；demo 使用 mock，不调用真实模型。两者通过不代表 Key 有效或账户有余额。准备项目及 [标准任务包](literature.md#最小任务示例) 后，先预览，再执行：

```powershell
# 子模型：根据任务角色与路由选择连接
python tools/wf.py run my-research projects/my-research/00_inbox/task.yaml
python tools/wf.py run my-research projects/my-research/00_inbox/task.yaml --execute

# 主模型 API/CLI：处理同一任务包，按主模型职责输出文本草稿
python tools/wf.py run my-research projects/my-research/00_inbox/task.yaml --main
python tools/wf.py run my-research projects/my-research/00_inbox/task.yaml --main --execute
```

以上为保留的旧 `run` 接口。将项目名和路径换成实际任务，结果位于 `.runs/<run>/`，查看 prompt.md、response.md 与 run.yaml。`--main` 不启动新的 Codex 会话，也不自动赋予 API 模型文件工具或循环调度能力；采用当前 Codex 时，在会话里完成主模型工作。缺 Key、无效配置或外部失败会保留 prompt 转人工接力，并记录原因；人工模式将输出保存为 response.md 后还需核验、补记完成情况。

### 新任务优先使用契约闭环

先生成 INDEX.json，从中选择输入 ID，填写 ArtifactRef 格式的新任务包；再预览并按授权执行：

```powershell
python tools/wf.py index my-research --json
python tools/wf.py validate --contracts
python tools/wf.py task run my-research projects/my-research/00_inbox/verify-paper-id.yaml
python tools/wf.py task run my-research projects/my-research/00_inbox/verify-paper-id.yaml --execute
python tools/wf.py task review my-research verify-paper-id --attempt 1
```

子模型只接收受控 context，结构化结果为 `result` 与 `artifacts`，执行器先保存到 `.runs/<task-id>/attempts/<n>`；manual 整理真实模型输出后使用 `task submit ... --result <file>`，仅保存 response.md 不算提交。

主模型通过 `.runs/<task-id>/reviews/<n>` 的小型评审包验收并按需抽查原文。当前 Codex/GPT 在已有会话中审核，将真实评审文件交 `task review ... --review <file>`；主 API/CLI 评审用 `task review ... --execute --evidence <refs.yaml>`，连接自动来自 orchestrator，不需要 `--main`。refs.yaml 只选择必要 ArtifactRef ID/anchor 片段，执行器按限额展开；API 不因路径引用获得自主读文件能力，无证据不能 accept。执行器管理文件与调度。

完成真实审核并登记 reviews/<n>.yaml 后，才能运行 `task accept my-research verify-paper-id --attempt <n>`；需要返修使用 `task revise ... --review <review.yaml>`。缺 Key 的 manual 同样走结果提交和评审，不能把生成 prompt、mock 或自检当正式完成。可复制任务包、result/review 字段和所有 CLI 见 [模型分工与闭环手册](task-orchestration.md)。

## 分享前

执行 `python tools/wf.py doctor --offline --share-check`，手动确认不上传 `.env`、models.local.yaml、`.runs/`、个人认证及真实研究资料。检查不覆盖 Git 历史和所有秘密；直接压缩也不会应用 .gitignore。Git 提交与推送由使用者自行操作。

更新已有 [GitHub 模板仓库](https://github.com/FengchenOkk/paperlearning-workflow-template) 时，将这版公开模板文件同步到该仓库的本地克隆，保留克隆中的 `.git` 和自己的私有配置，复查 `git status` 与 diff 后自行提交、推送。若当前目录没有 `.git`，它是模板工作区，请在目标仓库的本地克隆中执行 Git；不要直接将含 `.env` 的工作区整目录上传。
