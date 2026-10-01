"""合同驱动的草稿/评审闭环；外部模型仅接收显式上下文，不直接写正式文件。"""
import copy
import hashlib
from pathlib import Path
import re
import uuid
import yaml
try:
    from . import adapters, literature, registry, storage, study
except ImportError:
    import adapters, literature, registry, storage, study


TYPE_ALIASES = {
    'paper.meta': 'paper', 'paper.analysis': 'analysis', 'paper.reading': 'reading',
    'paper.translation': 'translation', 'paper.source.text': 'source.text',
    'paper.summary': 'artifact', 'paper.learning-guide': 'artifact',
    'research.profile': 'research-profile', 'claim.feasibility': 'artifact',
    'claim.plan': 'artifact', 'verification.report': 'artifact', 'critique.report': 'artifact',
}
DECISIONS = {'accept', 'revise', 'reject', 'block', 'escalate'}
TERMINAL = {'accepted', 'rejected', 'blocked', 'escalated'}


def digest(content):
    return 'sha256:' + hashlib.sha256(content).hexdigest()


def dump(value):
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=False)


def unchanged_write(path, text):
    if not path.exists() or path.read_bytes() != text.encode('utf-8'):
        storage.write_text(path, text)


def contracts(root, ops, config=None):
    config = config or ops.models(root)
    filename = config.get('settings', {}).get('task_contracts', 'workflow/task-contracts.yaml')
    file = ops.contained(root, filename)
    if not file.is_file():
        raise ValueError('缺少任务合同；不能派发：' + filename)
    data = ops.load(file)
    if data.get('version') != 1 or not isinstance(data.get('tasks'), dict):
        raise ValueError('task-contracts.yaml 版本或 tasks 格式错误')
    main_limit = data.get('settings', {}).get('main_repair_max_attempts', 1)
    if not isinstance(main_limit, int) or isinstance(main_limit, bool) or main_limit < 1:
        raise ValueError('main_repair_max_attempts 必须为正整数')
    for name, item in data['tasks'].items():
        if not isinstance(item, dict) or not item.get('role'):
            raise ValueError('任务合同缺少 role：' + name)
        criteria = item.get('acceptance')
        if not isinstance(criteria, list) or not criteria or any(not isinstance(x, str) or not x.strip() for x in criteria) or len(set(criteria)) != len(criteria):
            raise ValueError('任务合同缺少有效验收标准：' + name)
        limit = item.get('max_attempts')
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError('任务合同 max_attempts 无效：' + name)
        for key in ('inputs', 'outputs'):
            rows = item.get(key)
            if not isinstance(rows, list) or not rows or any(not isinstance(x, dict) or not isinstance(x.get('type'), str) for x in rows):
                raise ValueError('任务合同输入/输出格式错误：' + name)
        if any(not x.get('id_template') or not x.get('path') for x in item['outputs']):
            raise ValueError('任务合同输出缺 id_template/path：' + name)
        if config['routing'].get(name) != item['role']:
            raise ValueError('任务合同与 routing 不一致：' + name)
        limits = dict(data.get('settings', {}).get('context_limits', {}), **item.get('context_limits', {}))
        if any(not isinstance(limits.get(k), int) or isinstance(limits[k], bool) or limits[k] < 1 for k in ('max_chars', 'max_file_chars', 'max_total_bytes')):
            raise ValueError('上下文大小限制无效：' + name)
    missing = set(config['routing']) - set(data['tasks'])
    if missing:
        raise ValueError('路由缺少任务合同：' + ', '.join(sorted(missing)))
    return data


def run_directory(project, task_id, ops):
    return ops.contained(project / '.runs', ops.slug(task_id))


def state(root, project, task_id, ops, status=None, **fields):
    folder = run_directory(project, task_id, ops)
    file = folder / 'status.yaml'
    current = ops.load(file) if file.exists() else {'schema_version':1, 'generated_by':'wf.tasks', 'generated_from':['task:'+task_id], 'task_id': task_id, 'id': 'task:' + task_id, 'history': []}
    if status:
        event = {'status': status, 'at': ops.now(), **fields}
        current.update(event)
        current['generated_at'] = event['at']
        current['history'].append(event)
        ops.save(file, current)
        registry.build(root, project, ops)
    return current


def type_matches(expected, ref):
    actual = ref.get('type')
    if ref.get('contract_type') == expected or actual in {expected, TYPE_ALIASES.get(expected)}:
        return True
    return expected == 'artifact' and actual not in {'project', 'task', 'attempt'}


def check_contract(root, task, ops):
    book = contracts(root, ops)
    spec = book['tasks'].get(task['task_type'])
    if spec is None or digest(dump(spec).encode()) != task.get('contract_hash'):
        raise ValueError('任务合同已变化；请创建新任务并重新验收')


def resolved_input(root, project, item, ops, index):
    if isinstance(item, str):
        if item in index['artifacts'] or item in index.get('aliases', {}):
            item = {'id': item}
        else:
            path, _, anchor = item.partition('#')
            file = literature.resolve_path(project, path, ops)
            if not file.is_file():
                raise ValueError('输入不存在：' + path)
            rel = file.relative_to(project).as_posix()
            candidates = [(key, val) for key, val in index['artifacts'].items() if val.get('path') == rel]
            if candidates:
                key = sorted(candidates, key=lambda x: bool(x[1].get('anchor')))[0][0]
            else:
                key = 'artifact:' + uuid.uuid5(uuid.NAMESPACE_URL, index['project_id'] + ':' + rel).hex
                record = {'id': key, 'type': 'source.text', 'path': rel, 'anchors': []}
                index = registry.register(root, project, ops, [record])
            item = {'id': key, 'anchor': anchor or None}
    if not isinstance(item, dict) or not item.get('id'):
        raise ValueError('输入必须是带 id 的 ArtifactRef')
    resolved = registry.resolve(project, item, ops, index=index)
    if item.get('type') and not type_matches(item['type'], resolved):
        raise ValueError('ArtifactRef.type 与索引不一致：' + item['id'])
    resolved.update(role='input', required=item.get('required', True))
    return resolved


def normalize_task(root, project, task, ops, config=None):
    config = config or ops.models(root)
    book = contracts(root, ops, config)
    task = copy.deepcopy(task)
    ops.slug(task.get('task_id', ''))
    if not isinstance(task.get('objective'), str) or not task['objective'].strip():
        raise ValueError('任务缺少 objective')
    context = task.setdefault('context', {})
    if not isinstance(context, dict):
        raise ValueError('task.context 必须为对象')
    kind = task.get('task_type') or context.get('task_type')
    if task.get('task_type') and context.get('task_type') and task['task_type'] != context['task_type']:
        raise ValueError('task_type 与 context.task_type 不一致')
    if kind not in book['tasks']:
        raise ValueError('未定义任务合同：' + str(kind))
    spec = book['tasks'][kind]
    if task.get('role', spec['role']) != config['routing'][kind]:
        raise ValueError('任务 role 与 routing 不一致')
    task.update(id='task:' + task['task_id'], task_type=kind, role=spec['role'], links=task.get('links', []))
    index = registry.build(root, project, ops)
    if index.get('duplicates'):
        raise ValueError('项目有重复 ID；修复后再派发')
    inputs = task.get('inputs')
    if not isinstance(inputs, list) or not inputs:
        raise ValueError('任务必须有实际输入 ArtifactRef')
    refs = [resolved_input(root, project, item, ops, index) for item in inputs]
    for required in spec['inputs']:
        if required.get('required', True) and not any(type_matches(required['type'], ref) for ref in refs):
            raise ValueError('任务合同缺少输入：' + required['type'])
    if any(not any(type_matches(x['type'], ref) for x in spec['inputs']) for ref in refs):
        raise ValueError('任务含合同以外输入；请扩展合同或移除无关输入')
    task['inputs'] = refs
    task['acceptance_criteria'] = spec['acceptance']
    task['max_attempts'] = spec['max_attempts']
    task['contract'] = config.get('settings', {}).get('task_contracts','workflow/task-contracts.yaml') + '#' + kind
    task['contract_hash'] = digest(dump(spec).encode())
    paper = next((r for r in refs if r['type'] == 'paper'), None)
    claim = next((r for r in refs if r['type'] == 'claim'), None)
    paper_id = paper['id'] if paper else context.get('paper_id')
    key = paper_id.partition(':')[2] if paper_id else context.get('paper_citekey')
    if kind in {'literature-translate', 'literature-close-read', 'literature-synthesis', 'literature-learning-guide'}:
        if not paper_id:
            raise ValueError('翻译或精读需 paper 输入')
        analysis = registry.resolve(project, 'analysis:' + key, ops, index=registry.load_index(project))
        overview = ops.load(ops.contained(project, analysis['path'])).get('overview', {})
        if not all(literature.meaningful(overview.get(k)) for k in ('object', 'core_problem', 'why_important', 'position')):
            raise ValueError('没有完整全局定位，不得开始翻译或逐节精读')
        reading = registry.resolve(project, 'reading:' + key, ops, index=registry.load_index(project))
        body = ops.contained(project, reading['path']).read_text(encoding='utf-8-sig')
        sections = re.split(r'^##\s+', body, flags=re.M)
        if len(sections) < 3 or not all(re.sub(r'(?m)^.*TODO.*$', '', re.sub(r'^[^\n]*\n', '', s)).strip() for s in sections[1:3]):
            raise ValueError('请先确认 reading 第1/2节')
    allowed = task.get('allowed_paths', [])
    if not isinstance(allowed, list) or not all(isinstance(x, str) for x in allowed):
        raise ValueError('allowed_paths 必须为路径数组')
    for path in allowed:
        ops.contained(project, path)
    explicit = task.get('outputs', task.get('outputs_expected'))
    if explicit is not None and (not isinstance(explicit,list) or any(not isinstance(x,dict) or not isinstance(x.get('id'),str) for x in explicit)):
        raise ValueError('outputs 必须为 ArtifactRef 数组')
    outputs = []
    for position, definition in enumerate(spec['outputs']):
        supplied = next((x for x in (explicit or []) if type_matches(definition['type'], x)), None)
        if explicit is not None and not supplied:
            raise ValueError('任务缺少输出 ArtifactRef：' + definition['type'])
        definition = dict(definition)
        identifier = definition['id_template'].replace('<task-id>', task['task_id']).replace('<citekey>', key or '<citekey>')
        rel = definition['path'].replace('<task-id>', task['task_id'])
        if supplied:
            identifier = supplied.get('id', identifier)
        if '<' in identifier or '<' in rel:
            if not supplied or not supplied.get('path'):
                raise ValueError('请显式指定输出 id/path 以替换占位符：' + definition['type'])
            rel = supplied['path']
        if identifier in index['artifacts']:
            ref = registry.resolve(project, identifier, ops, index=registry.load_index(project))
        else:
            if supplied and supplied.get('path'):
                rel = supplied['path']
            elif '/' not in rel or (definition['type'].startswith('paper.') and re.fullmatch(r'\d{2}_[\w-]+', rel.split('/')[0])):
                if definition['type'].startswith('paper.') and paper:
                    rel = (Path(paper['path']).parent / rel).as_posix()
                elif definition['type'].startswith('claim.') and claim:
                    rel = (Path(claim['path']).parent / rel).as_posix()
                else:
                    raise ValueError('无法定位输出；请给输出 ArtifactRef.path')
            target = ops.contained(project, rel)
            ref = {'id': identifier, 'type': TYPE_ALIASES.get(definition['type'], definition['type']), 'path': target.relative_to(project).as_posix(), 'hash': digest(target.read_bytes()) if target.is_file() else None, 'anchor': None}
        expected_type = TYPE_ALIASES.get(definition['type'], definition['type'])
        if not registry.valid_id(identifier) or ref['type'] != expected_type or identifier.split(':', 1)[0] != expected_type:
            raise ValueError('输出 ID/type 与合同不一致：' + identifier)
        target = ops.contained(project, ref['path'])
        if expected_type in {'paper','analysis','claim'} and target.suffix not in {'.yaml','.yml'} or expected_type in {'reading','translation','concept'} and target.suffix != '.md':
            raise ValueError('核心产物格式与对象类型不一致')
        colocated = [(key, value) for key,value in index['artifacts'].items() if value.get('path')==ref['path']]
        if any(value.get('type') in {'source.text','source.binary'} for _,value in colocated):
            raise ValueError('原始资料只读：' + ref['path'])
        if any(key != identifier and value.get('type') in {'project','paper','analysis','reading','translation','concept','claim','task','attempt','research-profile'} for key,value in colocated):
            raise ValueError('输出路径已有另一核心对象；必须沿用该对象 ID')
        if ref['path'] in {'INDEX.json','INDEX.md'} or target.name in {'knowledge-graph.json','knowledge-map.md','reading-list.md'} or '.runs' in target.relative_to(project).parts:
            raise ValueError('生成视图和运行记录由执行器管理，不作为正式输出目标')
        if '01_source' in target.parts or target.suffix not in {'.md', '.yaml', '.yml', '.txt', '.json'}:
            raise ValueError('正式输出必须为可审核文本，原始资料只读')
        if not allowed or not any(target == ops.contained(project, x) or ops.contained(project, x) in target.parents for x in allowed):
            raise ValueError('输出不在 allowed_paths：' + ref['path'])
        ref.update(role='output', required=True, contract_type=definition['type'], mode=(supplied or {}).get('mode', 'replace'))
        outputs.append(ref)
    if explicit is not None and len(explicit) != len(outputs):
        raise ValueError('输出 ArtifactRef 数量与合同不一致')
    task['outputs'] = outputs
    task['context_limits'] = dict(book.get('settings', {}).get('context_limits', {}), **spec.get('context_limits', {}))
    task['review_max_chars'] = book.get('settings', {}).get('review_max_chars', 16000)
    task['main_repair_max_attempts'] = book.get('settings', {}).get('main_repair_max_attempts', 1)
    return task


def prepare(root, project, task, ops, config=None):
    normalized = normalize_task(root, project, task, ops, config)
    folder = run_directory(project, normalized['task_id'], ops)
    if (folder / 'task.yaml').exists():
        old = ops.load(folder / 'task.yaml')
        for field in ('task_type', 'objective', 'role'):
            if old.get(field) != normalized.get(field):
                raise ValueError('任务 ID 已有不同任务；请使用新 task_id')
        current = state(root, project, normalized['task_id'], ops)
        if current.get('status') in TERMINAL:
            raise ValueError('任务已结束；新任务请使用新 task_id')
        if current.get('status') not in {'prepared', 'revision-requested', 'main-repair-requested', 'waiting-manual', 'dry-run'}:
            raise ValueError('已有尝试需先提交/评审；不得改写任务包')
        if old.get('contract_hash') != normalized.get('contract_hash'):
            raise ValueError('任务合同已变化；请创建新 task_id')
        if [(x['id'],x.get('anchor'),x['hash']) for x in old['inputs']] != [(x['id'],x.get('anchor'),x['hash']) for x in normalized['inputs']]:
            raise ValueError('任务输入已变化；请创建新 task_id，不能沿用旧草稿')
        normalized['outputs'] = old['outputs']
        normalized['main_repair_max_attempts'] = old.get('main_repair_max_attempts', normalized['main_repair_max_attempts'])
    ops.save(folder / 'task.yaml', normalized)
    if not (folder / 'status.yaml').exists():
        state(root, project, normalized['task_id'], ops, 'prepared', attempt=0)
    return folder


def select_anchor(content, anchor):
    if not anchor:
        return content
    anchor = str(anchor).lstrip('#')
    nested = re.fullmatch(r'(formulas|first_principles|concepts)\[(\d+)\]', anchor)
    if nested:
        try:
            data = yaml.safe_load(content)
            return dump(data[nested[1]][int(nested[2])])
        except (yaml.YAMLError, TypeError, KeyError, IndexError):
            raise ValueError('YAML anchor 不存在：' + anchor) from None
    # Select ordinary YAML fields without uploading a growing analysis wholesale.
    if re.fullmatch(r'[a-z][\w-]*(?:\.[a-z][\w-]*|\[\d+\])*', anchor):
        try:
            current = yaml.safe_load(content)
            for component in re.findall(r'[a-z][\w-]*|\[\d+\]', anchor):
                current = current[int(component[1:-1])] if component.startswith('[') else current[component]
            return dump(current)
        except (yaml.YAMLError, TypeError, KeyError, IndexError):
            pass  # A Markdown heading may have the same spelling.
    line = re.fullmatch(r'(?:L|lines=)(\d+)(?:[-:](\d+))?', anchor)
    if line:
        start, end = int(line[1]), int(line[2] or line[1])
        if start < 1 or end < start or end > len(content.splitlines()):
            raise ValueError('行号 anchor 不存在：' + anchor)
        return '\n'.join(content.splitlines()[start-1:end])
    headings = list(re.finditer(r'^(#{1,6})\s+(.+?)\s*#*$', content, re.M))
    for n, item in enumerate(headings):
        label = item[2].strip()
        slug = re.sub(r'[^\w\- ]', '', label.lower()).replace(' ', '-')
        if anchor in {label, slug}:
            end = next((h.start() for h in headings[n+1:] if len(h[1]) <= len(item[1])), len(content))
            return content[item.start():end]
    raise ValueError('Markdown anchor 不存在：' + anchor)


def context(root, project, task_id, ops):
    folder = run_directory(project, task_id, ops)
    task = ops.load(folder / 'task.yaml')
    check_contract(root, task, ops)
    current = state(root, project, task_id, ops)
    index = registry.build(root, project, ops)
    revision_of = current.get('active_revision')
    if revision_of is None and current.get('status') in {'revision-requested','main-repair-requested'}:
        revision_of = current['attempt']
    if revision_of is None and current.get('status') in {'waiting-manual','dry-run'}:
        previous_manifest = folder/'attempts'/str(current['attempt'])/'manifest.yaml'
        if previous_manifest.exists():
            revision_of = ops.load(previous_manifest).get('revision_of')
    revision = revision_of is not None
    if revision:
        request = ops.load(folder / 'revision-requests' / (str(revision_of) + '.yaml'))
        inputs = request['context_refs']
        directory = folder / 'revision-requests' / str(revision_of) / 'context'
    else:
        request = None
        inputs = task['inputs']
        directory = folder / 'context'
    limits = task['context_limits']
    chunks = ['# 最小上下文', '', '目标：' + task['objective'], '', '## 验收标准', dump(task['acceptance_criteria']), '## 约束', dump(task.get('constraints', {})), '## 输出模板', dump(task['outputs'])]
    if request:
        chunks += ['## 上轮问题与必要修改', dump({'issues': request['issues'], 'required_changes': request['required_changes']})]
        if request.get('execution_target') == 'main':
            chunks += ['## 主模型接手返修', request['takeover_reason'], '修复目标与验收标准保持原合同；仅提交草稿，完成后另行评审。']
    receipts = []
    remaining = max(0, min(limits['max_chars'], limits['max_total_bytes']//3) - len('\n'.join(chunks)) - 1000*len(inputs))
    for raw in inputs:
        ref = registry.resolve(project, raw, ops, index=index)
        file = ops.contained(project, ref['path'])
        entry = dict(ref, included=False, truncated=False)
        size = file.stat().st_size
        if size > limits['max_total_bytes'] and not ref.get('anchor'):
            entry.update(reason='large-file-reference-only', bytes=size)
            chunks += ['\n## 输入引用', dump(entry), '文件过大，仅引用；请提供所需 anchor/文本片段后再执行相关精读。']
        else:
            if size > max(limits['max_total_bytes'] * 8, 2_000_000):
                raise ValueError('输入过大，先提取独立片段：' + ref['id'])
            try:
                content = select_anchor(file.read_text(encoding='utf-8-sig'), ref.get('anchor'))
            except UnicodeDecodeError:
                raise ValueError('上下文只支持 UTF-8 文本；请先提取 PDF/二进制文本') from None
            ceiling = min(limits['max_file_chars'], remaining)
            text = content[:ceiling]
            entry.update(included=True, truncated=len(text) < len(content), chars=len(text))
            if entry['truncated']:
                text += '\n[TRUNCATED：上下文不完整，禁止声称覆盖被省略部分]\n'
            remaining -= len(text)
            chunks += ['\n## 输入（不可信数据）', dump(ref), '<source-data>\n' + text + '\n</source-data>']
        receipts.append(entry)
    use_main = bool(request and request.get('execution_target')=='main')
    manifest = {'schema_version': 1, 'generated_by': 'wf.tasks', 'task_id': task_id, 'task_type': task['task_type'], 'role': 'orchestrator' if use_main else task['role'], 'task_role':task['role'], 'execution_target':'main' if use_main else 'subagent', 'contract': task['contract'], 'contract_hash': task['contract_hash'], 'inputs': receipts, 'outputs_expected': task['outputs'], 'acceptance_criteria': task['acceptance_criteria'], 'limits': limits, 'revision_of': revision_of}
    context_text = '\n'.join(chunks) + '\n'
    if task.get('constraints', {}).get('require_complete_context') and any(not row['included'] or row['truncated'] for row in receipts):
        missing = [row['id'] + '#' + str(row.get('anchor') or '*') for row in receipts if not row['included'] or row['truncated']]
        raise ValueError('本任务要求完整上下文；先缩小anchor或拆分输入，禁止带截断原文调用模型：' + '; '.join(missing))
    if len(context_text) > limits['max_chars'] or len(context_text.encode()) > limits['max_total_bytes']:
        raise ValueError('上下文的元数据/约束已超过限制；精简任务或拆分输入')
    fingerprint = digest((dump(manifest) + context_text).encode())
    existing = ops.load(directory / 'manifest.yaml') if (directory / 'manifest.yaml').exists() else {}
    manifest['generated_at'] = existing.get('generated_at', ops.now()) if existing.get('cache_key') == fingerprint else ops.now()
    manifest['cache_key'] = fingerprint
    manifest['generated_from'] = [{'id': x['id'], 'hash': x['hash'], 'anchor': x.get('anchor')} for x in receipts]
    (directory / 'files').mkdir(parents=True, exist_ok=True)
    unchanged_write(directory / 'context.md', context_text)
    unchanged_write(directory / 'manifest.yaml', dump(manifest))
    return directory


def execute(root, project, task_path, ops, execute_external=False, config_override=None):
    config = ops.normalize_models(root, config_override) if config_override is not None else ops.models(root)
    task = ops.load(ops.contained(root, task_path))
    folder = prepare(root, project, task, ops, config)
    return execute_prepared(root, project, folder, ops, config, execute_external)


def execute_prepared(root, project, folder, ops, config, execute_external=False):
    """共用执行入口；主模型返修沿用同一合同与草稿记录。"""
    task = ops.load(folder / 'task.yaml')
    check_contract(root, task, ops)
    for ref in task['inputs']:
        registry.resolve(project, ref, ops)
    task_id = task['task_id']
    current = state(root, project, task_id, ops)
    if current.get('status') not in {'prepared', 'revision-requested', 'main-repair-requested', 'waiting-manual', 'dry-run'}:
        raise ValueError('已有尝试需先提交/评审；不得盲目重复调用')
    directory = context(root, project, task_id, ops)
    retry_same = current.get('status') in {'waiting-manual', 'dry-run'}
    attempt = current.get('attempt', 0) if retry_same else current.get('attempt', 0) + 1
    use_main = current.get('execution_target')=='main'
    main_attempts = current.get('main_attempts',0)
    if use_main and not retry_same:
        main_attempts += 1
    if use_main and main_attempts > task.get('main_repair_max_attempts',1) or not use_main and attempt > task['max_attempts']:
        state(root, project, task_id, ops, 'blocked', attempt=attempt-1, reason='达到最大尝试次数')
        raise ValueError('达到最大尝试次数')
    target = folder / 'attempts' / str(attempt)
    role = 'orchestrator' if use_main else ops.resolve_role(config, task['role'])
    settings = ops.execution_settings(config, role, use_main=use_main)
    envelope = {'task_id': task_id, 'attempt': attempt, 'status': 'submitted', 'summary': 'TODO(user)', 'created_artifacts': [], 'updated_artifacts': [], 'evidence': [{'id':ref['id'], 'anchor':ref.get('anchor')} for ref in ops.load(directory/'manifest.yaml')['inputs']], 'unresolved_issues': [], 'confidence': 'low', 'self_check': {x: 'unknown' for x in task['acceptance_criteria']}}
    prompt = ops.role_prompt(root, role, task['role']) + '\n\n' + directory.joinpath('context.md').read_text(encoding='utf-8')
    if use_main:
        prompt += '\n\n## 当前职责：主模型接手返修\n按上轮问题与原验收标准直接修复草稿。本次返回 result/artifacts，不是评审决定。不得以自检代替正式验收，资料不足须在 unresolved_issues 说明。\n'
    output_format = 'JSON 对象；字符串必须正确转义，不要嵌套YAML或代码块' if task.get('constraints', {}).get('response_format') == 'json' else 'YAML 对象（也接受JSON，可放代码块）'
    prompt += '\n\n## 提交合同\n只返回一个 ' + output_format + '：result 和 artifacts。artifacts 每项含 id（正式目标ID）、type、content（完整候选文件）、mode（replace/append）；不得执行工具或写正式路径。\n' + dump({'result': envelope, 'artifacts': []})
    prompt += '\nresult.evidence 每项必须含 id，可直接复制上述真实输入ID；不要写artifact_id或仅file/path。只列实际使用的来源。created_artifacts/updated_artifacts可留空，由执行器登记真实草稿。\n'
    storage.write_text(target / 'prompt.md', prompt)
    ops.save(target / 'manifest.yaml', ops.load(directory / 'manifest.yaml'))
    requested = config['orchestrator'] if use_main else config['subagents'].get(task['role'],{})
    execution = {'requested_role':'orchestrator' if use_main else task['role'], 'task_role':task['role'], 'effective_role': role, 'execution_target': 'main' if use_main else 'subagent', 'execution_kind':'main-repair' if use_main else 'revision' if ops.load(directory/'manifest.yaml')['revision_of'] is not None else 'initial', 'takeover_reason':current.get('takeover_reason') if use_main else None, 'requested_profile': requested.get('profile'), 'actual_role_profile':config['orchestrator']['profile'] if use_main else config['subagents'][role]['profile'], 'effective_profile': settings['profile'], 'adapter': settings['adapter'], 'model': settings.get('model'), 'fallback_reason': settings.get('fallback_reason'), 'role_fallback_reason': '请求角色缺失或禁用，沿用配置 fallback' if not use_main and role != task['role'] else None, 'context_hash': ops.load(directory / 'manifest.yaml')['cache_key'], 'prompt_hash': digest(prompt.encode()), 'execute_external': execute_external}
    ops.save(target / 'execution.yaml', execution)
    state(root, project, task_id, ops, 'executing', attempt=attempt, execution_target=execution['execution_target'], main_attempts=main_attempts, active_revision=ops.load(directory/'manifest.yaml')['revision_of'])
    try:
        status, response = adapters.execute(settings, prompt, project, execute_external)
    except Exception as error:
        execution.update(adapter='manual', effective_profile='manual', attempted_adapter=settings['adapter'], attempted_profile=settings['profile'], fallback_reason='外部调用失败；仅记录异常类型', error_type=type(error).__name__)
        ops.save(target / 'execution.yaml', execution)
        status, response = 'waiting-manual', None
    if response:
        storage.write_text(target / 'response.md', response)
    else:
        unchanged_write(target / 'response.md', '<!-- 等待真实模型/人工响应；不是完成结果。 -->\n')
    if not (target / 'result.yaml').exists():
        ops.save(target / 'result.yaml', dict(envelope, status='pending'))
        ops.save(target / 'artifact-index.yaml', {'artifacts': []})
        storage.write_text(target / 'self-check.md', '# 自检待填写\n\n子模型自检不能代替主模型验收。\n')
    if status == 'draft':
        try:
            submit(root, project, task_id, attempt, parse_response(response), ops)
            return target
        except (ValueError, yaml.YAMLError, TypeError, KeyError):
            status = 'waiting-manual'
            execution['fallback_reason'] = '响应未满足结构化提交合同；保留响应，由人工整理，未登记正式成果'
            ops.save(target / 'execution.yaml', execution)
    state(root, project, task_id, ops, 'waiting-manual' if status in {'mock', 'partial'} else status, attempt=attempt, response_status=status)
    return target


def parse_response(text):
    match = re.fullmatch(r'\s*```(?:yaml|yml|json)?\s*\n(.*?)\n```\s*', text, re.S)
    data = yaml.safe_load(match[1] if match else text)
    if not isinstance(data, dict):
        raise ValueError('响应应为 result/artifacts 对象')
    return data


def submit(root, project, task_id, attempt, payload, ops):
    folder = run_directory(project, task_id, ops)
    task = ops.load(folder / 'task.yaml')
    check_contract(root, task, ops)
    current = state(root, project, task_id, ops)
    if current.get('attempt') != attempt or current.get('status') not in {'executing', 'waiting-manual', 'dry-run'}:
        raise ValueError('当前尝试不能提交结果')
    result = copy.deepcopy(payload.get('result'))
    items = payload.get('artifacts')
    if not isinstance(result, dict) or not isinstance(items, list) or not items:
        raise ValueError('提交必须有 result 与 artifacts')
    ops.contract(root, 'task_result', result)
    if any(not isinstance(x,dict) or not isinstance(x.get('id'),str) for x in items):
        raise ValueError('提交 artifacts 必须为带 id 的对象数组')
    if result.get('task_id') != task_id or result.get('attempt') != attempt or result.get('status') != 'submitted':
        raise ValueError('结果 task_id/attempt/status 不符合合同')
    for field in ('summary', 'confidence', 'created_artifacts', 'updated_artifacts', 'evidence', 'unresolved_issues', 'self_check'):
        if field not in result:
            raise ValueError('结果缺字段：' + field)
    if not isinstance(result['summary'], str) or not result['summary'].strip() or result['confidence'] not in {'high', 'medium', 'low'} or not isinstance(result['self_check'], dict):
        raise ValueError('结果摘要/置信度/自检无效')
    if any(not isinstance(result[x], list) for x in ('created_artifacts', 'updated_artifacts', 'evidence', 'unresolved_issues')):
        raise ValueError('结果清单字段必须为数组')
    for proof in result['evidence']:
        if not isinstance(proof, dict) or not proof.get('id'):
            raise ValueError('结果 evidence 必须使用 ArtifactRef')
        registry.resolve(project, proof, ops)
    expected = {x['id']: x for x in task['outputs']}
    supplied_ids = {x.get('id') for x in items}
    if not supplied_ids <= set(expected) or len(supplied_ids) != len(items):
        raise ValueError('提交产物必须与合同输出一致')
    missing = set(expected) - supplied_ids
    if missing:
        if attempt <= 1 or not (folder / 'revision-requests' / (str(attempt-1) + '.yaml')).exists():
            raise ValueError('提交产物必须与合同输出一致')
        request = ops.load(folder / 'revision-requests' / (str(attempt-1) + '.yaml'))
        affected = {x.get('artifact_id') for x in request['required_changes']}
        previous = ops.load(folder / 'attempts' / str(attempt-1) / 'artifact-index.yaml')['artifacts']
        if None in affected or missing & affected:
            raise ValueError('返修必须提交每个需修改的产物')
        items = copy.deepcopy(items)
        for identifier in sorted(missing):
            row = next((x for x in previous if x['target_id'] == identifier), None)
            if not row or row['id'] in affected:
                raise ValueError('缺少可沿用的未修改草稿')
            registry.resolve(project, row, ops)
            items.append({'id': identifier, 'type': expected[identifier]['type'], 'content': ops.contained(project, row['path']).read_text(encoding='utf-8'), 'mode': expected[identifier]['mode']})
    target = folder / 'attempts' / str(attempt)
    prepared = []
    records = []
    for n, item in enumerate(items):
        official = expected[item['id']]
        if not isinstance(item.get('content'), str) or not item['content'].strip():
            raise ValueError('产物必须提供非空文本 content')
        if item.get('mode', official['mode']) != official['mode'] or official['mode'] not in {'replace', 'append'}:
            raise ValueError('产物 mode 与任务声明不一致')
        suffix = Path(official['path']).suffix
        if suffix in {'.yaml', '.yml'}:
            parsed = yaml.safe_load(item['content'])
            if not isinstance(parsed, dict):
                raise ValueError('YAML 产物必须是对象')
            if parsed.get('id', official['id']) != official['id']:
                raise ValueError('产物 ID 不得改变')
        draft_id = 'artifact:' + task_id + ':attempt-' + str(attempt) + '-' + str(n+1)
        path = target / 'drafts' / (str(n+1) + suffix)
        record = {'id': draft_id, 'type': 'artifact', 'path': path.relative_to(project).as_posix(), 'hash': digest(item['content'].encode()), 'anchor': None, 'role': 'output', 'required': True, 'target_id': official['id'], 'target_type': official['type'], 'target_path': official['path'], 'base_hash': official.get('hash'), 'mode': official['mode'], 'contract_type': official['contract_type'], 'links': [{'rel': 'generated-from', 'target': 'attempt:' + task_id + ':' + str(attempt), 'evidence': [{'file': target.joinpath('result.yaml').relative_to(project).as_posix(), 'field': 'summary'}], 'confidence': 'high', 'status': 'candidate'}]}
        records.append(record)
        prepared.append((path, item['content']))
    # 所有内容预检通过后写草稿；正式路径始终由 accept 管理。
    for path, content in prepared:
        storage.write_text(path, content)
    result['created_artifacts'] = [r for r in records if not r['base_hash']]
    result['updated_artifacts'] = [r for r in records if r['base_hash']]
    execution = ops.load(target/'execution.yaml')
    result.update(id='attempt:' + task_id + ':' + str(attempt), links=[], schema_version=1, generated_by=execution.get('execution_target','subagent'), model_role=execution['effective_role'], execution_target=execution.get('execution_target','subagent'), generated_at=ops.now(), generated_from=[{'id': x['id'], 'hash': x['hash']} for x in task['inputs']])
    ops.save(target / 'result.yaml', result)
    ops.save(target / 'artifact-index.yaml', {'schema_version': 1, 'generated_by':'wf.tasks', 'generated_at':result['generated_at'], 'generated_from':[result['id']], 'artifacts': records})
    storage.write_text(target / 'self-check.md', '# 子模型自检\n\n' + dump(result['self_check']))
    registry.register(root, project, ops, records)
    state(root, project, task_id, ops, 'submitted', attempt=attempt)
    return result


def review_bundle(root, project, task_id, attempt, ops):
    folder = run_directory(project, task_id, ops)
    task = ops.load(folder / 'task.yaml')
    check_contract(root, task, ops)
    current = state(root, project, task_id, ops)
    if current.get('attempt') != attempt or current.get('status') not in {'submitted', 'review-ready', 'reviewed'}:
        raise ValueError('只有当前已提交的尝试可以评审')
    target = folder / 'attempts' / str(attempt)
    result = ops.load(target / 'result.yaml')
    index = registry.build(root, project, ops)
    records = result['created_artifacts'] + result['updated_artifacts']
    refs = []
    changed = []
    for row in records:
        ref = registry.resolve(project, row, ops, index=index)
        expected = next(x for x in task['outputs'] if x['id'] == row['target_id'])
        target_entry = index['artifacts'].get(row['target_id'])
        ref['target_ref'] = dict(expected, path=target_entry['path'] if target_entry else row['target_path'])
        refs.append(ref)
        draft_path = ops.contained(project, row['path'])
        try:
            proposed = literature.markdown(draft_path)[0] if draft_path.suffix == '.md' else ops.load(draft_path) if draft_path.suffix in {'.yaml', '.yml'} else {}
        except (ValueError, yaml.YAMLError):
            raise ValueError('候选产物元数据损坏，不能评审') from None
        old_links = [x for x in index.get('links', []) if x.get('source') == row['target_id']]
        for link in proposed.get('links', []):
            if not any(all(old.get(k)==link.get(k) for k in ('rel','target','evidence','confidence','status')) for old in old_links):
                changed.append(dict(link, source=row['target_id']))
        for old in old_links:
            if not any(link.get('rel')==old.get('rel') and link.get('target')==old.get('target') for link in proposed.get('links', [])) and 'links' in proposed:
                changed.append(dict(old, change='removed'))
    bundle = {'objective': task['objective'], 'acceptance_criteria': task['acceptance_criteria'], 'summary': result['summary'], 'artifacts': refs, 'changed_links': changed, 'evidence': result['evidence'], 'unresolved_issues': result['unresolved_issues'], 'verifier_summary': result.get('verifier_summary', '未提供；需要时另派 verification 任务')}
    text = '# 主模型最小评审包\n\n' + dump(bundle)
    if len(text) > task['review_max_chars']:
        raise ValueError('评审包过大；先精简摘要/证据索引，不截掉验收标准')
    directory = folder / 'reviews' / str(attempt)
    unchanged_write(directory / 'review-bundle.md', text)
    unchanged_write(directory / 'acceptance.yaml', dump({'criteria': task['acceptance_criteria']}))
    unchanged_write(directory / 'evidence.yaml', dump({'evidence': result['evidence'], 'inputs': ops.load(target / 'manifest.yaml')['inputs']}))
    unchanged_write(directory / 'links.yaml', dump({'links': changed}))
    template = {'task_id': task_id, 'attempt': attempt, 'reviewer': 'main', 'decision': 'TODO(user)', 'passed_criteria': [], 'failed_criteria': [], 'issues': [], 'required_changes': [], 'evidence_checks': [], 'next_action': 'TODO(user)', 'reason': 'TODO(user)'}
    if not (directory / 'review-template.yaml').exists():
        ops.save(directory / 'review-template.yaml', template)
    if current['status'] == 'submitted':
        state(root, project, task_id, ops, 'review-ready', attempt=attempt)
    return directory


def validate_review(task, review, task_id, attempt):
    if not isinstance(review, dict) or review.get('task_id') != task_id or review.get('attempt') != attempt or review.get('reviewer') != 'main' or review.get('decision') not in DECISIONS:
        raise ValueError('评审必须为 main 且匹配 task_id/attempt/decision')
    for key in ('passed_criteria', 'failed_criteria', 'issues', 'required_changes', 'evidence_checks'):
        if not isinstance(review.get(key), list):
            raise ValueError('评审缺清单字段：' + key)
    if not isinstance(review.get('reason'), str) or not review['reason'].strip() or not isinstance(review.get('next_action'), str):
        raise ValueError('评审缺 reason/next_action')
    criteria = set(task['acceptance_criteria'])
    passed, failed = set(review['passed_criteria']), set(review['failed_criteria'])
    if (passed | failed) - criteria or passed & failed:
        raise ValueError('评审验收标准未知或相互冲突')
    for issue in review['issues'] + review['required_changes']:
        if not isinstance(issue, dict) or issue.get('criterion') not in criteria:
            raise ValueError('评审问题/修改必须映射 criterion')
    if review['decision'] == 'accept' and (passed != criteria or failed or review['issues'] or review['required_changes'] or not review['evidence_checks']):
        raise ValueError('accept 需全部标准通过、无待修问题且有来源抽查')
    if review['decision'] == 'revise' and (not failed or not review['issues'] or not review['required_changes']):
        raise ValueError('revise 需列出失败标准和可修复问题')
    if review['decision'] == 'revise' and (not failed <= {x['criterion'] for x in review['issues']} or not failed <= {x['criterion'] for x in review['required_changes']}):
        raise ValueError('每个失败 criterion 必须有问题和修改说明')


def record_review(root, project, task_id, attempt, review, ops):
    directory = review_bundle(root, project, task_id, attempt, ops)
    folder = directory.parent.parent
    task = ops.load(folder / 'task.yaml')
    ops.contract(root, 'task_review', review)
    validate_review(task, review, task_id, attempt)
    if review['decision'] == 'accept':
        for check in review['evidence_checks']:
            if not isinstance(check, dict) or check.get('status') != 'verified' or not check.get('ref'):
                raise ValueError('accept 的 evidence_checks 需 ref 与 verified 状态')
            registry.resolve(project, check['ref'], ops)
    ops.save(folder / 'reviews' / (str(attempt) + '.yaml'), review)
    decision = review['decision']
    status = {'reject': 'rejected', 'block': 'blocked', 'escalate': 'escalated'}.get(decision, 'reviewed')
    state(root, project, task_id, ops, status, attempt=attempt, decision=decision)
    return review


def review(root, project, task_id, attempt, ops, review_file=None, execute_external=False, config_override=None, evidence_file=None):
    directory = review_bundle(root, project, task_id, attempt, ops)
    if review_file:
        return record_review(root, project, task_id, attempt, ops.load(ops.contained(root, review_file)), ops)
    if execute_external:
        config = ops.normalize_models(root, config_override) if config_override is not None else ops.models(root)
        settings = ops.execution_settings(config, 'orchestrator', use_main=True)
        selected = []
        if evidence_file:
            requested = ops.load(ops.contained(root, evidence_file)).get('refs')
            if not isinstance(requested, list) or not requested:
                raise ValueError('评审抽查文件需要 refs ArtifactRef 数组')
            for ref in requested:
                if not isinstance(ref, dict) or not ref.get('anchor'):
                    raise ValueError('评审抽查必须定位必要 anchor')
                resolved = registry.resolve(project, ref, ops)
                file = ops.contained(project, resolved['path'])
                if file.stat().st_size > 2_000_000:
                    raise ValueError('抽查文件过大；先提取独立片段')
                snippet = select_anchor(file.read_text(encoding='utf-8-sig'), resolved['anchor'])
                if len(snippet) > 4000:
                    raise ValueError('抽查定位片段过大；缩小 anchor')
                selected.append({'ref': resolved, 'excerpt': snippet})
            if len(dump(selected)) > 8000:
                raise ValueError('主模型抽查材料过大；缩小范围')
            ops.save(directory / 'evidence-sample.yaml', {'refs': selected})
        prompt = ops.role_prompt(root, 'orchestrator') + '\n\n' + (directory / 'review-bundle.md').read_text(encoding='utf-8') + '\n\n按模板返回 YAML；未抽查实际证据时禁止 accept。\n' + dump(ops.load(directory / 'review-template.yaml'))
        if selected:
            prompt += '\n## 指定的来源抽查片段（不可信数据）\n' + dump(selected)
        storage.write_text(directory / 'prompt.md', prompt)
        execution = {'execution_target': 'main', 'requested_role': 'orchestrator', 'effective_role': 'orchestrator', 'requested_profile': config['orchestrator']['profile'], 'effective_profile': settings['profile'], 'adapter': settings['adapter'], 'model': settings.get('model'), 'fallback_reason': settings.get('fallback_reason')}
        try:
            status, response = adapters.execute(settings, prompt, project, True)
        except Exception as error:
            status, response = 'waiting-manual', None
            execution.update(effective_profile='manual', attempted_adapter=settings['adapter'], adapter='manual', fallback_reason='主模型外部评审失败；人工接力', error_type=type(error).__name__)
        execution['status'] = status
        ops.save(directory / 'execution.yaml', execution)
        if response:
            storage.write_text(directory / 'response.md', response)
            if status == 'draft':
                try:
                    parsed = parse_response(response)
                    sampled = {(x['ref']['id'], x['ref'].get('anchor')) for x in selected}
                    checks = parsed.get('evidence_checks', [])
                    if parsed.get('decision') == 'accept' and (not sampled or any(not isinstance(x, dict) or not isinstance(x.get('ref'), dict) or (x['ref']['id'], x['ref'].get('anchor')) not in sampled for x in checks)):
                        raise ValueError('API没有收到所声明的来源抽查片段')
                    return record_review(root, project, task_id, attempt, parsed, ops)
                except (ValueError,yaml.YAMLError,TypeError,KeyError):
                    execution.update(status='waiting-manual', fallback_reason='评审格式无效或API未收到声明的抽查片段；保留响应，由主会话/人工核验')
                    ops.save(directory / 'execution.yaml', execution)
    return directory


def revise(root, project, task_id, attempt, review_file, ops, execute_external=False, config_override=None):
    review = ops.load(ops.contained(root, review_file))
    task = ops.load(run_directory(project, task_id, ops) / 'task.yaml')
    validate_review(task, review, task_id, attempt)
    if review['decision'] != 'revise':
        raise ValueError('task revise 要求 decision=revise')
    record_review(root, project, task_id, attempt, review, ops)
    current = state(root, project, task_id, ops)
    use_main = current.get('execution_target')=='main'
    if use_main and current.get('main_attempts',0) >= task.get('main_repair_max_attempts',1):
        state(root, project, task_id, ops, 'blocked', attempt=attempt, reason='主模型返修仍未通过，已达主模型尝试上限；等待资料或用户决定')
        return None
    requested = review.get('context_refs', [])
    if not isinstance(requested, list):
        raise ValueError('context_refs 必须是 ArtifactRef 数组')
    for ref in requested:
        if not isinstance(ref, dict) or not ref.get('id') or not ref.get('anchor'):
            raise ValueError('返修原文必须指定 id 与必要 anchor；不重传全部原文')
        registry.resolve(project, ref, ops)
    artifacts = ops.load(run_directory(project, task_id, ops) / 'attempts' / str(attempt) / 'artifact-index.yaml')['artifacts']
    selected_ids = {x.get('artifact_id') for x in review['required_changes'] if x.get('artifact_id')}
    if selected_ids - {r['target_id'] for r in artifacts} - {r['id'] for r in artifacts}:
        raise ValueError('返修 artifact_id 不在本次输出中')
    relevant = [x for x in artifacts if not selected_ids or x['id'] in selected_ids or x['target_id'] in selected_ids]
    refs = []
    for artifact in relevant:
        file = ops.contained(project, artifact['path'])
        if task.get('constraints', {}).get('require_complete_context') and file.stat().st_size <= 2_000_000:
            text = file.read_text(encoding='utf-8-sig')
            limit = task['context_limits']['max_file_chars']
            if len(text) > limit:
                # Reuse the full draft in bounded, disjoint excerpts; never silently truncate a repair.
                refs += [dict(id=artifact['id'], hash=artifact['hash'], anchor=f'L{start}-{end}')
                         for start, end in study.split_lines(text, min(limit, 10000))]
                continue
        refs.append(dict(id=artifact['id'], hash=artifact['hash']))
    refs += requested
    folder = run_directory(project, task_id, ops)
    failed_revision = attempt>1 and (folder/'revision-requests'/str(attempt-1)).with_suffix('.yaml').exists()
    takeover = not use_main and (failed_revision or attempt >= task['max_attempts'])
    main_target = use_main or takeover
    reason = '子模型返修后仍未通过，主模型接手修复' if failed_revision else '子模型已达尝试上限，主模型接手修复'
    request = {'schema_version': 1, 'task_id': task_id, 'attempt': attempt, 'issues': review['issues'], 'required_changes': review['required_changes'], 'context_refs': refs, 'execution_target':'main' if main_target else 'subagent'}
    if main_target:
        request['takeover_reason'] = current.get('takeover_reason') or reason
    ops.save(folder / 'revision-requests' / (str(attempt) + '.yaml'), request)
    state(root, project, task_id, ops, 'main-repair-requested' if main_target else 'revision-requested', attempt=attempt, execution_target=request['execution_target'], active_revision=attempt, takeover_reason=request.get('takeover_reason'), main_attempts=current.get('main_attempts',0))
    directory = context(root, project, task_id, ops)
    if main_target:
        config = ops.normalize_models(root,config_override) if config_override is not None else ops.models(root)
        execute_prepared(root,project,folder,ops,config,execute_external)
    return directory


def accept(root, project, task_id, attempt, ops):
    folder = run_directory(project, task_id, ops)
    current = state(root, project, task_id, ops)
    if current.get('status') == 'accepted' and current.get('attempt') == attempt:
        return current
    if current.get('attempt') != attempt or current.get('status') not in {'reviewed', 'review-ready'}:
        raise ValueError('只有当前已评审任务可 accept')
    task = ops.load(folder / 'task.yaml')
    check_contract(root, task, ops)
    review = ops.load(folder / 'reviews' / (str(attempt) + '.yaml'))
    validate_review(task, review, task_id, attempt)
    if review['decision'] != 'accept':
        raise ValueError('主模型尚未决定 accept')
    for check in review['evidence_checks']:
        if not isinstance(check, dict) or check.get('status') != 'verified' or not check.get('ref'):
            raise ValueError('缺少已核验来源')
        registry.resolve(project, check['ref'], ops)
    index = registry.build(root, project, ops)
    manifest = ops.load(folder / 'attempts' / str(attempt) / 'manifest.yaml')
    for ref in task['inputs'] + manifest['inputs']:
        registry.resolve(project, ref, ops, index=index)
    rows = ops.load(folder / 'attempts' / str(attempt) / 'artifact-index.yaml')['artifacts']
    targets = []
    for row in rows:
        registry.resolve(project, row, ops, index=index)
        official = next(x for x in task['outputs'] if x['id'] == row['target_id'])
        # 目标移动后使用稳定 ID 找到新位置；不允许陈旧快照覆盖人工修改。
        existing = index['artifacts'].get(row['target_id'])
        target = ops.contained(project, existing['path'] if existing else row['target_path'])
        old = target.read_bytes() if target.exists() else None
        if (digest(old) if old is not None else None) != row['base_hash']:
            raise ValueError('正式目标已变化，需重新评审：' + row['target_id'])
        draft = ops.contained(project, row['path']).read_bytes()
        content = old + draft if row['mode'] == 'append' and old is not None else draft
        if task['task_type'] == 'literature-translate' and task.get('constraints', {}).get('segment_id'):
            sid = ops.slug(task['constraints']['segment_id'])
            begin, end = f'<!-- translation:{sid} -->', f'<!-- /translation:{sid} -->'
            fragment = draft.decode('utf-8-sig')
            matched = re.search(re.escape(begin) + r'([\s\S]*?)' + re.escape(end), fragment)
            if fragment.count(begin)!=1 or fragment.count(end)!=1 or not matched or not matched[1].strip():
                raise ValueError('翻译片段标记缺失、重复或正文为空')
            if old and (begin in old.decode('utf-8-sig') or end in old.decode('utf-8-sig')):
                raise ValueError('翻译片段已存在，拒绝重复追加')
        # 核心文本更新不得悄悄丢掉人工正文；要求候选保留旧正文。
        if old and target.suffix == '.md' and row['mode'] == 'replace':
            _, body = literature.markdown(target)
            significant = [line.strip() for line in body.splitlines() if line.strip() and not line.lstrip().startswith(('#', '<!--')) and 'TODO' not in line and not line.strip().startswith('|---')]
            new_text = content.decode('utf-8-sig')
            if any(line not in new_text for line in significant):
                raise ValueError('候选删除已有正文；请保留人工内容或改用 append：' + row['target_id'])
        if target.suffix in {'.yaml', '.yml'}:
            proposed = yaml.safe_load(content.decode('utf-8-sig'))
            original = yaml.safe_load(old.decode('utf-8-sig')) if old else {}
            if proposed.get('id', row['target_id']) != row['target_id']:
                raise ValueError('产物不能变更稳定 ID')
            # 保留旧字段；新内容的变更仍由主模型验收负责。
            proposed = dict(original or {}, **proposed)
            proposed.update(id=row['target_id'], links=proposed.get('links', []))
            kind = {'paper': 'paper', 'analysis': 'analysis', 'claim': 'claim'}.get(official['type'])
            if kind:
                ops.contract(root, kind, proposed)
            content = dump(proposed).encode()
        elif target.suffix == '.md':
            draft_file = ops.contained(project, row['path'])
            proposed, body = literature.markdown(draft_file)
            if task['task_type'] in {'literature-synthesis','literature-learning-guide'}:
                kind = 'summary' if task['task_type']=='literature-synthesis' else 'concept-guide'
                expected_paper = 'paper:' + task['context']['paper_citekey']
                study.validate_delivery(root, project, draft_file, kind, expected_paper, ops)
            original, _ = literature.markdown(target) if old else ({}, '')
            if proposed.get('id', row['target_id']) != row['target_id']:
                raise ValueError('Markdown 产物不能变更稳定 ID')
            proposed = dict(original, **proposed)
            proposed.update(id=row['target_id'], links=proposed.get('links', []))
            execution = ops.load(folder/'attempts'/str(attempt)/'execution.yaml')
            for key,value in dict(generated_by='wf.tasks',model_role=execution['effective_role'],prompt_version='task-contract-v1',created_at=ops.now(),source_refs=[x['path'] for x in task['inputs']]).items():
                proposed.setdefault(key,value)
            if official['type'] == 'concept':
                ops.contract(root, 'concept', proposed)
            if row['mode'] == 'replace':
                content = ('---\n' + dump(proposed) + '---\n\n' + body).encode()
            elif literature.markdown(draft_file)[0]:
                raise ValueError('append 内容只应包含新增正文，不可重复 front matter')
        proposed_links = []
        if target.suffix in {'.yaml', '.yml', '.md'}:
            proposed_links = proposed.get('links', [])
            if not isinstance(proposed_links, list):
                raise ValueError('links 必须为数组')
        prior_links = [x for x in index.get('links', []) if x.get('source') == row['target_id']]
        output_ids = {x['target_id'] for x in rows}
        for link in proposed_links:
            if not isinstance(link, dict) or link.get('target') not in set(index['artifacts']) | output_ids or not link.get('evidence'):
                raise ValueError('候选产物含悬空或无证据 link')
            if link.get('confidence') not in {'high','medium','low'} or link.get('status') not in {'candidate','verified'} or not isinstance(link.get('rel'), str):
                raise ValueError('候选 link 状态/置信度无效')
            prior = next((x for x in prior_links if x.get('rel')==link.get('rel') and x.get('target')==link.get('target')), None)
            if link['status'] == 'verified' and (not prior or prior.get('status') != 'verified' or prior.get('evidence') != link['evidence']):
                checks = review.get('link_checks', [])
                if not any(x.get('source')==row['target_id'] and x.get('target')==link['target'] and x.get('rel')==link['rel'] and x.get('status')=='verified' for x in checks if isinstance(x, dict)):
                    raise ValueError('新增 verified link 需要主模型逐条 link_checks；自动链接只为 candidate')
        targets.append((target, old, content, row, official, proposed_links))
    # 核心文件及派生视图一起回滚；失败不留下“已接受”但未联动的正式成果。
    paths = {project/'project.yaml', project/'INDEX.json', project/'INDEX.md', folder/'status.yaml', folder/'final/acceptance.yaml'}
    paths.update(project/'10_literature'/name for name in ('reading-list.md','knowledge-graph.json','knowledge-map.md'))
    paths.update(project.glob('10_literature/papers/*/meta.yaml'))
    paths.update(project.glob('10_literature/papers/*/04_analysis/analysis.yaml'))
    paths.update(project.glob('10_literature/concepts/*.md'))
    paths.update(target for target, *_ in targets)
    originals = {path: path.read_bytes() if path.is_file() else None for path in paths}
    try:
        for n, (target, old, content, row, official, links) in enumerate(targets):
            if old is not None:
                storage.write_bytes(folder / 'final' / 'backups' / (str(n+1) + target.suffix), old)
            storage.write_bytes(target, content)
        records = [dict(id=row['target_id'], type=official['type'], contract_type=official['contract_type'], path=target.relative_to(project).as_posix(), anchors=[], links=links) for target, old, content, row, official, links in targets]
        updated = registry.register(root, project, ops, records)
        new_issues = set(updated.get('issues', [])) - set(index.get('issues', []))
        if new_issues:
            raise ValueError('候选引入无效连接：' + '; '.join(sorted(new_issues)))
        ops.save(folder / 'final' / 'acceptance.yaml', dict(review, applied_at=ops.now(), artifacts=records))
        state(root, project, task_id, ops, 'accepted', attempt=attempt)
        ops.index(root, project.name)
    except Exception:
        for target, old in originals.items():
            if old is None:
                target.unlink(missing_ok=True)
            else:
                storage.write_bytes(target, old)
        raise
    return state(root, project, task_id, ops)


def statuses(project, task_id, ops):
    if task_id:
        if not (run_directory(project, task_id, ops) / 'status.yaml').is_file():
            raise ValueError('任务不存在：' + task_id)
        return state(None, project, task_id, ops)
    return {path.parent.name: ops.load(path) for path in sorted((project / '.runs').glob('*/status.yaml'))}
