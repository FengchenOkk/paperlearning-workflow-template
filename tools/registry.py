"""Stable object identities and the rebuildable project INDEX.json.

The index stores connections, never scientific conclusions.  Source ``links``
remain authoritative; malformed objects are reported without stopping a scan.
"""
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import yaml

try:
    from . import literature, storage
except ImportError:
    import literature, storage


KINDS = {'project', 'paper', 'analysis', 'translation', 'reading', 'concept',
         'principle', 'formula', 'claim', 'topic', 'task', 'attempt', 'artifact'}
ARTIFACT_TYPES = KINDS | {'source.text', 'source.binary', 'research-profile'}
PRIVATE_NAMES = {'.env', 'auth.json', 'models.local.yaml', 'zotero.local.yaml'}
PRIVATE_PARTS = {'private', '.git', '.codex', '.agents', '__pycache__'}


# A named format rather than a dict subclass: PyYAML safe_dump must be able to
# serialize refs embedded anywhere in a task or manifest without custom hooks.
ArtifactRef = dict


def valid_id(value):
    return (isinstance(value, str) and ':' in value and
            value.split(':', 1)[0] in KINDS and bool(value.split(':', 1)[1]) and
            not any(ord(c) < 32 for c in value) and
            not any(c in value for c in '/\\#') and 'TODO' not in value)


def _identity(value, kind, fallback):
    if literature.meaningful(value):
        if not isinstance(value,str):
            raise ValueError('已存 ID 必须为字符串')
        return value  # Existing identities are never silently replaced.
    return f'{kind}:{fallback}'


def _hash(content):
    return 'sha256:' + hashlib.sha256(content).hexdigest()


def _hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return 'sha256:' + digest.hexdigest()


def _json(data):
    def compatible(value):
        if isinstance(value,dict):return {str(key):compatible(item) for key,item in value.items()}
        if isinstance(value,(list,tuple)):return [compatible(item) for item in value]
        if isinstance(value,(date,datetime)):return value.isoformat()
        if isinstance(value,float) and not math.isfinite(value):return None
        if isinstance(value,(str,int,float,bool,type(None))):return value
        return str(value)
    return json.dumps(compatible(data), ensure_ascii=False, indent=2, sort_keys=True,allow_nan=False) + '\n'


def _safe(project, path, ops):
    target = ops.contained(Path(project), path)
    rel = target.relative_to(Path(project).resolve())
    if (any(part in PRIVATE_PARTS for part in rel.parts) or
            target.name in PRIVATE_NAMES or target.name.startswith('.env.') or
            target.suffix.lower() in {'.pem', '.key'} or
            any(part == 'config' for part in rel.parts)):
        raise ValueError('私有配置或凭据不能登记为 artifact')
    return target


def _read(path, ops):
    if path.suffix.lower() == '.md':
        return literature.markdown(path)
    return ops.load(path), None


def _only_added_fields(before,after):
    if before==after:return True
    if isinstance(before,dict) and isinstance(after,dict):
        return all(key in after and _only_added_fields(value,after[key]) for key,value in before.items())
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        return all(_only_added_fields(a,b) for a,b in zip(before,after))
    return False


def _nested_additions(node,before,after,original):
    edits=[]
    if isinstance(before,dict):
        children={key.value:value for key,value in node.value}
        for key,value in before.items():
            if value!=after[key]:
                edits.extend(_nested_additions(children[key],value,after[key],original))
        additions={key:value for key,value in after.items() if key not in before}
        if additions:
            if node.flow_style:
                text=yaml.safe_dump(additions,allow_unicode=True,sort_keys=False,default_flow_style=True).strip()
                text=text.removesuffix('...').strip()[1:-1]
                edits.append((node.end_mark.index-1,node.end_mark.index-1,(', ' if before else '')+text))
            else:
                indent=node.value[0][0].start_mark.column if node.value else node.start_mark.column
                text=yaml.safe_dump(additions,allow_unicode=True,sort_keys=False)
                text=''.join(' '*indent+line+'\n' for line in text.splitlines())
                position=original.rfind('\n',0,node.end_mark.index)+1
                if position==0 and node.end_mark.index==len(original):position=len(original)
                if position==len(original) and original and not original.endswith('\n'):text='\n'+text
                edits.append((position,position,text))
    elif isinstance(before,list):
        for child,a,b in zip(node.value,before,after):
            if a!=b:edits.extend(_nested_additions(child,a,b,original))
    return edits


def _preserving_yaml(original, before, after):
    """Replace changed top-level values, retaining unrelated comments/text."""
    try:
        node = yaml.compose(original)
    except yaml.YAMLError:
        raise ValueError('YAML 格式错误') from None
    if not isinstance(node, yaml.MappingNode):
        return yaml.safe_dump(after, allow_unicode=True, sort_keys=False)
    fields = {key.value: value for key, value in node.value}
    changes = []
    additions = []
    for key, value in after.items():
        if key in before and before[key] == value:
            continue
        dumped = yaml.safe_dump({key: value}, allow_unicode=True, sort_keys=False)
        if key not in fields:
            additions.append(dumped)
            continue
        if _only_added_fields(before[key],value):
            changes.extend(_nested_additions(fields[key],before[key],value,original))
            continue
        # A complete field replacement is restricted to fields actually changed
        # by the identity/link compatibility layer, never free-text body fields.
        key_node = next(k for k, v in node.value if k.value == key)
        start = original.rfind('\n', 0, key_node.start_mark.index) + 1
        following = [k.start_mark.index for k,v in node.value if k.start_mark.index>key_node.start_mark.index]
        end = original.rfind('\n',0,min(following))+1 if following else len(original)
        changes.append((start, end, dumped))
    for start, end, text in sorted(changes, reverse=True):
        original = original[:start] + text + original[end:]
    if additions:
        original = original.rstrip('\r\n') + '\n' + ''.join(additions)
    # Fail closed if a rare YAML layout would make textual replacement unsafe.
    if yaml.safe_load(original) != after:
        raise ValueError('无法安全追加身份字段；原件保留，请手动补 id/links')
    return original


def _serialize(path, before, after):
    text = path.read_text(encoding='utf-8-sig')
    if path.suffix.lower() != '.md':
        return _preserving_yaml(text, before, after)
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    if match:
        # Preserve Markdown after the closing delimiter byte for byte.
        return text[:match.start(1)] + _preserving_yaml(match[1]+'\n', before, after).rstrip('\n') + text[match.end(1):]
    return '---\n' + yaml.safe_dump(after, allow_unicode=True, sort_keys=False) + '---\n' + text


def load_index(project):
    path = Path(project) / 'INDEX.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        raise ValueError('INDEX.json 缺失或损坏；请先运行 index') from None
    if not isinstance(data, dict) or not isinstance(data.get('artifacts'), dict):
        raise ValueError('INDEX.json 需要 artifacts 对象')
    return data


def build(root, project, ops, dry_run=False, write=True):
    root, project = Path(root), Path(project).resolve()
    mutation = bool(write and not dry_run)
    documents, artifacts, aliases, links, issues, duplicates, tasks = {}, {}, {}, [], [], {}, {}
    source_links = {}
    extra_records = []

    def document(path):
        path = _safe(project, path, ops)
        if path not in documents:
            data, body = _read(path, ops)
            if not isinstance(data, dict):
                raise ValueError('核心对象需要 mapping')
            documents[path] = [data, deepcopy(data), body]
        return documents[path][0]

    def alias(name, identifier):
        if not isinstance(name, str) or not name or name == identifier:
            return
        if name in aliases and aliases[name] != identifier:
            issues.append('别名冲突：' + name)
            return
        aliases[name] = identifier

    def add(identifier, kind, path, data=None, anchor=None, label=None):
        if not valid_id(identifier):
            issues.append('无效 ID：' + str(identifier))
            return identifier
        path = _safe(project, path, ops)
        rel = path.relative_to(project).as_posix()
        item = dict(type=kind, path=rel, anchors=[anchor] if anchor else [], label=label or identifier.split(':',1)[1])
        if identifier in artifacts:
            old = artifacts[identifier]
            if old['path'] == rel and old['anchors'] == item['anchors']:
                if isinstance(data,dict) and data.get('contract_type'):
                    old['contract_type'] = data['contract_type']
                if isinstance(data,dict) and path in documents and documents[path][0] is data:
                    data.setdefault('links',[])
                    if isinstance(data['links'],list):
                        source_links[identifier]=(data['links'],rel)
                    else:
                        issues.append('links 必须为列表：'+identifier)
                return identifier
            duplicates.setdefault(identifier, [dict(path=old['path'], anchors=old['anchors'])]).append(dict(path=rel, anchors=item['anchors']))
            issues.append('重复 ID：' + identifier)
            return identifier
        artifacts[identifier] = item
        alias(rel + ('#'+anchor if anchor else ''), identifier)
        if data is not None:
            data.setdefault('links', [])
            if not isinstance(data['links'], list):
                issues.append('links 必须为列表：' + identifier)
            else:
                source_links[identifier] = (data['links'], rel)
            for name in data.get('aliases', []) if isinstance(data.get('aliases', []), list) else []:
                alias(name, identifier)
            if kind == 'concept':
                item['concept_type'] = data.get('type')
            for field in ('status', 'reading_status', 'analysis_status', 'paper_role', 'title', 'task_type', 'contract_type'):
                if field in data:
                    item[field] = data[field]
        return identifier

    def core(path, kind, fallback, foreign=None):
        data = document(path)
        identifier = _identity(data.get('id'), kind, fallback)
        data.setdefault('id', identifier)
        if not literature.meaningful(data.get('id')):
            data['id'] = identifier
        if kind == 'concept':
            data.setdefault('object_type', 'concept')
        else:
            data.setdefault('type', kind)
        if foreign:
            for key, value in foreign.items():
                data.setdefault(key, value)
        return add(identifier, kind, path, data), data

    def local_evidence(path, field, refs=None):
        return [dict(file=Path(path).relative_to(project).as_posix(), field=field, source_refs=refs or [])]

    def connect(source, rel, target, proof, owner=None, weight=None):
        if source not in source_links:
            return
        records = owner if owner is not None else source_links[source][0]
        # Manual relation always takes precedence over inferred compatibility.
        if any(isinstance(entry, dict) and entry.get('rel') == rel and
               (aliases.get(entry.get('target'),entry.get('target')) if isinstance(entry.get('target'),str) else entry.get('target')) == target
               for entry in records):
            return
        item = dict(rel=rel, target=target, evidence=proof, confidence='medium', status='candidate', generated_by='wf-registry')
        if weight is not None:
            item['weight'] = weight
        records.append(item)

    project_data = document(project/'project.yaml')
    project_id = _identity(project_data.get('id'), 'project', project_data.get('slug') if literature.meaningful(project_data.get('slug')) else project.name)
    project_data.setdefault('id', project_id)
    if not literature.meaningful(project_data.get('id')):
        project_data['id'] = project_id
    project_data.setdefault('type', 'project')
    add(project_id, 'project', project/'project.yaml', project_data)
    persisted_aliases = project_data.get('id_aliases', {})
    if not isinstance(persisted_aliases, dict):
        issues.append('project.id_aliases 必须为对象')
        persisted_aliases = {}
    for name, target in sorted(persisted_aliases.items(),key=lambda item:str(item[0])):
        if not isinstance(name,str) or not valid_id(target):
            issues.append('无效持久别名：'+str(name))
            continue
        alias(name, target)
    registry_records = project_data.get('artifact_registry', [])
    if not isinstance(registry_records, list):
        issues.append('project.artifact_registry 必须为列表')
        registry_records = []

    if (project/'research-profile.yaml').is_file():
        try:
            data = document(project/'research-profile.yaml')
            identifier = _identity(data.get('id'),'artifact',project_id.split(':',1)[1]+':research-profile')
            data.setdefault('id',identifier)
            data.setdefault('object_type','research-profile')
            add(identifier,'research-profile',project/'research-profile.yaml',data)
        except (ValueError,TypeError,OSError,yaml.YAMLError):
            issues.append('无法索引 research-profile.yaml')

    paper_records, concept_records, analysis_records, claims = [], [], [], []
    for path in sorted((project/'10_literature/papers').glob('*/meta.yaml')):
        try:
            identifier, data = core(path, 'paper', path.parent.name, {'project_id':project_id})
            key = data.get('citekey') if literature.meaningful(data.get('citekey')) else path.parent.name
            alias('paper:'+str(key), identifier)
            alias(str(key), identifier)
            zotero = data.get('zotero', {})
            zk = data.get('zotero_key') if literature.meaningful(data.get('zotero_key')) else (zotero.get('item_key') if isinstance(zotero, dict) else None)
            data.setdefault('zotero_key', zk if literature.meaningful(zk) else literature.TODO)
            if literature.meaningful(zk):
                alias('zotero:'+str(zk), identifier)
            paper_records.append((identifier, path, data, key))
            attachment_refs=path.parent/'01_source/source-links.yaml'
            if attachment_refs.is_file():
                core(attachment_refs,'artifact',identifier.split(':',1)[1]+':source-links',{'paper_id':identifier,'contract_type':'paper.source.links'})
            for name, kind in [('analysis.yaml','analysis'), ('translation.md','translation'), ('reading.md','reading')]:
                target = literature.paper_path(path.parent, name)
                if target.is_file():
                    aid, info = core(target, kind, identifier.split(':',1)[1], {'paper_id':identifier})
                    if kind == 'analysis':
                        analysis_records.append((identifier, aid, target, info, key))
        except (ValueError, TypeError, OSError, yaml.YAMLError):
            issues.append('无法索引论文：'+path.relative_to(project).as_posix())
    for path in sorted((project/'10_literature/concepts').glob('*.md')):
        try:
            identifier, data = core(path, 'concept', path.stem)
            prior_papers = data.get('papers', [])
            if isinstance(prior_papers,list):
                data.setdefault('paper_ids', [aliases.get(value if value.startswith('paper:') else 'paper:'+value, value if value.startswith('paper:') else 'paper:'+value) for value in prior_papers if isinstance(value,str)])
            else:
                data.setdefault('paper_ids', [])
            alias('concept:'+str(data.get('concept_id', path.stem)), identifier)
            alias('concept:'+path.stem, identifier)
            concept_records.append((identifier, path, data))
            if data.get('is_first_principle'):
                pid = _identity(data.get('principle_id'), 'principle', identifier.split(':',1)[1])
                data.setdefault('principle_id', pid)
                add(pid, 'principle', path, anchor='is_first_principle')
                data.setdefault('principle_links', [])
                if isinstance(data['principle_links'],list):
                    source_links[pid] = (data['principle_links'],path.relative_to(project).as_posix())
                    connect(pid,'uses',identifier,local_evidence(path,'is_first_principle'))
                # Relationship belongs to the source concept; it is not another
                # hand-maintained graph representation.
                connect(identifier, 'derived-from', pid, local_evidence(path, 'is_first_principle'))
        except (ValueError, TypeError, OSError, yaml.YAMLError):
            issues.append('无法索引概念：'+path.relative_to(project).as_posix())
    for path in sorted((project/'20_reproduction').glob('*/claim.yaml')):
        try:
            data = document(path)
            paper = data.get('paper_id') or 'paper:'+str(data.get('paper_citekey', 'unknown'))
            key = str(paper).split(':',1)[-1]
            claim = str(data.get('claim_id') or path.parent.name)
            claim_slug=claim.removeprefix(key+'--')
            identifier, data = core(path, 'claim', key+':'+claim_slug, {'paper_id':aliases.get(paper,paper), 'formula_ids':[], 'concept_ids':[]})
            alias(claim,identifier)
            alias('claim:'+claim,identifier)
            alias('claim:'+path.parent.name,identifier)
            claims.append((identifier, path, data))
        except (ValueError, TypeError, OSError, yaml.YAMLError):
            issues.append('无法索引 claim：'+path.relative_to(project).as_posix())

    def canonical(value, kind):
        target = value if isinstance(value,str) and value.startswith(kind+':') else kind+':'+str(value)
        return aliases.get(target, target)

    def values(data, field):
        result = data.get(field, [])
        if not isinstance(result, list):
            issues.append('字段必须为列表：'+field)
            return []
        return result

    def topic(value):
        identifier = canonical(value, 'topic')
        if not valid_id(identifier):
            issues.append('无效 topic ID：'+str(value))
            return identifier
        if not any(isinstance(entry,dict) and entry.get('id')==identifier for entry in registry_records+extra_records):
            extra_records.append(dict(id=identifier,type='topic',path='project.yaml',label=identifier.split(':',1)[1],links=[]))
        return identifier

    # Embedded items retain old short IDs (used by historical schemas), with a
    # separate stable object_id for cross-object connections.
    for paper, aid, path, data, key in analysis_records:
        for field, kind in [('formulas','formula'), ('first_principles','principle')]:
            for n, entry in enumerate(values(data, field)):
                if not isinstance(entry, dict):
                    issues.append('嵌套对象损坏：'+field)
                    continue
                legacy = entry.get('id')
                if not literature.meaningful(legacy):
                    issues.append('嵌套对象缺 ID：'+path.relative_to(project).as_posix()+'#'+field+'['+str(n)+']')
                    continue
                fallback = f'{paper.split(":",1)[1]}:{legacy}' if kind == 'formula' else legacy
                identifier = _identity(entry.get('object_id') or (legacy if valid_id(legacy) else None), kind, fallback)
                entry.setdefault('object_id', identifier)
                entry.setdefault('object_type', kind)
                entry.setdefault('links', [])
                if kind == 'principle' and identifier in artifacts:
                    # An occurrence of a canonical concept-card principle.
                    pass
                else:
                    add(identifier, kind, path, entry, anchor=f'{field}[{n}]')
                if kind == 'formula':
                    alias('formula:'+str(key)+':'+str(legacy), identifier)
                    connect(identifier,'derived-from',paper,local_evidence(path,f'{field}[{n}]',entry.get('source_refs',[])))
                    related = values(entry,'related_concepts')
                else:
                    related = entry.get('concept_ids',[legacy])
                    connect(paper,'uses',identifier,local_evidence(path,f'{field}[{n}]',entry.get('source_refs',[])))
                for cid in related if isinstance(related,list) else []:
                    connect(identifier,'uses',canonical(cid,'concept'),local_evidence(path,f'{field}[{n}]'))
        for n, entry in enumerate(values(data,'concepts')):
            if not isinstance(entry,dict) or not literature.meaningful(entry.get('id')):
                continue
            rel = {'introduced':'introduces','used':'uses','compared':'contrasts','extended':'extends'}.get(entry.get('role'),'uses')
            connect(paper,rel,canonical(entry['id'],'concept'),local_evidence(path,f'concepts[{n}]',entry.get('source_refs',[])))
    for identifier, path, data, key in paper_records:
        for field, kind, rel in [('concept_ids','concept','uses'),('first_principle_ids','principle','uses'),
                                 ('categories','topic','belongs-to-topic'),('topic_tags','topic','belongs-to-topic'),('topic_ids','topic','belongs-to-topic')]:
            for target in values(data,field):
                dst = topic(target) if kind=='topic' else canonical(target,kind)
                connect(identifier,rel,dst,local_evidence(path,field))
        for link in values(data,'links'):
            if isinstance(link,dict) and str(link.get('target','')).startswith('topic:'):
                topic(link['target'])
    for identifier, path, data in concept_records:
        for field, rel in [('prerequisites','prerequisite'),('related','related'),('contrasts','contrasts'),('extends','extends'),('replaces','replaces')]:
            for target in values(data,field):
                connect(identifier,rel,canonical(target,'concept'),local_evidence(path,field))
        for target in values(data,'papers') + values(data,'paper_ids'):
            target = canonical(target,'paper')
            connect(identifier,'derived-from',target,local_evidence(path,'papers/paper_ids'))
            connect(target,'uses',identifier,local_evidence(path,'papers/paper_ids'))
    for identifier, path, data in claims:
        paper = canonical(data.get('paper_id',data.get('paper_citekey','unknown')),'paper')
        connect(identifier,'derived-from',paper,local_evidence(path,'paper_id'))
        for field, kind in [('formula_ids','formula'),('concept_ids','concept')]:
            for target in values(data,field):
                dst = canonical(target,kind) if kind=='concept' or str(target).startswith('formula:') else 'formula:'+paper.split(':',1)[1]+':'+str(target)
                connect(identifier,'uses',dst,local_evidence(path,field))

    if extra_records:
        registry_records = registry_records + extra_records
        project_data['artifact_registry'] = registry_records
    source_paths = set()
    for identifier,path,data,key in paper_records:
        for raw in values(data,'source_files'):
            if isinstance(raw,str):
                try:
                    target = literature.resolve_path(project,raw.split('#',1)[0],ops)
                    if target.is_file():
                        source_paths.add(_safe(project,target,ops))
                except (ValueError,OSError):
                    issues.append('来源路径不安全：'+str(raw))
        for candidate in sorted((path.parent/'01_source').rglob('*')):
            if candidate.is_file() and candidate.suffix.lower() in {'.txt','.md','.tex','.rst'}:
                try:
                    source_paths.add(_safe(project,candidate,ops))
                except (ValueError,OSError):
                    issues.append('来源路径不安全：'+candidate.name)
    for path in sorted(source_paths):
        rel = path.relative_to(project).as_posix()
        matched = next((entry for entry in registry_records if isinstance(entry,dict) and entry.get('path')==rel),None)
        if matched is not None:
            matched['source_hash'] = _hash_file(path)
            continue
        previous = next((entry for entry in registry_records if isinstance(entry,dict) and entry.get('source_hash')==_hash_file(path) and not (project/str(entry.get('path'))).is_file()),None)
        if previous is not None:
            previous['path'] = rel
            continue
        identifier = 'artifact:'+hashlib.sha256((project_id+'\n'+rel).encode('utf-8')).hexdigest()[:24]
        kind = 'source.text' if path.suffix.lower() in {'.txt','.md','.tex','.rst'} else 'source.binary'
        registry_records.append(dict(id=identifier,type=kind,path=rel,source_hash=_hash_file(path),links=[]))
    if registry_records:
        project_data['artifact_registry'] = registry_records
    for n, record in enumerate(registry_records):
        try:
            if not isinstance(record,dict) or not valid_id(record.get('id')):
                raise ValueError('登记缺少有效 ID')
            path = _safe(project,record.get('path',''),ops)
            if not path.is_file():
                raise ValueError('登记路径不存在')
            kind = record.get('type', record['id'].split(':',1)[0])
            anchor = record.get('anchor')
            if kind=='topic' and path==project/'project.yaml' and anchor is None:
                anchor = f'artifact_registry[{n}]'
            owner=record
            if kind!='topic' and anchor is None and path.suffix.lower() in {'.md','.yaml','.yml'}:
                content=document(path)
                # A draft may contain its intended official ID; its registered
                # draft identity and generated-from link must remain separate.
                if content.get('id')==record['id']:
                    owner=content
                    record.pop('links',None)
            add(record['id'],kind,path,owner,anchor=anchor,label=record.get('label'))
            if record.get('contract_type') and record['id'] in artifacts:
                artifacts[record['id']]['contract_type']=record['contract_type']
        except (ValueError, TypeError, OSError):
            issues.append('无效 artifact 登记：'+str(record.get('id') if isinstance(record,dict) else n))

    # Explicit identities on standalone Markdown/YAML files are supported.  We
    # do not scan original source documents or private data looking for IDs.
    for base in [project/'30_outputs',project/'10_literature']:
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in {'.md','.yaml','.yml'} or path in documents or '01_source' in path.parts:
                continue
            try:
                data, body = _read(_safe(project,path,ops),ops)
                if valid_id(data.get('id')):
                    documents[path] = [data,deepcopy(data),body]
                    add(data['id'],data.get('object_type') or data['id'].split(':',1)[0],path,data)
            except (ValueError, TypeError, OSError, yaml.YAMLError):
                issues.append('无法读取显式 artifact：'+path.relative_to(project).as_posix())
    for folder in sorted((project/'.runs').glob('*')):
        if not folder.is_dir():
            continue
        task_path, status_path = folder/'task.yaml', folder/'status.yaml'
        if not task_path.is_file() and not status_path.is_file():
            continue
        try:
            task_data = document(task_path) if task_path.is_file() else {}
            status = document(status_path) if status_path.is_file() else {}
            raw = status.get('task_id') or task_data.get('id') or folder.name
            identifier = raw if str(raw).startswith('task:') else 'task:'+str(raw)
            task_data.setdefault('object_id',identifier)
            task_data.setdefault('links',[])
            add(identifier,'task',task_path if task_path.is_file() else status_path,task_data)
            tasks[identifier] = dict(task_id=str(raw).removeprefix('task:'),status=status.get('status','legacy'),
                    status_path=status_path.relative_to(project).as_posix() if status_path.is_file() else None,
                    task_path=task_path.relative_to(project).as_posix() if task_path.is_file() else None)
            for field in ['attempt','max_attempts','decision','updated_at','task_type','execution_target','main_attempts','takeover_reason','active_revision']:
                if field in status:
                    tasks[identifier][field] = status[field]
            for attempt in sorted((folder/'attempts').glob('*/result.yaml')):
                data = document(attempt)
                rid = f'attempt:{str(raw).removeprefix("task:")}:{data.get("attempt",attempt.parent.name)}'
                data.setdefault('object_id',rid)
                data.setdefault('links',[])
                add(rid,'attempt',attempt,data)
        except (ValueError,TypeError,OSError,yaml.YAMLError):
            issues.append('无法索引任务：'+folder.name)

    for identifier,(records,rel) in sorted(source_links.items()):
        records.sort(key=lambda value:(str(value.get('rel')),str(value.get('target')),str(value.get('generated_by','')),_json(value)) if isinstance(value,dict) else ('','','',str(value)))
        for entry in records:
            if not isinstance(entry,dict):
                issues.append('损坏 link：'+identifier)
                continue
            value = deepcopy(entry)
            value['source'] = identifier
            if isinstance(value.get('target'),str):
                value['target'] = aliases.get(value['target'],value['target'])
            value.setdefault('origin',rel)
            links.append(value)
    links.sort(key=lambda value:(str(value.get('source')),str(value.get('rel')),str(value.get('target')),_json(value)))

    # Persistent aliases survive index deletion and source file renaming.
    if isinstance(project_data.get('id_aliases',{}),dict):
        project_data['id_aliases'] = dict(sorted({**persisted_aliases,**aliases}.items(),key=lambda item:str(item[0])))
    for path,(data,before,body) in sorted(documents.items(),key=lambda item:str(item[0])):
        if data != before and mutation:
            try:
                storage.write_text(path,_serialize(path,before,data))
            except (ValueError,OSError):
                issues.append('安全追加失败，原件保留：'+path.relative_to(project).as_posix())
    for identifier,record in artifacts.items():
        try:
            path = _safe(project,record['path'],ops)
            record['hash'] = _hash_file(path)
            record['updated_at'] = datetime.fromtimestamp(path.stat().st_mtime,tz=timezone.utc).isoformat()
        except (ValueError,OSError):
            issues.append('artifact 无法读取：'+identifier)
    index = dict(schema_version=1,generated_by='wf-registry',generated_from=sorted({a['path'] for a in artifacts.values()}),
                 project_id=project_id,artifacts=dict(sorted(artifacts.items())),aliases=dict(sorted(aliases.items())),
                 links=links,tasks=dict(sorted(tasks.items())),duplicates=dict(sorted(duplicates.items())),issues=sorted(set(issues)))
    for error in validate(index,project,ops):
        if error not in index['issues']:
            index['issues'].append(error)
    index['issues'].sort()
    index=json.loads(_json(index))
    old = None
    try:
        old = load_index(project)
    except ValueError:
        pass
    comparable = {key:value for key,value in old.items() if key!='generated_at'} if old else None
    index['generated_at'] = old.get('generated_at') if comparable==index else ops.now()
    if mutation:
        path = _safe(project,'INDEX.json',ops)
        content = _json(index)
        if not path.is_file() or path.read_text(encoding='utf-8-sig') != content:
            storage.write_text(path,content)
    return index


def resolve(project, artifact_ref_or_id, ops, verify_hash=True, index=None):
    index = load_index(project) if index is None else index
    given = {'id':artifact_ref_or_id} if isinstance(artifact_ref_or_id,str) else dict(artifact_ref_or_id)
    identifier = given.get('id')
    identifier = index.get('aliases',{}).get(identifier,identifier)
    if not valid_id(identifier) or identifier not in index.get('artifacts',{}):
        raise ValueError('未登记的 artifact ID：'+str(identifier))
    if identifier in index.get('duplicates',{}):
        raise ValueError('重复 ID 无法解析：'+identifier)
    record = index['artifacts'][identifier]
    path = _safe(project,record['path'],ops)
    if not path.is_file():
        raise ValueError('artifact 路径不存在：'+identifier)
    if verify_hash:
        current = _hash_file(path)
        if record.get('hash') != current or (given.get('hash') and given['hash'] != current):
            raise ValueError('artifact hash 已过期：'+identifier)
    anchor = given.get('anchor')
    if anchor is None and len(record.get('anchors',[])) == 1:
        anchor = record['anchors'][0]
    if anchor is not None:
        if not isinstance(anchor,str) or '\n' in anchor or '\r' in anchor:
            raise ValueError('无效 artifact anchor')
        if anchor not in record.get('anchors',[]) and not _anchor_exists(path,anchor):
            raise ValueError('artifact anchor 不存在：'+identifier)
    ref = dict(id=identifier,type=record['type'],path=record['path'],anchor=anchor,
               role=given.get('role','input'),required=given.get('required',True),hash=record.get('hash'))
    if record.get('contract_type'):
        ref['contract_type'] = record['contract_type']
    return ref


def _anchor_exists(path,anchor):
    lines = re.fullmatch(r'(?:L|lines=)(\d+)(?:[-:](\d+))?',anchor.lstrip('#'))
    if lines:
        try:
            count = len(path.read_text(encoding='utf-8-sig').splitlines())
            start,end = int(lines[1]),int(lines[2] or lines[1])
            return 1<=start<=end<=count
        except (OSError,UnicodeDecodeError):
            return False
    if path.suffix.lower() in {'.yaml','.yml'}:
        try:
            current=yaml.safe_load(path.read_text(encoding='utf-8-sig'))
            for component in anchor.split('.'):
                token=re.fullmatch(r'([\w-]+)(?:\[(\d+)\])?',component)
                if not token or not isinstance(current,dict) or token[1] not in current:
                    return False
                current=current[token[1]]
                if token[2] is not None:
                    if not isinstance(current,list) or int(token[2])>=len(current):
                        return False
                    current=current[int(token[2])]
            return True
        except (OSError,UnicodeDecodeError,yaml.YAMLError):
            return False
    if path.suffix.lower() == '.md':
        body = path.read_text(encoding='utf-8-sig')
        headings = re.findall(r'^#{1,6}\s+(.+?)\s*#*$',body,re.M)
        return anchor in headings or anchor in {re.sub(r'[^\w\s-]','',h).lower().replace(' ','-') for h in headings}
    return False


def validate(index, project, ops):
    """Return all structural connection issues; scientific truth is not checked."""
    issues = []
    artifacts = index.get('artifacts',{})
    if not isinstance(artifacts,dict):
        return ['artifacts 必须为对象']
    for identifier,record in artifacts.items():
        if not valid_id(identifier):
            issues.append('无效 ID：'+str(identifier))
        if not isinstance(record,dict) or record.get('type') not in ARTIFACT_TYPES:
            issues.append('无效 artifact 类型：'+str(identifier)); continue
        try:
            target = _safe(project,record.get('path',''),ops)
            if not target.is_file():
                issues.append('artifact 文件不存在：'+identifier)
        except (ValueError,TypeError):
            issues.append('artifact 路径不安全：'+str(identifier))
    for identifier in index.get('duplicates',{}):
        issues.append('重复 ID：'+identifier)
    for name,target in index.get('aliases',{}).items():
        if not valid_id(target) or target not in artifacts:
            issues.append('悬空别名：'+str(name))
    for link in index.get('links',[]):
        if not isinstance(link,dict):
            issues.append('link 必须为对象'); continue
        source,target = link.get('source'),link.get('target')
        if not valid_id(source) or source not in artifacts:
            issues.append('悬空 link source：'+str(source))
        if not valid_id(target) or target not in artifacts:
            issues.append('悬空 link target：'+str(target))
        if not isinstance(link.get('rel'),str) or not link['rel'].strip():
            issues.append('link 缺 rel：'+str(source))
        evidence = link.get('evidence')
        if not isinstance(evidence,list) or not evidence:
            issues.append('link 缺证据：'+str(source)+' -> '+str(target))
        else:
            for proof in evidence:
                if not isinstance(proof,(str,dict)):
                    issues.append('link 证据类型错误：'+str(source)); continue
                raw = proof if isinstance(proof,str) else proof.get('file') or proof.get('path')
                if raw:
                    try:
                        path = _safe(project,str(raw).split('#',1)[0],ops)
                        if not path.is_file():
                            canonical=index.get('aliases',{}).get(str(raw).split('#',1)[0])
                            if isinstance(canonical,str) and canonical in artifacts:
                                path=_safe(project,artifacts[canonical]['path'],ops)
                        if not path.is_file():
                            issues.append('link 证据文件缺失：'+str(raw))
                    except (ValueError,TypeError):
                        issues.append('link 证据路径不安全：'+str(raw))
                elif isinstance(proof,dict) and (not valid_id(proof.get('id')) or proof['id'] not in artifacts):
                    issues.append('link 证据缺本地来源：'+str(source))
        confidence = link.get('confidence')
        if (confidence not in ('low','medium','high') and
                not (isinstance(confidence,(int,float)) and not isinstance(confidence,bool) and 0<=confidence<=1)):
            issues.append('link confidence 无效：'+str(source))
        if link.get('status') not in ('candidate','verified','rejected','stale'):
            issues.append('link status 无效：'+str(source))
        if 'weight' in link and (not isinstance(link['weight'],(int,float)) or isinstance(link['weight'],bool) or not 0<=link['weight']<=1):
            issues.append('link weight 无效：'+str(source))
    return sorted(set(issues))


def register(root, project, ops, records):
    """Persist only new artifact identity/connection records, then rebuild."""
    project = Path(project).resolve()
    if isinstance(records,dict):
        records = records.get('artifacts',[records])
    if not isinstance(records,list):
        raise ValueError('artifact 登记需要列表')
    path = _safe(project,'project.yaml',ops)
    before = ops.load(path)
    data = deepcopy(before)
    existing = data.setdefault('artifact_registry',[])
    if not isinstance(existing,list):
        raise ValueError('artifact_registry 必须为列表')
    prepared = []
    for record in records:
        if not isinstance(record,dict) or not valid_id(record.get('id')):
            raise ValueError('artifact 登记需要稳定 ID')
        target = _safe(project,record.get('path',''),ops)
        if not target.is_file():
            raise ValueError('artifact 登记路径不存在')
        kind = record.get('type',record['id'].split(':',1)[0])
        if kind not in ARTIFACT_TYPES:
            raise ValueError('artifact 登记 type 无效')
        item = dict(id=record['id'],type=kind,path=target.relative_to(project).as_posix(),links=deepcopy(record.get('links',[])))
        for key in ['anchor','label','aliases','contract_type']:
            if key in record:
                item[key] = deepcopy(record[key])
        prepared.append(item)
    for item in prepared:
        match = next((entry for entry in existing if isinstance(entry,dict) and entry.get('id')==item['id']),None)
        if match is None:
            existing.append(item)
        else:
            # A legitimate moved artifact keeps its identity and source links.
            match['path'] = item['path']
            for key in ['anchor','label','aliases','contract_type']:
                if key in item:
                    match[key] = item[key]
    if data!=before:
        storage.write_text(path,_serialize(path,before,data))
    return build(root,project,ops)
