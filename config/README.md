# 本地连接配置

- `models.example.yaml`：可分享的主模型、子模型与路由默认值。具体接入见 [模型接入手册](../workflow/model-setup.md)。
- `zotero.example.yaml`：可选只读文献来源，默认关闭。三种接入见 [Zotero 手册](../workflow/zotero.md)。
- `python tools/wf.py bootstrap` 为缺失配置创建同名 `.local.yaml`，已有文件保留。
- 所有 `.local.yaml` 只在本机使用；密钥只放 `.env` 或系统环境变量，配置通过 `api_key_env` 引用。
- 项目范围的集合、标签及私有复现扩展放各项目 `project.yaml`；不改全局模型分工。
