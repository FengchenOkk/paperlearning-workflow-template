"""文献文件管理与可重新生成的分类/知识视图；不调用模型或网络。"""
from collections import Counter, defaultdict
from pathlib import Path
import re
import warnings
from urllib.parse import unquote
import yaml
try:
    from . import storage
except ImportError:
    import storage

TODO = 'TODO(user)'
LEGACY = ['overview.md', 'close-reading.md', 'context.md', 'note.md',
          'formulas.yaml', 'concepts.yaml', 'extraction.yaml']
READING_HEADINGS = ['全局定位', '论文地图与逻辑链', '逐节精读', '方法与公式', '实验设计与结果',
                    '前因后果与代表文献', '局限性与边界条件', '与当前研究方向的关系',
                    '复现线索', '待验证问题', '证据与来源索引']
OLD_STATUSES = {'triage': 'pre-read', 'read': 'deep-read', 'extracted': 'deep-read'}
PAPER_FILES = {'translation.md': '02_translation/translation.md',
               'reading.md': '03_reading/reading.md', 'analysis.yaml': '04_analysis/analysis.yaml',
               'notes.md': '05_notes/notes.md', 'note.md': '05_notes/notes.md', 'source': '01_source'}

def paper_path(folder, name):
    current = Path(folder) / PAPER_FILES.get(name, name)
    return current if current.exists() else Path(folder) / name

def resolve_path(project, value, ops):
    """旧任务包和来源路径在原件清理后仍可定位；存在的原件优先。"""
    target = ops.contained(project, value)
    if target.exists():
        return target
    try:
        from . import registry
    except ImportError:
        import registry
    try:
        index=registry.load_index(project)
        alias=index.get('aliases',{}).get(str(value).split('#',1)[0])
        if alias:
            ref=registry.resolve(project,alias,ops,verify_hash=False,index=index)
            return ops.contained(project,ref['path'])
    except (ValueError,OSError,TypeError):
        pass
    parts = target.relative_to(project).parts
    if len(parts) >= 4 and parts[:2] == ('10_literature', 'papers'):
        name = parts[3]
        if name in PAPER_FILES:
            alias = Path(*parts[:3]) / PAPER_FILES[name] / Path(*parts[4:])
            alternative = ops.contained(project, alias)
            if alternative.exists():
                return alternative
    return target

def markdown(path):
    text = path.read_text(encoding='utf-8-sig')
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not match:
        return {}, text
    try:
        data = yaml.safe_load(match[1])
    except yaml.YAMLError:
        raise ValueError('Markdown front matter 损坏；原始内容已隐藏') from None
    if not isinstance(data, dict):
        raise ValueError(f'Markdown front matter 需要对象：{path}')
    return data, text[match.end():]

def write_markdown(path, info, body):
    storage.write_text(path, '---\n' + yaml.safe_dump(info, allow_unicode=True, sort_keys=False) + '---\n\n' + body)

def meaningful(value):
    return value not in (None, '', TODO, 'TODO') if isinstance(value, (str, type(None))) else bool(value)

def cell(value):
    return str(value if value is not None else TODO).replace('|', '\\|').replace('\n', ' ')

class Library:
    def __init__(self, root, project, ops, dry_run=False):
        self.root, self.p, self.ops = Path(root), Path(project), ops
        self.base = self.ops.contained(self.p,'10_literature')
        self.dry_run = dry_run
        self.scan_issues = []
        self._paper_paths, self._paper_aliases = {}, {}
        self._concept_paths, self._concept_aliases = {}, {}

    def warn(self, text):
        self.scan_issues.append(text)
        warnings.warn(text, UserWarning)

    def write(self, path, info, body):
        self.ops.contained(self.p,path)
        if self.dry_run:
            print('预览生成：' + Path(path).relative_to(self.p).as_posix())
        else:
            write_markdown(path, info, body)

    def papers(self):
        records = {}
        for file in sorted((self.base / 'papers').glob('*/meta.yaml')):
            try:
                self.ops.contained(self.p,file)
                row = self.ops.load(file)
                self.ops.paper_key(file.parent.name)
                for field in ['categories', 'topic_tags', 'concept_ids', 'formula_ids', 'first_principle_ids']:
                    if field in row and (not isinstance(row[field], list) or any(not isinstance(x, str) for x in row[field])):
                        raise ValueError('元数据列表格式错误')
                if 'zotero' in row and not isinstance(row['zotero'],dict):
                    raise ValueError('Zotero 元数据必须为对象')
                identifier=row.get('id')
                if meaningful(identifier) and (not isinstance(identifier,str) or not identifier.startswith('paper:')):
                    raise ValueError('论文稳定 ID 无效')
                key=identifier.split(':',1)[1] if meaningful(identifier) else row.get('citekey',file.parent.name)
                self.ops.paper_key(key)
                if key in records:raise ValueError('论文稳定 ID 重复')
                records[key] = row
                self._paper_paths[key]=file.parent
                for alias in [key,file.parent.name,row.get('citekey'),identifier]:
                    if isinstance(alias,str):self._paper_aliases[alias]=key
                for alias in row.get('aliases',[]) if isinstance(row.get('aliases',[]),list) else []:
                    if isinstance(alias,str):self._paper_aliases[alias]=key
            except (ValueError, OSError, TypeError):
                self.warn(f'跳过损坏论文：{file.parent.name}/meta.yaml；请修复后重新扫描。')
        return records

    def concepts(self):
        records = {}
        for file in sorted((self.base / 'concepts').glob('*.md')):
            try:
                self.ops.contained(self.p,file)
                row = markdown(file)[0]
                for field in ['prerequisites','related','contrasts','papers','extends','replaces']:
                    if field in row and (not isinstance(row[field],list) or any(not isinstance(x,str) for x in row[field])):
                        raise ValueError('概念列表格式错误')
                row.setdefault('is_first_principle',False)
                row.setdefault('canonical_statement',TODO)
                identifier=row.get('id')
                if meaningful(identifier) and (not isinstance(identifier,str) or not identifier.startswith('concept:')):
                    raise ValueError('概念稳定 ID 无效')
                cid=identifier.split(':',1)[1] if meaningful(identifier) else row.get('concept_id',file.stem)
                self.ops.slug(cid)
                if cid in records:raise ValueError('概念稳定 ID 重复')
                records[cid] = row
                self._concept_paths[cid]=file
                for alias in [cid,file.stem,row.get('concept_id'),identifier]:
                    if isinstance(alias,str):self._concept_aliases[alias]=cid
            except (ValueError, OSError, TypeError):
                self.warn(f'跳过损坏概念卡：{file.name}；请修复后重新扫描。')
        return records

    def paper_key_alias(self,value):
        return self._paper_aliases.get(value,value)

    def concept_key_alias(self,value):
        return self._concept_aliases.get(value,value)

    def _indexed_path(self,identifier):
        try:
            from . import registry
        except ImportError:
            import registry
        try:
            ref=registry.resolve(self.p,identifier,self.ops,verify_hash=False)
            return self.ops.contained(self.p,ref['path'])
        except (ValueError,OSError,TypeError):
            return None

    def paper_folder(self,key):
        canonical=self.paper_key_alias(key)
        identifier=canonical if isinstance(canonical,str) and canonical.startswith('paper:') else 'paper:'+str(canonical)
        indexed=self._indexed_path(identifier)
        if indexed is not None:return indexed.parent
        if canonical in self._paper_paths:return self._paper_paths[canonical]
        self.papers()
        return self._paper_paths.get(self.paper_key_alias(key),self.base/'papers'/str(key))

    def concept_path(self,cid):
        canonical=self.concept_key_alias(cid)
        identifier=canonical if isinstance(canonical,str) and canonical.startswith('concept:') else 'concept:'+str(canonical)
        indexed=self._indexed_path(identifier)
        if indexed is not None:return indexed
        if canonical in self._concept_paths:return self._concept_paths[canonical]
        self.concepts()
        return self._concept_paths.get(self.concept_key_alias(cid),self.base/'concepts'/(str(cid)+'.md'))

    def generated(self, body, paths):
        info = self.ops.provenance('orchestrator')
        info.update(prompt_version='v2', status='generated', source_refs=sorted(set(paths)))
        info.update(schema_version=1, generated_from=sorted(set(paths)), generated_at=self.ops.now())
        return info, body

    def ensure_project_files(self):
        if self.dry_run:
            return
        self.ops.contained(self.p,self.base/'concepts').mkdir(exist_ok=True)
        for name in ['README.md', 'reading-list.md', 'knowledge-map.md']:
            dest = self.base / name
            if not dest.exists():
                storage.copy_file(self.root / 'workflow/layouts/project/10_literature' / name, dest)

    def migrate(self):
        """复制迁移：保留旧原件，冲突逐项报告，元数据变更先备份。"""
        self.ensure_project_files()
        template = self.root / 'workflow/layouts/paper'
        report = {'schema_version': 1, 'generated_by': 'wf', 'generated_at': self.ops.now(),
                  'generated_from': [], 'copied': [], 'generated': [], 'conflicts': [], 'errors': []}
        for folder in sorted((self.base / 'papers').glob('*')):
            if not folder.is_dir() or not (folder / 'meta.yaml').is_file():
                continue
            try:
                self.ops.paper_key(folder.name)
                self.ops.contained(self.p,folder)
                meta_path = folder / 'meta.yaml'
                meta = self.ops.load(meta_path)
                defaults = self.ops.load(template / 'meta.yaml')
                new = dict(defaults, **meta)
                new['status'] = OLD_STATUSES.get(meta.get('status'), meta.get('status', 'unread'))
                for key in ['created_at', 'updated_at', 'year']:
                    if new[key] is None:
                        new[key] = TODO
                old_files = [name for name in LEGACY + ['translation.md','reading.md','analysis.yaml','source']
                             if (folder/name).exists()]
                if old_files:
                    warnings.warn(f'{folder.name} 旧结构保留；编号目录迁移只补缺失文件。', UserWarning)
                if not old_files and new == meta:
                    continue
                report['generated_from'].append(meta_path.relative_to(self.p).as_posix())
                prior_copied,prior_conflicts=len(report['copied']),len(report['conflicts'])
                if not self.dry_run:
                    run_dir = self.p/'.runs'/(self.ops.now().replace(':','').replace('.','-')+'-migration-'+folder.name)
                    self.ops.contained(self.p,run_dir)
                else:
                    run_dir = None

                def copy_missing(source, target):
                    self.ops.contained(self.p,target)
                    if target.exists():
                        if target.read_bytes() != source.read_bytes():
                            if source.name=='analysis.yaml':
                                left,right=self.ops.load(source),self.ops.load(target)
                                if all(right.get(k)==v for k,v in left.items()):
                                    return
                            conflict = {'source': source.relative_to(self.p).as_posix(),
                                        'target': target.relative_to(self.p).as_posix()}
                            report['conflicts'].append(conflict)
                            print('迁移冲突（不覆盖）：'+conflict['target'])
                        return
                    report['copied'].append(target.relative_to(self.p).as_posix())
                    if not self.dry_run:
                        storage.copy_file(source, target)

                for old, numbered in PAPER_FILES.items():
                    if old in ['source', 'notes.md'] or not (folder/old).is_file():
                        continue
                    copy_missing(folder/old, folder/numbered)
                source = folder/'source'
                if source.is_dir():
                    for file in sorted(source.rglob('*')):
                        if file.is_file():
                            self.ops.contained(self.p, file)
                            if file.is_symlink():
                                raise ValueError('原始材料符号链接需人工归档')
                            copy_missing(file, folder/'01_source'/file.relative_to(source))
                if self.dry_run:
                    if new != meta:
                        print('预览补充元数据（将先备份）：'+str(meta_path.relative_to(self.p)))
                    for filename in ['translation.md','reading.md','analysis.yaml','notes.md']:
                        dest=folder/PAPER_FILES[filename]
                        rel=dest.relative_to(self.p).as_posix()
                        if not dest.exists() and rel not in report['copied']:
                            report['generated'].append(rel)
                            print('预览补充骨架：'+rel)
                    continue

                if new != meta:
                    storage.copy_file(meta_path, run_dir/'meta.before.yaml')
                    self.ops.save(meta_path, new)
                # 最早期零散文献文件也合入编号骨架；原文始终留在旧位置。
                reading = folder/PAPER_FILES['reading.md']
                self.ops.contained(self.p,reading)
                if not reading.exists():
                    info, body = markdown(template/PAPER_FILES['reading.md'])
                    body = body.replace('论文精读：'+TODO, '论文精读：'+folder.name)
                    for name, section in {'overview.md':1,'close-reading.md':3,'context.md':6,'note.md':10}.items():
                        if (folder/name).is_file():
                            heading = f'## {section}. {READING_HEADINGS[section-1]}'
                            body = body.replace(heading, heading+'\n\n### 旧内容（保留原文，待整理）\n\n'
                                                +(folder/name).read_text(encoding='utf-8-sig'))
                    info.update(self.ops.provenance('literature-reader'), prompt_version='v3')
                    info.pop('status',None)
                    write_markdown(reading,info,body)
                analysis_path = folder/PAPER_FILES['analysis.yaml']
                self.ops.contained(self.p,analysis_path)
                if not analysis_path.exists():
                    analysis = self.ops.load(template/PAPER_FILES['analysis.yaml'])
                    for name, target in [('extraction.yaml','extraction'),('formulas.yaml','formulas'),('concepts.yaml','concepts')]:
                        if not (folder/name).is_file():
                            continue
                        old = yaml.safe_load((folder/name).read_text(encoding='utf-8-sig'))
                        if target == 'extraction' and isinstance(old,dict):
                            for key in analysis['extraction']:
                                if key in old:
                                    value = old[key]
                                    analysis['extraction'][key] = {'legacy_items':value} if key=='method' and isinstance(value,list) else value
                            analysis['legacy_extraction'] = {k:v for k,v in old.items()
                                                            if k not in analysis['extraction'] and k not in self.ops.PROVENANCE}
                            analysis['source_refs'] = old.get('source_refs',[])
                        elif isinstance(old,list) or isinstance(old,dict) and isinstance(old.get(target),list):
                            analysis[target] = old if isinstance(old,list) else old[target]
                        else:
                            analysis['legacy_'+target] = old
                    analysis.update(self.ops.provenance('literature-reader'),paper=folder.name,
                                    prompt_version='v3',source_refs=analysis['source_refs'])
                    analysis.pop('status',None)
                    self.ops.save(analysis_path,analysis)
                elif (folder/'analysis.yaml').is_file() and analysis_path.read_bytes() == (folder/'analysis.yaml').read_bytes():
                    analysis = self.ops.load(analysis_path)
                    changed = False
                    for key in ['first_principles','review_similarity']:
                        if key not in analysis:
                            analysis[key] = self.ops.load(template/PAPER_FILES['analysis.yaml'])[key]
                            changed = True
                    if changed:
                        self.ops.save(analysis_path,analysis)
                for name in ['translation.md','notes.md']:
                    dest = folder/PAPER_FILES[name]
                    self.ops.contained(self.p,dest)
                    if not dest.exists():
                        storage.copy_file(template/PAPER_FILES[name],dest)
                        self.ops.stamp_markdown(dest,'literature-reader')
                (folder/'01_source').mkdir(exist_ok=True)
                # 不把兼容提示写入旧原文；记录旧/新映射供用户核对后手动删除。
                mapping = {name:PAPER_FILES.get(name,'03_reading/reading.md') for name in old_files}
                if new != meta or len(report['copied'])>prior_copied or len(report['conflicts'])>prior_conflicts:
                    self.ops.save(run_dir/'run.yaml',dict(report,status='migration',paper=folder.name,
                                                         legacy_mapping=mapping,note='旧原件未删除；冲突需人工合并。'))
            except (ValueError,OSError,yaml.YAMLError,TypeError) as error:
                report['errors'].append(folder.name)
                self.warn(f'迁移跳过损坏条目：{folder.name}（{type(error).__name__}）；原件保留。')
        for name in ['collections','catalog','synthesis']:
            if (self.base/name).exists():
                warnings.warn(f'保留旧 {name}/；请人工整理，工具不删除。',UserWarning)
        if self.dry_run or report['generated_from'] or report['errors']:
            print(f'迁移{"预览" if self.dry_run else "完成"}：复制 {len(report["copied"])} 项；'
                  f'冲突 {len(report["conflicts"])} 项；损坏 {len(report["errors"])} 项。')
        return report

    def new_concept(self, concept_id):
        self.ops.slug(concept_id)
        target = self.ops.contained(self.base / 'concepts', concept_id + '.md')
        if target.exists():
            raise ValueError('概念已存在，不覆盖')
        target.parent.mkdir(exist_ok=True)
        info, body = markdown(self.root / 'workflow/layouts/concept.md')
        info.update(self.ops.provenance('knowledge-builder'), concept_id=concept_id, status='not-started', prompt_version='v2')
        body = body.replace('概念：TODO(user)', '概念：' + concept_id)
        write_markdown(target, info, body)
        return target

    def paper_rows(self, records):
        lines = ['| 论文 | 年份 | 类型 | 优先级 | 状态 |', '|---|---|---|---|---|']
        for key, row in records:
            rel=self.paper_folder(key).relative_to(self.p).as_posix()
            lines.append(f'| [{cell(key)}]({rel}/) | {cell(row.get("year"))} | {cell(row.get("paper_role"))} | {cell(row.get("reading_priority"))} | {cell(row.get("status"))} |')
        return lines if len(lines)>2 else ['TODO(user)：暂无条目。']

    def index(self):
        if not self.dry_run:
            self.migrate()
        papers = self.papers()
        data, profile = self.ops.load(self.p / 'project.yaml'), self.ops.load(self.p / 'research-profile.yaml')
        lines = ['# 项目索引', '', '> 扫描生成，请勿手工维护分类。', '', '## 项目概览', '',
                 f'项目：{data["title"]}；阶段：{data["stage"]}', f'方向：{profile["direction"]}',
                 f'当前 claim：{data.get("current_claim")}；下一步：{data.get("next_action")}', '',
                 '- [阅读清单](10_literature/reading-list.md)', '- [对比矩阵](10_literature/matrix.md)',
                 '- [知识网络](10_literature/knowledge-map.md)', '', '## 全部论文', '']
        lines += self.paper_rows(papers.items())
        lines += ['', '## 论文通读入口', '', '| 论文 | 综合总结 | 概念学习指南 | 全文翻译 | 精读与证据 |', '|---|---|---|---|---|']
        for key in sorted(papers):
            folder=self.paper_folder(key)
            targets=['06_synthesis/summary.md','06_synthesis/concept-guide.md','02_translation/translation.md','03_reading/reading.md']
            labels=['综合总结','概念指南','全文翻译','精读']
            cells=[f'[{label}]({(folder/target).relative_to(self.p).as_posix()})' if (folder/target).is_file() else '尚未生成' for target,label in zip(targets,labels)]
            lines += ['| '+cell(key)+' | '+' | '.join(cells)+' |']
        for field, title in [('categories','category'), ('topic_tags','topic'), ('paper_role','paper_role'), ('status','status')]:
            lines += ['', f'## 按 {title} 分类', '']
            groups = defaultdict(list)
            for key, row in papers.items():
                values = row.get(field, []) if field in ('categories','topic_tags') else [row.get(field, TODO)]
                for value in set(values or [TODO]): groups[str(value)].append((key,row))
            for group, rows in sorted(groups.items()):
                lines += [f'### {cell(group)}', ''] + self.paper_rows(rows) + ['']
            if not groups: lines += [TODO]
        lines += ['', '## 时间线', '']
        ordered = sorted(papers.items(), key=lambda kv: (str(kv[1].get('year', TODO)),kv[0]))
        lines += self.paper_rows(ordered)
        lines += ['', '## 文献综合工作稿', '']
        for file in sorted(self.base.glob('*.md')):
            if file.name not in ['README.md','reading-list.md','matrix.md','knowledge-map.md']:
                rel = file.relative_to(self.p).as_posix(); lines += [f'- [{rel}]({rel})']
        # 旧项目的综合稿仍可导航，不迁移或隐藏用户文件。
        for file in sorted((self.base / 'synthesis').rglob('*')):
            if file.is_file() and not file.name.startswith('.') and file.name != 'README.md':
                rel = file.relative_to(self.p).as_posix(); lines += [f'- [{rel}]({rel})（旧目录保留）']
        lines += ['', '## 复现 claim 摘要', '']
        claim_paths = []
        for file in sorted((self.p / '20_reproduction').glob('*/claim.yaml')):
            claim = self.ops.load(file); rel = file.relative_to(self.p).as_posix(); claim_paths.append(rel)
            lines += [f'- [{claim["claim_id"]}]({rel})：路线 {claim["route"]} / {claim["status"]}']
        lines += ['', '## 正式输出', '']
        for file in sorted((self.p / '30_outputs').rglob('*')):
            if file.is_file() and not file.name.startswith('.') and file.name != 'README.md':
                rel=file.relative_to(self.p).as_posix(); lines += [f'- [{rel}]({rel})']
        paths = ['project.yaml','research-profile.yaml'] + [(self.paper_folder(key)/'meta.yaml').relative_to(self.p).as_posix() for key in papers] + claim_paths
        info, body = self.generated('\n'.join(lines)+'\n',paths)
        self.write(self.p / 'INDEX.md', info, body)
        self.reading_list(papers)
        self.knowledge_map(papers)

    def reading_list(self, papers):
        path = self.base / 'reading-list.md'
        info, body = markdown(path if path.exists() else self.root/'workflow/layouts/project/10_literature/reading-list.md')
        notes, topics, order = info.get('reading_notes',{}), info.get('topic_paths',{}), info.get('reading_order',[])
        if not isinstance(notes,dict) or not isinstance(topics,dict) or not isinstance(order,list):
            raise ValueError('阅读清单 reading_notes/topic_paths/reading_order 类型错误')
        if path.exists():
            try:
                self.check_reading_list(papers)
            except ValueError:
                self.warn('阅读清单含损坏/缺失论文引用；保留人工备注，扫描其他论文继续，验收前修复引用。')
        def table(keys):
            rows = ['| citekey | 年份 | 类型 | 为什么读 | 优先级 | 当前状态 |', '|---|---|---|---|---|---|']
            for key in keys:
                key=self.paper_key_alias(key)
                if key not in papers:
                    continue
                row=papers[key]
                reason=notes.get(key,TODO)
                if isinstance(reason,dict): reason=reason.get('why_read',TODO)
                rel=self.paper_folder(key).relative_to(self.base).as_posix()
                rows += [f'| [{key}]({rel}/) | {cell(row.get("year"))} | {cell(row.get("paper_role"))} | {cell(reason)} | {cell(row.get("reading_priority"))} | {cell(row.get("status",TODO))} |']
            return rows if len(rows)>2 else [TODO]
        lines=[]
        for role,title in [('survey','综述'), ('classic','经典/奠基'), ('group-recent','课题组近期工作')]:
            lines += [f'## {title}','']+table([k for k,v in papers.items() if v.get('paper_role')==role])+['']
        lines += ['## 主题阅读路径','']
        paths=defaultdict(list)
        for key,row in papers.items():
            for topic in set(row.get('categories',[])+row.get('topic_tags',[])): paths[topic].append(key)
        paths.update(topics)
        for topic,keys in sorted(paths.items()):
            lines += [f'### {cell(topic)}','']+table(keys)+['']
        if not paths: lines += [TODO,'']
        lines += ['## 推荐阅读顺序',''] + table(order + [k for k in sorted(papers, key=lambda k:(str(papers[k].get('reading_priority',TODO)),k)) if k not in order])
        start,end='<!-- wf:reading-list:begin -->','<!-- wf:reading-list:end -->'
        content=start+'\n'+'\n'.join(lines)+'\n'+end
        if start not in body or end not in body:
            warnings.warn('reading-list.md 没有生成标记，保留手工正文；请按模板添加标记后重新生成。',UserWarning)
            return
        body=re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda _:content,body,count=1,flags=re.S)
        # 不改动人写的 reading_notes、topic_paths、reading_order 或标记区外正文。
        info.update(generated_by='wf', model_role='orchestrator',prompt_version='v2',created_at=self.ops.now(),
                    source_refs=[(self.paper_folder(k)/'meta.yaml').relative_to(self.p).as_posix() for k in papers])
        info.update(schema_version=1,generated_from=info['source_refs'],generated_at=self.ops.now())
        self.write(path,info,body)

    def check_reading_list(self, papers):
        info, body = markdown(self.base / 'reading-list.md')
        notes=info.get('reading_notes',{})
        topics=info.get('topic_paths',{})
        order=info.get('reading_order',[])
        if not isinstance(notes,dict) or not isinstance(topics,dict) or not isinstance(order,list):
            raise ValueError('阅读清单注释字段类型错误')
        if any(not isinstance(k,str) for k in notes) or any(not isinstance(k,str) for k in order):
            raise ValueError('阅读清单 citekey 必须为字符串')
        keys=set(notes)
        keys.update(order)
        for values in topics.values():
            if not isinstance(values,list) or not all(isinstance(k,str) for k in values): raise ValueError('主题阅读路径必须是 citekey 字符串列表')
            keys.update(values)
        for text in re.findall(r'\]\(([^)]+)\)',body):
            clean=unquote(text.split('#',1)[0])
            match=re.search(r'(?:^|/)papers/([^/]+)/?',clean)
            if match: keys.add(match[1])
        # 支持手工表格第一列直接写 citekey，以及 citekey: value。
        for line in body.splitlines():
            if line.strip().startswith('|'):
                value=line.strip().split('|')[1].strip().strip('`')
                if value and value not in ('citekey','论文') and not value.startswith(('[','-','TODO')):
                    keys.add(value)
        keys.update(re.findall(r'\bcitekey:\s*([A-Za-z0-9_.-]+)',body))
        canonical_keys={self.paper_key_alias(k) for k in keys if isinstance(k,str)}
        if any(not isinstance(k,str) for k in keys) or canonical_keys-set(papers):
            raise ValueError('阅读清单引用不存在的 citekey：'+', '.join(map(str,canonical_keys-set(papers))))

    def knowledge_map(self, papers):
        try:
            from . import knowledge
        except ImportError:
            import knowledge
        return knowledge.generate(self,papers)

    def validate(self):
        papers=self.papers();cards=self.concepts()
        if self.scan_issues:
            raise ValueError('存在损坏论文或概念卡；扫描已继续，验收前必须修复。')
        legacy_project=any((self.base/name).exists() for name in ['catalog','collections','synthesis'])
        for name in ['README.md','concepts','reading-list.md','knowledge-map.md']:
            if not (self.base/name).exists():
                if legacy_project or any((self.paper_folder(k)/'note.md').exists() for k in papers):
                    warnings.warn(f'旧项目缺少 {name}；运行 index 合并新骨架，保留原件。',UserWarning)
                else:raise ValueError(f'文献模块缺少 {name}')
        for key,meta in papers.items():
            folder=self.paper_folder(key)
            old=[f for f in LEGACY+['translation.md','reading.md','analysis.yaml','source'] if (folder/f).exists()]
            for name in old:warnings.warn(f'迁移提示：{key}/{name} 原件保留，映射见文献说明。',UserWarning)
            if self.paper_key_alias(meta.get('citekey'))!=key:raise ValueError('citekey 与稳定论文 ID 不一致')
            if old and any(not paper_path(folder,f).exists() for f in ['reading.md','analysis.yaml']):
                warnings.warn(f'{key} 尚未迁移；运行 index 安全合并。',UserWarning)
                self.ops.refs(self.p,meta)
                continue
            checked_meta=meta
            numbered=all((folder/PAPER_FILES[f]).exists() for f in ['translation.md','reading.md','analysis.yaml'])
            if numbered:
                for dirname in ['01_source','02_translation','03_reading','04_analysis','05_notes']:
                    if not (folder/dirname).is_dir():
                        raise ValueError(f'{key} 缺少标准文件夹 {dirname}')
            if not numbered and old:
                warnings.warn(f'{key} 旧目录兼容读取；运行 migrate 生成编号目录。',UserWarning)
                checked_meta=dict(self.ops.load(self.root/'workflow/layouts/paper/meta.yaml'),**meta)
            self.ops.contract(self.root,'paper',checked_meta)
            binding=checked_meta['zotero']
            if binding['library_type'] not in ['user','group','export',TODO,'TODO']:
                raise ValueError('Zotero library_type 不合法')
            if binding['library_type'] in ['user','group'] and meaningful(binding['library_id']) and not binding['library_id'].isdigit():
                raise ValueError('Zotero library_id 必须为数字字符串')
            for name in ['meta.yaml','translation.md','reading.md','analysis.yaml','source']:
                if not paper_path(folder,name).exists():raise ValueError(f'{key} 缺少 {PAPER_FILES.get(name,name)}')
            if numbered and not (folder/PAPER_FILES['notes.md']).is_file():
                raise ValueError(f'{key} 缺少 05_notes/notes.md')
            if isinstance(meta['year'],str) and meta['year']!=TODO:raise ValueError('year 只能是整数或 TODO(user)')
            self.ops.refs(self.p,meta)
            for ref in meta['source_files']:
                if not resolve_path(self.p,ref,self.ops).is_file():raise ValueError('source_files 文件不存在')
            analysis=self.ops.load(paper_path(folder,'analysis.yaml'))
            if not numbered:
                defaults=self.ops.load(self.root/'workflow/layouts/paper'/PAPER_FILES['analysis.yaml'])
                analysis=dict(defaults,**analysis)
            self.ops.contract(self.root,'analysis',analysis)
            if self.paper_key_alias(analysis['paper'])!=key:raise ValueError('analysis.paper 与稳定论文 ID 不一致')
            self.ops.refs(self.p,analysis)
            principles=[entry['id'] for entry in analysis['first_principles']]
            if len(principles)!=len(set(principles)):
                raise ValueError('第一性原理 ID 重复')
            for entry in analysis['first_principles']:
                self.ops.slug(entry['id'])
                associated=entry.get('concept_ids',[entry['id']])
                if not associated:
                    raise ValueError('第一性原理必须关联全局概念卡')
                if meaningful(entry['statement']) and not entry['source_refs']:
                    raise ValueError('第一性原理结论需要 source_refs')
                for cid in associated:
                    if self.concept_key_alias(cid) not in cards:
                        raise ValueError('第一性原理关联概念卡不存在：'+cid)
            for principle in checked_meta['first_principle_ids']:
                if principle not in principles and not cards.get(self.concept_key_alias(principle),{}).get('is_first_principle'):
                    raise ValueError('meta.first_principle_ids 未定义或未关联全局概念卡')
            for cid in analysis['review_similarity']['key_concepts']:
                if self.concept_key_alias(cid) not in cards:
                    raise ValueError('综述比较引用的概念卡不存在：'+cid)
            ids=[f['id'] for f in analysis['formulas']]
            if len(ids)!=len(set(ids)):raise ValueError('公式 ID 重复')
            if any(i not in ids for i in meta['formula_ids']):raise ValueError('meta.formula_ids 未在 analysis 中定义')
            for f in analysis['formulas']:
                self.ops.slug(f['id'])
                if isinstance(f['confidence'],str) and f['confidence']!=TODO:raise ValueError('公式 confidence 不合法')
                for cid in f['related_concepts']:
                    if self.concept_key_alias(cid) not in cards:raise ValueError('公式关联概念卡不存在')
            ids=[c['id'] for c in analysis['concepts']]
            if len(ids)!=len(set(ids)):raise ValueError('论文概念 ID 重复')
            for cid in set(ids+meta['concept_ids']):
                cid=self.concept_key_alias(cid)
                self.ops.slug(cid)
                if cid not in cards:raise ValueError(f'概念卡不存在：{cid}')
            try:
                from . import study
            except ImportError:
                import study
            for kind, (filename, _, _) in study.DELIVERIES.items():
                path=folder/'06_synthesis'/filename
                if path.is_file():
                    study.validate_delivery(self.root,self.p,path,kind,meta['id'],self.ops)
                    self.check_concept_links(markdown(path)[1],path.parent,cards)
            if meta['translation_status']=='complete' and (folder/'02_translation/coverage.yaml').exists():
                result=study.coverage(self.root,self.p,key,self.ops)
                if not result['structural_coverage']:
                    raise ValueError('完成翻译覆盖核对未通过：'+'; '.join(result['errors']))
            for name in ['translation.md','reading.md']:
                path=paper_path(folder,name)
                info,body=markdown(path)
                self.ops.refs(self.p,info)
                self.check_concept_links(body,path.parent,cards)
                progress=meta['translation_status' if name=='translation.md' else 'reading_status']
                # 为旧输出兼容 front matter.status，但不得与 meta 的进度矛盾。
                if info.get('status')=='complete' and progress!='complete':raise ValueError('完成状态必须统一写入 meta.yaml')
                if progress=='complete':
                    if not body.strip():raise ValueError('完成文件不能为空')
                    if name=='reading.md':
                        headings=re.findall(r'^##\s+(\d+)\.\s*(.+?)\s*$',body,re.M)
                        if any((str(i),h) not in headings for i,h in enumerate(READING_HEADINGS,1)):
                            raise ValueError('完成精读缺少固定章节')
                    elif re.search(r'TODO(?:\(user\))?',body,re.I):
                        raise ValueError('完成翻译仍包含 TODO 占位内容')
        for cid,card in cards.items():
            self.ops.contract(self.root,'concept',card)
            self.ops.slug(cid)
            if self.concept_key_alias(card['concept_id'])!=cid:raise ValueError('概念 ID 与稳定 ID 不一致')
            self.ops.refs(self.p,card)
            for field in ['prerequisites','related','contrasts','extends','replaces']:
                for linked in card.get(field,[]):
                    if self.concept_key_alias(linked) not in cards:raise ValueError(f'概念 {cid} 引用缺失卡：{linked}')
            for key in card['papers']:
                if self.paper_key_alias(key) not in papers:raise ValueError('概念引用论文不存在')
            if meaningful(card['first_defined_in']) and self.paper_key_alias(card['first_defined_in']) not in papers:
                raise ValueError('first_defined_in 需指向本地 citekey 或 TODO(user)')
            self.check_concept_links(markdown(self.concept_path(cid))[1],self.base/'concepts',cards)
        if (self.base/'reading-list.md').exists():self.check_reading_list(papers)
        try:
            from . import knowledge
        except ImportError:
            import knowledge
        if (self.base/'knowledge-graph.json').exists():
            knowledge.validate(self)
        elif not legacy_project:
            warnings.warn('缺少知识图谱；运行 graph 或 index 后验收。',UserWarning)
        for file in [self.p/'INDEX.md',self.base/'knowledge-map.md',self.base/'reading-list.md']:
            if file.exists():
                info,_=markdown(file)
                if info.get('generated_by')=='wf' and info.get('schema_version')!=1:
                    warnings.warn(f'{file.name} 旧生成格式；运行 index 更新 schema 版本。',UserWarning)
        for name in ['catalog','collections','synthesis']:
            if (self.base/name).exists():warnings.warn(f'旧 {name}/ 保留，需人工迁移。',UserWarning)

    def check_concept_links(self,body,folder,cards):
        for link in re.findall(r'\]\(([^)]+)\)',body):
            clean=unquote(link.split('#',1)[0])
            if 'concepts/' not in clean:continue
            target=resolve_path(self.p,self.ops.contained(self.p,(folder/clean).resolve()).relative_to(self.p).as_posix(),self.ops)
            if not target.exists() and folder.name in ['02_translation','03_reading','05_notes'] and clean.startswith('../../concepts/'):
                warnings.warn('旧相对概念链接兼容读取；请改为 ../../../concepts/<slug>.md。',UserWarning)
                target=self.base/'concepts'/Path(clean).name
            if not target.is_file() or self.concept_key_alias(target.stem) not in cards or target.parent!=self.base/'concepts':
                raise ValueError('Markdown 概念链接不存在或位置错误')
