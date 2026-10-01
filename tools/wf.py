"""论文工作流 CLI；只依赖 PyYAML，所有相对路径基于仓库根目录。"""
import argparse
import copy
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
if sys.version_info < (3, 11):
    raise SystemExit('需要 Python 3.11+；请升级后再执行 bootstrap。')
try:
    import yaml
except ImportError:
    raise SystemExit('请先执行 python -m pip install -r requirements.txt')
try:
    from . import adapters, literature, storage, zotero, knowledge, registry, tasks
except ImportError:
    import adapters, literature, storage, zotero, knowledge, registry, tasks

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ['online-code', 'online-simulation', 'offline-lab', 'hybrid', 'observe-only', 'unreproducible']
PROVENANCE = ['generated_by', 'model_role', 'prompt_version', 'source_refs', 'created_at', 'status']

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path):
    try:data = yaml.safe_load(Path(path).read_text(encoding='utf-8-sig'))
    except yaml.YAMLError:raise ValueError('YAML 格式错误；为避免泄露敏感内容，不显示原始行') from None
    if not isinstance(data, dict):
        raise ValueError(f'需要 YAML 对象：{path}')
    return data

def save(path, data):
    storage.write_text(path,yaml.safe_dump(data, allow_unicode=True, sort_keys=False))

def slug(value):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError('标识符应使用小写字母、数字与单个连字符')
    return value

def paper_key(value):
    # Better BibTeX 的大小写和下划线须原样保留；禁止跨平台不安全文件名。
    if not isinstance(value,str) or not re.fullmatch(r'\w[\w.-]{0,159}',value) or value.endswith('.') or value.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
        raise ValueError('citekey 必须为安全的字母、数字、点、下划线或连字符文件名')
    return value

def contained(base, value):
    base = Path(base).resolve()
    path = (base / value).resolve()
    if not path.is_relative_to(base):
        raise ValueError('路径不能越过指定目录')
    return path

def project(root, name):
    path = contained(root / 'projects', slug(name))
    if not (path / 'project.yaml').is_file():
        raise ValueError('项目不存在')
    return path

def bootstrap(root):
    for name in ['config','workflow','projects','tools','tests']:
        (root/name).mkdir(parents=True,exist_ok=True)
    for source, dest in [('config/models.example.yaml', 'config/models.local.yaml'), ('config/zotero.example.yaml','config/zotero.local.yaml'), ('.env.example', '.env')]:
        if not (root / dest).exists():
            storage.copy_file(root / source, root / dest)
    print('Python 3.11+ 与 PyYAML 可用；目录、配置已准备，已有文件保留，未读取密钥。')
    print('主模型：保留已有 agent 会话，或用 orchestrator.profile 选择 API/CLI Profile。')
    print('子模型：default_subagent_profile 选择独立 Profile；Key 放 .env，变量名与 api_key_env 对应。')
    print('无 Key：保持 manual；其他能读取 AGENTS.md 的 agent 或人工均可接力。')
    print('下一步：python tools/wf.py doctor --offline --share-check；python tools/wf.py demo')
    print('简明接入手册：workflow/model-setup.md；DeepSeek 也支持 ds_apikey。')

def environment(root):
    # 不修改进程环境；每个模型仅在调用瞬间解析自己的变量名和别名。
    return adapters.local_environment(root/'.env')

def models(root):
    environment(root)
    config=load(root/'config/models.local.yaml')
    config.pop('_profiles_resolved',None)
    return normalize_models(root,config)

def reject_credentials(value):
    if isinstance(value,dict):
        if any(str(k).lower() in {'api_key','token','password','secret','authorization','access_token'} for k in value):
            raise ValueError('模型配置不得包含认证字段或密钥值；请使用 api_key_env')
        for item in value.values():reject_credentials(item)
    elif isinstance(value,list):
        for item in value:reject_credentials(item)

def normalize_models(root,config):
    """仅在内存展开 Profile；旧角色直接配置优先，用户文件不改写。"""
    config=copy.deepcopy(config)
    reject_credentials(config)
    if config.get('_profiles_resolved'):return config
    if not isinstance(config.get('orchestrator'),dict):raise ValueError('orchestrator 必须为对象')
    if not isinstance(config.get('subagents'), dict) or not isinstance(config.get('routing'), dict):
        raise ValueError('缺少 subagents/routing')
    # 旧 local 配置无需手工重写；仅在内存中补充新模式，不覆盖现有值。
    defaults = load(root / 'config/models.example.yaml')
    settings=config.setdefault('settings',{})
    if not isinstance(settings,dict):raise ValueError('settings 必须为对象')
    for key, value in defaults.get('settings',{}).items():
        settings.setdefault(key,copy.deepcopy(value))
    settings.setdefault('default_subagent_profile','manual')
    if not isinstance(settings['default_subagent_profile'],str):raise ValueError('默认 Profile 必须为字符串')
    profiles=copy.deepcopy(defaults['model_profiles'])
    for field in ['subagent_profiles','model_profiles']:
        group=config.get(field,{})
        if not isinstance(group,dict):raise ValueError(field+' 必须为对象')
        for name,item in group.items():
            if isinstance(item,dict) and isinstance(profiles.get(name),dict):profiles[name].update(copy.deepcopy(item))
            else:profiles[name]=copy.deepcopy(item)
    config['model_profiles']=profiles
    config['subagent_profiles']=profiles  # 旧调用方的只读兼容视图；新模板只维护共享池。
    manual=defaults['model_profiles']['manual']
    if not isinstance(profiles['manual'],dict) or profiles['manual'].get('adapter')!='manual':
        raise ValueError('manual Profile 必须保持 manual 适配器')
    for role, raw in list(config['subagents'].items()):
        if not isinstance(raw,dict):raise ValueError('子模型配置必须为对象')
        slug(role)
        name=raw.get('profile') or settings['default_subagent_profile']
        profile=profiles.get(name) if isinstance(name,str) else None
        legacy='adapter' in raw and not raw.get('profile')
        item=dict(copy.deepcopy(manual),enabled=defaults['subagents'].get(role,{}).get('enabled',True))
        if not legacy and isinstance(profile,dict):item.update(copy.deepcopy(profile))
        item.update({k:v for k,v in raw.items() if k!='profile'})
        item['requested_profile']='legacy-'+role if legacy else name if isinstance(name,str) else '[无效 Profile]'
        item['profile']=item['requested_profile']
        item['_env_file']=str(root/'.env')
        if not legacy and not isinstance(profile,dict):item['_profile_issue']='Profile 未定义或格式错误'
        config['subagents'][role]=item
    raw=config['orchestrator']
    name=raw.get('profile')
    profile=profiles.get(name) if isinstance(name,str) else None
    main=dict(copy.deepcopy(manual),enabled=True)
    if isinstance(profile,dict):
        main.update(copy.deepcopy(profile))
        main.update({k:v for k,v in raw.items() if k!='profile'})
    else:main.update(copy.deepcopy(raw))
    main['profile']=name or 'legacy-orchestrator'
    main['requested_profile']=main['profile']
    if name and not isinstance(profile,dict) and not raw.get('adapter'):main['_profile_issue']='主模型 Profile 未定义或格式错误'
    main['_env_file']=str(root/'.env')
    main['auth']='api_key' if isinstance(main['adapter'],str) and main['adapter'] in {'openai_compatible','anthropic'} else 'external'
    config['orchestrator']=main
    if not (root/'workflow/prompts/orchestrator.md').is_file():raise ValueError('缺少主模型 prompt')
    for key, value in defaults['routing'].items():
        config['routing'].setdefault(key, value)
    for key, value in defaults.get('fallback', {}).items():
        config.setdefault('fallback', {}).setdefault(key, value)
    for role, item in config['subagents'].items():
        slug(role)
        if not (root / 'workflow/prompts' / (role + '.md')).is_file():
            raise ValueError('缺少角色 prompt')
    for role in config['routing'].values():
        resolve_role(config, role)
    config['_profiles_resolved']=True
    return config

def execution_settings(config,role,use_main=False):
    """主/子模型共享适配器；不可用时只降级 manual，不切换外部服务。"""
    item=copy.deepcopy(config['orchestrator'] if use_main else config['subagents'][role])
    reason=item.get('_profile_issue')
    if item['adapter']=='codex' and not use_main:reason='codex 仅用于已有主会话，子任务请选择 API/CLI/manual'
    if not reason:
        try:
            adapters.check(item)
            if item['adapter']=='command' and not shutil.which(item['command'][0]):reason='外部命令不存在'
        except (ValueError,TypeError):reason='配置无效或所需密钥未设置'
    if reason:
        manual=config.get('model_profiles',{}).get('manual',{})
        item=dict(adapter='manual',timeout_seconds=600,max_concurrency=1,privacy='local',**{k:v for k,v in manual.items() if k not in {'adapter','timeout_seconds','max_concurrency','privacy'}})
        item.update(enabled=True,profile='manual',fallback_reason=reason)
    else:item['profile']=item.get('requested_profile',item.get('profile','legacy-'+role))
    return item

def resolve_role(config, role):
    seen = set()
    while role not in seen:
        seen.add(role)
        item = config['subagents'].get(role)
        if item and item.get('enabled', True):
            return role
        next_role = config.get('fallback', {}).get(role)
        if not next_role:
            raise ValueError(f'角色 {role} 未配置或已禁用，且无可用回退')
        role = next_role
    raise ValueError('角色回退存在循环')

def role_prompt(root, role, requested_role=None):
    """统一规则只拼接一次；保留旧工作流文档和角色文件的使用方式。"""
    prompt = (root / 'workflow/prompts' / (slug(role) + '.md')).read_text(encoding='utf-8')
    rules_path = root / 'workflow/README.md'
    if rules_path.is_file():
        rules = rules_path.read_text(encoding='utf-8')
        match = re.search(r'<!-- wf:task-rules:begin -->\s*(.*?)\s*<!-- wf:task-rules:end -->',rules,re.S)
        if match:
            prompt = match.group(1) + '\n\n' + prompt
    if requested_role and role != requested_role:
        prompt += '\n\n' + (root / 'workflow/prompts' / (slug(requested_role)+'.md')).read_text(encoding='utf-8')
    return prompt

def share_check(root,scan=False):
    """只读分享检查；不输出匹配到的密钥或读取 Git 认证配置。"""
    def git(*args):
        if not shutil.which('git'):return None
        try:
            result=subprocess.run(['git','-C',str(root),*args],capture_output=True,timeout=15)
            return result if result.returncode==0 else None
        except (OSError,subprocess.TimeoutExpired):return None
    repo=git('rev-parse','--is-inside-work-tree')
    listed=git('ls-files','-z','--','.') if repo else None
    tracked=set(listed.stdout.decode('utf-8',errors='replace').split('\0')) if listed else set()
    issues=[]
    rules=(root/'.gitignore').read_text(encoding='utf-8-sig').splitlines() if (root/'.gitignore').exists() else []
    print('分享检查：')
    for rel in ['.env','config/models.local.yaml','config/zotero.local.yaml']:
        ignored=git('check-ignore','--no-index','--',rel) if repo else None
        if rel in tracked:status='存在风险：已被 Git 追踪';issues.append(rel)
        elif ignored:status='已忽略、未追踪'
        elif not repo and rel in rules:status='忽略规则已声明；当前无 Git 仓库，打包时需排除'
        else:status='存在风险：缺少有效忽略规则';issues.append(rel)
        print('  '+rel+': '+status)
    if repo and listed is None:issues.append('无法检查 Git 追踪状态')
    if scan:
        private=lambda rel: rel in {'.env','config/models.local.yaml','config/zotero.local.yaml','auth.json'} or Path(rel).name.endswith('.local.yaml') or (Path(rel).name.startswith('.env.') and Path(rel).name!='.env.example') or any(x in Path(rel).parts for x in {'.runs','source','01_source','private','raw-data','data','tmp','cache'}) or Path(rel).suffix.lower() in {'.pdf','.pem','.key','.csv','.h5','.hdf5','.pt','.pth','.ckpt','.parquet','.npy','.npz','.pkl','.pickle','.zip','.safetensors'}
        unsafe=[rel for rel in tracked if rel and private(rel) and Path(rel).name!='.gitkeep']
        issues.extend(unsafe)
        for rel in sorted(unsafe):print('  已追踪私有资料：'+rel)
        pattern=re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b|\bAKIA[A-Z0-9]{16}\b|'
            r'(?i:\b(?:[A-Z0-9_]*API_KEY|access_token|authorization)[\"\']?\s*[:=]\s*'
            r'(?:\"[A-Za-z0-9_-]{24,}\"|\'[A-Za-z0-9_-]{24,}\'|[A-Za-z0-9_-]{24,}(?=\s*(?:$|#))))')
        skipped=0;hits=0;fixtures=0
        for path in root.rglob('*'):
            if not path.is_file() or path.is_symlink():continue
            rel=path.relative_to(root).as_posix()
            if any(x in path.relative_to(root).parts for x in {'.git','.codex','.agents','.aws','__pycache__'}):continue
            if private(rel) and rel not in tracked:continue
            if path.stat().st_size>1_000_000:skipped+=1;continue
            try:content=path.read_text(encoding='utf-8-sig')
            except (UnicodeError,OSError):continue
            matches=[]
            for i,line in enumerate(content.splitlines(),1):
                tokens=pattern.findall(line)
                # ARS v3.22.2 中人工核对过的测试假 Key：只匹配此文件、此摘要；不豁免测试目录。
                confirmed=rel=='workflow/vendor/academic-research-suite/codex/tests/test_hook_wrapper.py'
                known=lambda token: confirmed and hashlib.sha256(token.encode()).hexdigest()=='aafd1d9e01724fb3ad013b364ca5a6995f2c9e6ab7c70c7f468cf3043df9bd45'
                fixtures+=sum(known(token) for token in tokens)
                if any(not known(token) for token in tokens):matches.append(str(i))
            if matches:
                hits+=len(matches);issues.append(rel)
                print('  疑似密钥：'+rel+'，行 '+','.join(matches[:10])+'（内容已隐藏）')
        print(f'  明显密钥风险：{hits} 处；已核对的 ARS 测试占位：{fixtures} 处；跳过大文件 {skipped} 个。')
        print('  不扫描 Git 历史；本地私有文件不属于分享集；此模式检查不能代替人工脱敏。')
    print('  打包或复制文件夹不会应用 .gitignore；排除 .env、local 配置、.runs、原文和私密数据。')
    return not issues

def doctor(root, offline=False, share=False):
    for name in ['config', 'workflow', 'projects', 'tools', 'tests']:
        if not (root / name).is_dir():
            raise ValueError(f'缺少目录 {name}')
    extras = [p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith('.') and p.name not in ['config','workflow','projects','tools','tests']]
    if extras:
        raise ValueError('多余顶层目录：' + ', '.join(extras))
    for rel in ['workflow/README.md', 'workflow/literature.md', 'workflow/reproduction.md', 'workflow/schemas.yaml', 'workflow/layouts/project/project.yaml']:
        if not (root / rel).is_file():
            raise ValueError(f'缺少文件 {rel}')
    config = models(root)
    main=config['orchestrator']
    effective=execution_settings(config,'orchestrator',use_main=True)
    print(f'主模型：adapter={main["adapter"]}，auth={main["auth"]}，profile={main["profile"]} → {effective["profile"]}，model={main.get("model","inherit")}')
    if effective.get('fallback_reason'):print('  回退原因：'+effective['fallback_reason'])
    elif main['adapter'] in {'openai_compatible','anthropic'}:print('  API 配置就绪（未验证真实连接）；使用 run --main --execute。')
    print('  codex 命令：'+('存在' if shutil.which('codex') else '不存在；可继续 manual 或使用已有桌面会话/其他 agent'))
    print('  建议：CLI 用户自行在本机 codex login；本检查不读取认证信息。')
    print('子模型：')
    for role, item in config['subagents'].items():
        if not item.get('enabled',True):print(f'  {role}: profile={item["profile"]}，未启用');continue
        effective=execution_settings(config,role)
        detail='无需 Key，manual 可用' if effective['adapter']=='manual' else '配置就绪（未验证真实连接）'
        print(f'  {role}: profile={item["profile"]} → {effective["profile"]}，{detail}')
        if effective.get('fallback_reason'):print('    回退原因：'+effective['fallback_reason'])
    print('共享 API Profiles：')
    for name,profile in config['model_profiles'].items():
        if not isinstance(profile,dict) or profile.get('adapter') not in {'openai_compatible','anthropic'}:continue
        candidate=dict(profile,enabled=True,timeout_seconds=profile.get('timeout_seconds',600),_env_file=str(root/'.env'))
        try:adapters.check(candidate,require_credentials=False);valid=True
        except (ValueError,TypeError):valid=False
        print('  '+str(name)+': base_url='+ (str(profile.get('base_url')) if valid else '[配置无效，地址已隐藏]')+'，model='+str(profile.get('model')))
        print('    api_key_env: '+(str(profile.get('api_key_env')) if valid else '[配置无效，变量名已隐藏]')+'；环境变量：'+('已设置' if valid and adapters.key_value(candidate) else '未设置'))
    print('  建议：没有 Key 时继续使用 manual 即可；填写密钥不会自动启用未选择的 Profile。')
    if (root/'config/zotero.example.yaml').is_file():
        try:
            zconfig=zotero.config(root,sys.modules[__name__])
            print(f'Zotero：enabled={zconfig["enabled"]}；mode={zconfig["mode"]}；只读、可选（本检查不联网）。')
        except (ValueError,OSError):
            print('Zotero 配置未就绪；请检查 zotero.local.yaml，手动工作流仍可用，本检查不联网。')
    safe=share_check(root,scan=share)
    if share and not safe:raise ValueError('分享检查发现风险；请按报告排除文件或撤销泄露密钥')
    print('检查完成：未访问网络。缺 Codex 或 Key 不阻止 manual；主模型配置不修改当前会话。')

def init(root, name, title):
    target = contained(root / 'projects', slug(name))
    if target.exists():
        raise ValueError('项目已存在，不覆盖')
    storage.copy_tree(root / 'workflow/layouts/project', target)
    for rel in ['00_inbox', '10_literature/papers', '10_literature/concepts', '30_outputs']:
        contained(target, rel).mkdir(parents=True, exist_ok=True)
    data = load(target / 'project.yaml')
    data.update(slug=name, id='project:'+name, type='project', links=[], title=title, created_at=now())
    save(target / 'project.yaml', data)
    stamp_markdown(target / '10_literature/matrix.md', 'literature-reader')
    index(root, name)
    return target

def provenance(role='orchestrator'):
    return dict(generated_by='wf', model_role=role, prompt_version='v1', source_refs=[], created_at=now(), status='draft')

def stamp_markdown(path, role):
    text = path.read_text(encoding='utf-8')
    if text.startswith('---\n'):
        original, body = literature.markdown(path)
        info = dict(original, **provenance(role))
        if path.name in ['reading.md','translation.md']:
            info.pop('status', None)
            info['prompt_version'] = 'v2'
        literature.write_markdown(path, info, body)

def new_paper(root, name, key, refresh=True):
    p = project(root, name)
    target = contained(p / '10_literature/papers', paper_key(key))
    if target.exists() or any(f.name.casefold()==key.casefold() for f in target.parent.iterdir()):
        raise ValueError('论文已存在，不覆盖')
    storage.copy_tree(root / 'workflow/layouts/paper', target)
    contained(target, '01_source').mkdir(parents=True, exist_ok=True)
    data = load(target / 'meta.yaml')
    data.update(provenance(), citekey=key, id='paper:'+key, type='paper', project_id=load(p/'project.yaml').get('id','project:'+name), links=[], status='unread', updated_at=now(), prompt_version='v2')
    save(target / 'meta.yaml', data)
    analysis_path = target/literature.PAPER_FILES['analysis.yaml']
    data = load(analysis_path)
    data.update(provenance('literature-reader'), paper=key, id='analysis:'+key, type='analysis', paper_id='paper:'+key, links=[], prompt_version='v2')
    data.pop('status', None)
    save(analysis_path, data)
    for filename in ['reading.md','translation.md']:
        path=target/literature.PAPER_FILES[filename]
        stamp_markdown(path, 'literature-reader')
        text = path.read_text(encoding='utf-8').replace('：TODO(user)', '：'+key, 1)
        storage.write_text(path,text)
    if refresh:
        index(root, name)
    return target

def new_concept(root, name, concept_id):
    p = project(root, name)
    library = literature.Library(root, p, sys.modules[__name__])
    library.ensure_project_files()
    target = library.new_concept(concept_id)
    index(root, name)
    return target

def new_claim(root, name, key, claim_slug):
    p = project(root, name)
    machine=registry.build(root,p,sys.modules[__name__])
    try:paper_ref=registry.resolve(p,'paper:'+paper_key(key),sys.modules[__name__],index=machine)
    except ValueError:
        raise ValueError('请先创建关联论文')
    key=paper_ref['id'].partition(':')[2]
    claim_id = key + '--' + slug(claim_slug)
    target = contained(p / '20_reproduction', claim_id)
    if target.exists():
        raise ValueError('claim 已存在，不覆盖')
    storage.copy_tree(root / 'workflow/layouts/claim', target)
    for rel in ['online', 'lab', 'results']:
        contained(target, rel).mkdir(parents=True, exist_ok=True)
    data = load(target / 'claim.yaml')
    data.update(provenance('reproduction-analyst'), claim_id=claim_id, id='claim:'+key+':'+claim_slug, type='claim', links=[], formula_ids=[], concept_ids=[], paper_citekey=key, paper_id=paper_ref['id'], status='pending')
    save(target / 'claim.yaml', data)
    for filename in ['feasibility.md', 'plan.md']:
        stamp_markdown(target / filename, 'reproduction-analyst')
    index(root, name)
    return target

def index(root, name, dry_run=False):
    literature.Library(root, project(root, name), sys.modules[__name__],dry_run).index()
    return registry.build(root,project(root,name),sys.modules[__name__],dry_run=dry_run)

def migrate(root,name,dry_run=False):
    report=literature.Library(root,project(root,name),sys.modules[__name__],dry_run).migrate()
    if not report['generated_from'] and not report['errors']:
        print('未发现需要迁移的旧论文；已有编号文件保留。')
    return report

def graph(root,name,dry_run=False):
    library=literature.Library(root,project(root,name),sys.modules[__name__],dry_run)
    return knowledge.generate(library)

def contract(root, kind, data):
    if kind=='analysis' and isinstance(data,dict):
        data=copy.deepcopy(data)
        for item in data.get('formulas',[]):
            if isinstance(item,dict) and 'plain_meaning' not in item and 'meaning' in item:
                item['plain_meaning']=item['meaning']
    schema = load(root / 'workflow/schemas.yaml')['contracts'][kind]
    def check(rules, value, path):
        types = rules.get('type', [])
        types = [types] if isinstance(types, str) else types
        matches = {'string': isinstance(value,str), 'array': isinstance(value,list), 'object': isinstance(value,dict),
                   'boolean': isinstance(value,bool),
                   'null': value is None, 'number': isinstance(value,(int,float)) and not isinstance(value,bool),
                   'integer': isinstance(value,int) and not isinstance(value,bool)}
        if types and not any(matches.get(t,False) for t in types):raise ValueError(f'{path} 类型错误')
        if 'enum' in rules and value not in rules['enum']:raise ValueError(f'{path} 值不合法')
        if isinstance(value,dict):
            for key in rules.get('required',[]):
                if key not in value:raise ValueError(f'{path} 缺少字段 {key}')
            for key, sub in rules.get('properties',{}).items():
                if key in value:check(sub,value[key],path+'.'+key)
        if isinstance(value,list) and 'items' in rules:
            for i,item in enumerate(value):check(rules['items'],item,f'{path}[{i}]')
        if isinstance(value,(int,float)) and not isinstance(value,bool):
            if 'minimum' in rules and value<rules['minimum'] or 'maximum' in rules and value>rules['maximum']:
                raise ValueError(f'{path} 超出范围')
    check(schema,data,kind)

def refs(p, data):
    if isinstance(data, dict):
        sources = data.get('source_refs', [])
        if not isinstance(sources, list) or not all(isinstance(ref,str) for ref in sources):
            raise ValueError('source_refs 必须为字符串列表')
        for ref in sources:
            path = literature.resolve_path(p, ref.split('#', 1)[0],sys.modules[__name__])
            if not path.is_file():
                raise ValueError(f'来源文件不存在：{ref}')
        for key, value in data.items():
            if key != 'source_refs': refs(p, value)
    elif isinstance(data, list):
        for value in data: refs(p, value)

def validate(root, name):
    p = project(root, name)
    for rel in ['project.yaml','research-profile.yaml','INDEX.md','00_inbox','10_literature/papers','10_literature/matrix.md','20_reproduction/README.md','30_outputs']:
        if not (p / rel).exists():
            raise ValueError(f'缺少 {rel}')
    data = load(p / 'project.yaml')
    zotero.project_options(p,sys.modules[__name__])
    reproduction=data.get('reproduction',{'profile':'generic','private_extension':'TODO(user)','extension_data':{}})
    if not isinstance(reproduction,dict) or not isinstance(reproduction.get('profile'),str) or not isinstance(reproduction.get('extension_data'),dict):
        raise ValueError('reproduction 私有扩展接口格式错误')
    for key in ['slug','title','stage','current_claim','next_action','created_at']:
        if key not in data:
            raise ValueError(f'project 缺少 {key}')
    profile = load(p / 'research-profile.yaml')
    for key in ['direction','goal','resources','constraints','preferences']:
        if key not in profile:
            raise ValueError(f'研究画像缺少 {key}')
    for section, keys in {'resources':['compute','data','software','lab_access','equipment','budget','time'],
                          'constraints':['ethics','privacy'], 'preferences':['prefer_online','allow_simulation','allow_offline_lab']}.items():
        if not isinstance(profile[section], dict) or any(k not in profile[section] for k in keys):
            raise ValueError(f'研究画像 {section} 字段不完整')
    literature.Library(root,p,sys.modules[__name__]).validate()
    machine=registry.build(root,p,sys.modules[__name__],write=False)
    for file in p.rglob('*.yaml'):
        if '.runs' in file.parts:
            continue
        try:
            item = yaml.safe_load(file.read_text(encoding='utf-8-sig'))
        except yaml.YAMLError:
            raise ValueError('YAML 格式错误：'+file.relative_to(p).as_posix()+'；原始内容已隐藏') from None
        refs(p, item)
        if file.name == 'claim.yaml':
            contract(root, 'claim', item)
            paper_ref=item.get('paper_id') or 'paper:'+paper_key(item['paper_citekey'])
            try:registry.resolve(p,paper_ref,sys.modules[__name__],index=machine)
            except ValueError:raise ValueError('claim 关联论文错误') from None
            if not item.get('id') and item['claim_id'] != file.parent.name:raise ValueError('claim 标识错误')
            for rel in ['feasibility.md','plan.md','online','lab','results']:
                if not (file.parent / rel).exists():
                    raise ValueError(f'claim 缺少 {rel}')
    if data['current_claim'] is not None:
        if not (contained(p / '20_reproduction', data['current_claim']) / 'claim.yaml').exists():
            try:ref=registry.resolve(p,data['current_claim'],sys.modules[__name__],index=machine)
            except ValueError:raise ValueError('current_claim 不存在') from None
            if ref['type']!='claim':raise ValueError('current_claim 未指向claim')
    print('项目校验通过；TODO 与空来源表示待补充，不代表证据已验证。')

def run(root, name, task_path, execute_external=False, config_override=None, use_main=False):
    p = project(root, name)
    task = load(contained(root, task_path))
    if task.get('inputs') and all(isinstance(x,dict) for x in task['inputs']):
        if use_main:raise ValueError('ArtifactRef 新任务由子模型执行；主模型请使用 task review')
        return tasks.execute(root,p,task_path,sys.modules[__name__],execute_external,config_override)
    contract(root, 'task', task)
    slug(task['task_id'])
    config = normalize_models(root,config_override) if config_override is not None else models(root)
    task_type = task.get('task_type', task.get('context',{}).get('task_type'))
    if task.get('task_type') and task.get('context',{}).get('task_type') and task['task_type'] != task['context']['task_type']:
        raise ValueError('顶层 task_type 与 context.task_type 不一致')
    routed_role = config['routing'].get(task_type)
    if routed_role and routed_role != task['role']:
        raise ValueError('任务角色与 routing 不一致')
    requested_role = task['role']
    role = 'orchestrator' if use_main else resolve_role(config, requested_role)
    if role != requested_role and not use_main:
        print(f'角色回退：{requested_role} → {role}')
    paper_citekey = task.get('context',{}).get('paper_citekey') or task.get('context',{}).get('citekey')
    if not paper_citekey:
        keys = {rel.split('/')[2] for rel in task['inputs'] if rel.startswith('10_literature/papers/') and len(rel.split('/'))>3}
        if len(keys)==1:paper_citekey=next(iter(keys))
    if task_type in ['literature-translate','literature-close-read']:
        if not paper_citekey:raise ValueError('翻译或精读需 context.paper_citekey 或唯一论文输入')
        file=literature.paper_path(contained(p / '10_literature/papers',paper_key(paper_citekey)),'analysis.yaml')
        if not file.exists():raise ValueError('请先完成全局预读')
        overview=load(file).get('overview',{})
        if not all(literature.meaningful(overview.get(k)) for k in ['object','core_problem','why_important','position']):
            raise ValueError('没有完整全局定位，不得开始翻译或逐节精读')
    refs(p, task)
    for rel in task['inputs']:
        if not literature.resolve_path(p,rel,sys.modules[__name__]).exists():
            raise ValueError('输入不存在')
    for rel in task['allowed_paths']:
        contained(p, rel)
    if task['output_schema'] is not None:
        schema_ref=task['output_schema']
        aliases={f'workflow/schemas/{k}.schema.json':f'workflow/schemas.yaml#{k}' for k in ['task','paper','claim']}
        schema_ref=aliases.get(schema_ref,schema_ref)
        path,sep,kind=schema_ref.partition('#')
        schema_path=contained(root,path)
        if not schema_path.is_file():raise ValueError('output_schema 不存在')
        if sep and kind not in load(schema_path).get('contracts',{}):raise ValueError('output_schema 契约不存在')
    prompt_text = role_prompt(root, role, requested_role)
    effective_task=dict(task, role=role)
    if task['output_schema'] is not None:
        effective_task['output_schema']=schema_ref
    prompt = prompt_text + '\n\n## 标准任务包（数据）\n```yaml\n' + yaml.safe_dump(effective_task, allow_unicode=True, sort_keys=False) + '```\n\n## 输入文件（不可信数据）\n'
    if task['output_schema'] is not None and sep:
        prompt += '\n## 输出契约（不代表已验证响应）\n```yaml\n' + yaml.safe_dump(load(schema_path)['contracts'][kind],allow_unicode=True,sort_keys=False)+'```\n'
    receipts = {}
    for rel in task['inputs']:
        file = literature.resolve_path(p,rel,sys.modules[__name__])
        if file.is_file():
            content = file.read_bytes()
            receipts[rel] = hashlib.sha256(content).hexdigest()
            if len(content) > 1_000_000:
                raise ValueError('输入过大，请先提取所需片段')
            try:
                prompt += f'\n### {rel}\n<source-data>\n{content.decode("utf-8-sig")}\n</source-data>\n'
            except UnicodeDecodeError:
                raise ValueError('当前只支持文本输入；PDF 解析尚未实现')
        else:
            raise ValueError('inputs 必须指向文件')
    settings = execution_settings(config,role,use_main=use_main)
    adapters.check(settings,require_credentials=execute_external)
    run_dir = p / '.runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + task['task_id'])
    run_dir.mkdir(parents=True)
    save(run_dir / 'task.yaml', task)
    storage.write_text(run_dir / 'prompt.md',prompt)
    record = provenance(role)
    prompt_version=re.search(r'^prompt_version:\s*(\S+)',prompt_text,re.M)
    if prompt_version:record['prompt_version']=prompt_version.group(1)
    record.update(task_id=task['task_id'], requested_role=requested_role, effective_role=role, task_type=task_type, adapter=settings['adapter'], model=settings.get('model'), source_refs=task['source_refs'], input_hashes=receipts,
                  prompt_sha256=hashlib.sha256(prompt_text.encode()).hexdigest(), status='prepared', execute_external=execute_external,
                  orchestrator=config['orchestrator'], allowed_paths_enforced=False)
    requested=config['orchestrator'] if use_main else config['subagents'][role]
    record.update(requested_profile=requested['profile'],effective_profile=settings['profile'],
                  requested_adapter=requested['adapter'],requested_model=requested.get('model'),
                  execution_target='main' if use_main else 'subagent')
    if settings.get('fallback_reason'):record['fallback_reason']=settings['fallback_reason']
    if settings.get('request_options'):
        record['request_options']=settings['request_options']
    save(run_dir / 'run.yaml', record)
    try:
        status, response = adapters.execute(settings, prompt, p, execute_external)
        record['status'] = status
        if response is not None:
            storage.write_text(run_dir / 'response.md',response)
    except Exception as error:
        record['error_type'] = type(error).__name__
        if settings['adapter'] in {'command','openai_compatible','anthropic'}:
            record.update(status='waiting-manual',effective_profile='manual',adapter='manual',model=None,
                          attempted_profile=settings['profile'],attempted_adapter=settings['adapter'],attempted_model=settings.get('model'),
                          fallback_reason='外部调用失败；保留 prompt，人工接力，不自动重试付费请求')
            print('外部调用失败，已回退 manual；异常正文不记录。')
        else:
            record['status'] = 'failed'
            raise ValueError(f'适配器失败（{type(error).__name__}）；请检查配置，日志不记录密钥或原始异常') from None
    finally:
        record['finished_at'] = now()
        save(run_dir / 'run.yaml', record)
        # 时间更新不宣称内容已完成；进度由主模型核验后写入 meta。
        if paper_citekey:
            meta_path=contained(p / '10_literature/papers',paper_key(paper_citekey))/'meta.yaml'
            if meta_path.exists():
                meta=load(meta_path);meta['updated_at']=now();save(meta_path,meta)
        index(root,name)
    print(f'任务状态：{record["status"]}；目录：{run_dir}')
    return run_dir

def demo(root):
    with tempfile.TemporaryDirectory(prefix='paper-workflow-') as temp:
        sandbox = Path(temp)
        (sandbox/'config').mkdir()
        for name in ['models','zotero']:
            storage.copy_file(root/f'config/{name}.example.yaml',sandbox/f'config/{name}.example.yaml')
        storage.copy_tree(root/'workflow/layouts',sandbox/'workflow/layouts')
        storage.copy_tree(root/'workflow/prompts',sandbox/'workflow/prompts')
        for name in ['README.md','schemas.yaml']:
            storage.copy_file(root/'workflow'/name,sandbox/'workflow'/name)
        init(sandbox,'demo','本地 mock 演示；非真实研究')
        new_paper(sandbox,'demo','demo-paper')
        new_concept(sandbox,'demo','demo-concept')
        new_claim(sandbox,'demo','demo-paper','main-claim')
        project_path=project(sandbox,'demo')
        export=project_path/'00_inbox/zotero-demo.json'
        storage.copy_file(root/'tests/fixtures/zotero/better-bibtex.json',export)
        zconfig=load(sandbox/'config/zotero.example.yaml')
        zconfig['zotero'].update(enabled=True,mode='export')
        zconfig['zotero']['export']['path']=str(export)
        save(sandbox/'config/zotero.local.yaml',zconfig)
        report=zotero.sync(sandbox,project_path,sys.modules[__name__])
        if len(report['created'])!=2 or report['errors']:
            raise ValueError('Zotero fixture 演示失败')
        for key in report['created']:
            folder=project_path/'10_literature/papers'/key
            meta=load(folder/'meta.yaml');meta.update(paper_role='survey',concept_ids=['demo-concept'])
            save(folder/'meta.yaml',meta)
            analysis=load(folder/'04_analysis/analysis.yaml')
            analysis['first_principles']=[dict(id='demo-principle',statement='MOCK：仅演示关联，不是科学原理。',
                 concept_ids=['demo-concept'],source_refs=['00_inbox/zotero-demo.json'])]
            analysis['review_similarity']=dict(core_problem='mock workflow example',method_summary='mock local fixture',
                                               key_concepts=['demo-concept'])
            save(folder/'04_analysis/analysis.yaml',analysis)
        graph(sandbox,'demo')
        index(sandbox,'demo')
        validate(sandbox,'demo')
        task=load(root/'workflow/layouts/task.yaml')
        task.update(task_id='demo-task',objective='演示空模型流程',inputs=['research-profile.yaml'],source_refs=['research-profile.yaml'])
        save(sandbox/'task.yaml',task)
        config=load(root/'config/models.example.yaml')
        config['subagents'][task['role']]['adapter']='mock'
        result=run(sandbox,'demo','task.yaml',config_override=config)
        if load(result/'run.yaml')['status']!='mock':
            raise ValueError('演示失败')
    print('完整 mock 演示通过：创建论文 → Zotero 导出同步 → 知识图谱 → validate → mock 任务；'
          '未联网、未调用真实模型，临时目录已清理。')

def main(argv=None):
    parser = argparse.ArgumentParser(description='论文阅读与复现工作流')
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('bootstrap')
    doc = sub.add_parser('doctor'); doc.add_argument('--offline', action='store_true');doc.add_argument('--share-check',action='store_true')
    cmd = sub.add_parser('init'); cmd.add_argument('slug'); cmd.add_argument('--title', required=True)
    cmd = sub.add_parser('new'); children = cmd.add_subparsers(dest='kind', required=True)
    for kind in ['paper','claim','concept']:
        child = children.add_parser(kind); child.add_argument('project'); child.add_argument('citekey')
        if kind == 'claim': child.add_argument('claim_slug')
    for name in ['index','migrate','graph']:
        cmd = sub.add_parser(name); cmd.add_argument('project')
        cmd.add_argument('--dry-run',action='store_true')
        if name=='index':cmd.add_argument('--json',action='store_true',help='重建稳定 ID 机器索引（普通 index 也会生成）')
    cmd=sub.add_parser('validate');cmd.add_argument('project',nargs='?');cmd.add_argument('--links',action='store_true');cmd.add_argument('--contracts',action='store_true')
    cmd=sub.add_parser('context');cmd.add_argument('project');cmd.add_argument('task_id')
    cmd=sub.add_parser('task');tsub=cmd.add_subparsers(dest='task_action',required=True)
    tr=tsub.add_parser('run');tr.add_argument('project');tr.add_argument('task');tr.add_argument('--execute',action='store_true')
    tr=tsub.add_parser('status');tr.add_argument('project');tr.add_argument('task_id',nargs='?')
    for action in ['submit','review','accept','revise']:
        tr=tsub.add_parser(action);tr.add_argument('project');tr.add_argument('task_id');tr.add_argument('--attempt',required=True,type=int)
        if action=='submit':tr.add_argument('--result',required=True)
        if action in ['review','revise']:tr.add_argument('--review',required=action=='revise')
        if action=='review':tr.add_argument('--execute',action='store_true');tr.add_argument('--evidence',help='按需抽查 YAML refs ArtifactRef 片段，不全量上传论文')
        if action=='revise':tr.add_argument('--execute',action='store_true',help='授权返修失败后的主 API/CLI 修复调用；已有会话/manual生成接力包')
    z = sub.add_parser('zotero'); zsub=z.add_subparsers(dest='zotero_action',required=True)
    zsub.add_parser('doctor')
    zs=zsub.add_parser('status');zs.add_argument('project')
    zs=zsub.add_parser('sync');zs.add_argument('project');policy=zs.add_mutually_exclusive_group();policy.add_argument('--dry-run',action='store_const',const=True,default=None);policy.add_argument('--apply',dest='dry_run',action='store_const',const=False)
    cmd = sub.add_parser('run'); cmd.add_argument('project'); cmd.add_argument('task'); cmd.add_argument('--execute', action='store_true', help='明确授权命令或网络调用；默认 dry-run');cmd.add_argument('--main',action='store_true',help='用已配置的主模型执行同一任务包；默认使用子模型')
    sub.add_parser('demo')
    args = parser.parse_args(argv)
    try:
        if args.action == 'bootstrap': bootstrap(ROOT)
        elif args.action == 'doctor': doctor(ROOT, args.offline,args.share_check)
        elif args.action == 'init': init(ROOT, args.slug, args.title)
        elif args.action == 'new':
            if args.kind == 'paper': new_paper(ROOT, args.project, args.citekey)
            elif args.kind == 'concept': new_concept(ROOT, args.project, args.citekey)
            else: new_claim(ROOT, args.project, args.citekey, args.claim_slug)
        elif args.action == 'index': index(ROOT, args.project,args.dry_run)
        elif args.action == 'migrate': migrate(ROOT,args.project,args.dry_run)
        elif args.action == 'graph': graph(ROOT,args.project,args.dry_run)
        elif args.action == 'zotero':
            if args.zotero_action=='sync':zotero.sync(ROOT,project(ROOT,args.project),sys.modules[__name__],args.dry_run)
            else:zotero.status(ROOT,project(ROOT,args.project) if args.zotero_action=='status' else None,sys.modules[__name__],args.zotero_action=='doctor')
        elif args.action == 'validate':
            if args.contracts:
                tasks.contracts(ROOT,sys.modules[__name__]);print('任务合同与 routing 校验通过。')
            if args.project:
                if args.links:
                    machine=registry.build(ROOT,project(ROOT,args.project),sys.modules[__name__],write=False)
                    issues=sorted(set(machine.get('issues',[])+registry.validate(machine,project(ROOT,args.project),sys.modules[__name__])))
                    if issues:raise ValueError('连接校验失败：\n'+'\n'.join(issues))
                    print('稳定 ID 与连接校验通过。')
                else:validate(ROOT,args.project)
            elif not args.contracts:raise ValueError('validate 需要 project 或 --contracts')
        elif args.action == 'context':
            print(tasks.context(ROOT,project(ROOT,args.project),args.task_id,sys.modules[__name__]))
        elif args.action == 'task':
            p=project(ROOT,args.project);ops=sys.modules[__name__]
            if args.task_action=='run':print(tasks.execute(ROOT,p,args.task,ops,args.execute))
            elif args.task_action=='status':print(yaml.safe_dump(tasks.statuses(p,args.task_id,ops),allow_unicode=True,sort_keys=False))
            elif args.task_action=='submit':print(tasks.submit(ROOT,p,args.task_id,args.attempt,load(contained(ROOT,args.result)),ops)['status'])
            elif args.task_action=='review':print(tasks.review(ROOT,p,args.task_id,args.attempt,ops,args.review,args.execute,evidence_file=args.evidence))
            elif args.task_action=='accept':print(tasks.accept(ROOT,p,args.task_id,args.attempt,ops)['status'])
            elif args.task_action=='revise':print(tasks.revise(ROOT,p,args.task_id,args.attempt,args.review,ops,args.execute))
        elif args.action == 'run': run(ROOT, args.project, args.task, args.execute,use_main=args.main)
        elif args.action == 'demo': demo(ROOT)
    except (ValueError, OSError, yaml.YAMLError, KeyError) as error:
        print(f'错误：{error}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
