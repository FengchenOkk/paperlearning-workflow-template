"""文献文件管理与可重新生成的分类/知识视图；不调用模型或网络。"""
from collections import Counter, defaultdict
from pathlib import Path
import re
import warnings
from urllib.parse import unquote
import yaml

TODO = 'TODO(user)'
LEGACY = ['overview.md', 'close-reading.md', 'context.md', 'note.md',
          'formulas.yaml', 'concepts.yaml', 'extraction.yaml']
READING_HEADINGS = ['全局定位', '论文地图与逻辑链', '逐节精读', '方法与公式', '实验设计与结果',
                    '前因后果与代表文献', '局限性与边界条件', '与当前研究方向的关系',
                    '复现线索', '待验证问题', '证据与来源索引']
OLD_STATUSES = {'triage': 'pre-read', 'read': 'deep-read', 'extracted': 'deep-read'}

def markdown(path):
    text = path.read_text(encoding='utf-8-sig')
    match = re.match(r'\A---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not match:
        return {}, text
    data = yaml.safe_load(match[1])
    if not isinstance(data, dict):
        raise ValueError(f'Markdown front matter 需要对象：{path}')
    return data, text[match.end():]

def write_markdown(path, info, body):
    path.write_text('---\n' + yaml.safe_dump(info, allow_unicode=True, sort_keys=False) + '---\n\n' + body, encoding='utf-8')

def meaningful(value):
    return value not in (None, '', TODO, 'TODO') if isinstance(value, (str, type(None))) else bool(value)

def cell(value):
    return str(value if value is not None else TODO).replace('|', '\\|').replace('\n', ' ')

class Library:
    def __init__(self, root, project, ops):
        self.root, self.p, self.ops = Path(root), Path(project), ops
        self.base = self.p / '10_literature'

    def papers(self):
        return {f.parent.name: self.ops.load(f) for f in sorted((self.base / 'papers').glob('*/meta.yaml'))}

    def concepts(self):
        return {f.stem: markdown(f)[0] for f in sorted((self.base / 'concepts').glob('*.md'))}

    def generated(self, body, paths):
        info = self.ops.provenance('orchestrator')
        info.update(prompt_version='v2', status='generated', source_refs=sorted(set(paths)))
        return info, body

    def ensure_project_files(self):
        (self.base / 'concepts').mkdir(exist_ok=True)
        for name in ['README.md', 'reading-list.md', 'knowledge-map.md']:
            dest = self.base / name
            if not dest.exists():
                dest.write_bytes((self.root / 'projects/_template/10_literature' / name).read_bytes())

    def migrate(self):
        """只合并缺失的新文件；原件不删除，冲突不覆盖，元数据更新有快照。"""
        self.ensure_project_files()
        paper_template = self.root / 'workflow/templates/paper'
        for folder in sorted((self.base / 'papers').iterdir()):
            if not folder.is_dir() or not (folder / 'meta.yaml').exists():
                continue
            old_files = [f for f in LEGACY if (folder / f).exists()]
            meta_path = folder / 'meta.yaml'
            meta = self.ops.load(meta_path)
            defaults = self.ops.load(paper_template / 'meta.yaml')
            needs_meta = any(k not in meta for k in defaults) or meta.get('status') in OLD_STATUSES
            if not old_files and not needs_meta:
                continue
            warnings.warn(f'{folder.name} 旧结构迁移：原件保留；已有 reading/analysis 不覆盖。', UserWarning)
            changed = []
            if needs_meta:
                run_dir = self.p / '.runs' / (self.ops.now().replace(':', '').replace('.', '-') + '-migration-' + folder.name)
                run_dir.mkdir(parents=True, exist_ok=False)
                (run_dir / 'meta.before.yaml').write_bytes(meta_path.read_bytes())
                new = dict(defaults, **meta)
                new['status'] = OLD_STATUSES.get(meta.get('status'), meta.get('status', 'unread'))
                for k in ['created_at', 'updated_at', 'year']:
                    if new[k] is None:
                        new[k] = TODO
                self.ops.save(meta_path, new)
                changed.append('meta.yaml')
                self.ops.save(run_dir / 'run.yaml', dict(self.ops.provenance(), status='migration',
                    source_refs=[str(meta_path.relative_to(self.p))], changed_files=changed,
                    note='元数据补字段及旧状态映射；旧副本在 meta.before.yaml'))
            if not (folder / 'reading.md').exists():
                info, body = markdown(paper_template / 'reading.md')
                body = body.replace('论文精读：TODO(user)', '论文精读：' + folder.name)
                mapping = {'overview.md':1, 'close-reading.md':3, 'context.md':6, 'note.md':10}
                for name, section in mapping.items():
                    if (folder / name).exists():
                        heading = f'## {section}. {READING_HEADINGS[section-1]}'
                        legacy_text = (folder / name).read_text(encoding='utf-8-sig')
                        body = body.replace(heading, heading + '\n\n### 旧内容（保留原文，待整理）\n\n' + legacy_text)
                info.update(self.ops.provenance('literature-reader'), prompt_version='v2')
                info.pop('status', None)
                write_markdown(folder / 'reading.md', info, body)
            if not (folder / 'analysis.yaml').exists():
                analysis = self.ops.load(paper_template / 'analysis.yaml')
                analysis['paper'] = folder.name
                for name, target in [('extraction.yaml','extraction'), ('formulas.yaml','formulas'), ('concepts.yaml','concepts')]:
                    if not (folder / name).exists():
                        continue
                    old = yaml.safe_load((folder / name).read_text(encoding='utf-8-sig'))
                    if target == 'extraction' and isinstance(old, dict):
                        for k in analysis['extraction']:
                            if k in old:
                                value = old[k]
                                analysis['extraction'][k] = {'legacy_items': value} if k == 'method' and isinstance(value,list) else value
                        leftovers = {k:v for k,v in old.items() if k not in analysis['extraction'] and k not in self.ops.PROVENANCE}
                        if leftovers: analysis['legacy_extraction'] = leftovers
                        analysis['source_refs'] = old.get('source_refs', [])
                    elif isinstance(old, list) or isinstance(old, dict) and isinstance(old.get(target), list):
                        analysis[target] = old if isinstance(old, list) else old[target]
                    else:
                        analysis['legacy_' + target] = old
                analysis.update(self.ops.provenance('literature-reader'), paper=folder.name, prompt_version='v2',
                                source_refs=analysis['source_refs'])
                analysis.pop('status', None)
                self.ops.save(folder / 'analysis.yaml', analysis)
            if not (folder / 'translation.md').exists():
                (folder / 'translation.md').write_bytes((paper_template / 'translation.md').read_bytes())
                self.ops.stamp_markdown(folder / 'translation.md', 'literature-reader')
        for name in ['collections', 'catalog', 'synthesis']:
            if (self.base / name).exists():
                warnings.warn(f'保留旧 {name}/；请按 workflow/literature.md 迁移说明人工整理，工具不删除。', UserWarning)

    def new_concept(self, concept_id):
        self.ops.slug(concept_id)
        target = self.ops.contained(self.base / 'concepts', concept_id + '.md')
        if target.exists():
            raise ValueError('概念已存在，不覆盖')
        target.parent.mkdir(exist_ok=True)
        info, body = markdown(self.root / 'workflow/templates/concept.md')
        info.update(self.ops.provenance('knowledge-builder'), concept_id=concept_id, status='not-started', prompt_version='v2')
        body = body.replace('概念：TODO(user)', '概念：' + concept_id)
        write_markdown(target, info, body)
        return target

    def paper_rows(self, records):
        lines = ['| 论文 | 年份 | 类型 | 优先级 | 状态 |', '|---|---|---|---|---|']
        for key, row in records:
            lines.append(f'| [{cell(key)}](10_literature/papers/{key}/) | {cell(row.get("year"))} | {cell(row.get("paper_role"))} | {cell(row.get("reading_priority"))} | {cell(row.get("status"))} |')
        return lines if len(lines)>2 else ['TODO(user)：暂无条目。']

    def index(self):
        self.migrate()
        papers = self.papers()
        data, profile = self.ops.load(self.p / 'project.yaml'), self.ops.load(self.p / 'research-profile.yaml')
        lines = ['# 项目索引', '', '> 扫描生成，请勿手工维护分类。', '', '## 项目概览', '',
                 f'项目：{data["title"]}；阶段：{data["stage"]}', f'方向：{profile["direction"]}',
                 f'当前 claim：{data.get("current_claim")}；下一步：{data.get("next_action")}', '',
                 '- [阅读清单](10_literature/reading-list.md)', '- [对比矩阵](10_literature/matrix.md)',
                 '- [知识网络](10_literature/knowledge-map.md)', '', '## 全部论文', '']
        lines += self.paper_rows(papers.items())
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
        paths = ['project.yaml','research-profile.yaml'] + [f'10_literature/papers/{key}/meta.yaml' for key in papers] + claim_paths
        info, body = self.generated('\n'.join(lines)+'\n',paths)
        write_markdown(self.p / 'INDEX.md', info, body)
        self.reading_list(papers)
        self.knowledge_map(papers)

    def reading_list(self, papers):
        path = self.base / 'reading-list.md'
        info, body = markdown(path)
        notes, topics, order = info.get('reading_notes',{}), info.get('topic_paths',{}), info.get('reading_order',[])
        if not isinstance(notes,dict) or not isinstance(topics,dict) or not isinstance(order,list):
            raise ValueError('阅读清单 reading_notes/topic_paths/reading_order 类型错误')
        self.check_reading_list(papers)
        def table(keys):
            rows = ['| citekey | 年份 | 类型 | 为什么读 | 优先级 | 当前状态 |', '|---|---|---|---|---|---|']
            for key in keys:
                row=papers[key]
                reason=notes.get(key,TODO)
                if isinstance(reason,dict): reason=reason.get('why_read',TODO)
                rows += [f'| [{key}](papers/{key}/) | {cell(row.get("year"))} | {cell(row.get("paper_role"))} | {cell(reason)} | {cell(row.get("reading_priority"))} | {cell(row["status"])} |']
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
                    source_refs=[f'10_literature/papers/{k}/meta.yaml' for k in papers])
        write_markdown(path,info,body)

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
        keys.update(re.findall(r'\bcitekey:\s*([a-z0-9-]+)',body))
        if any(not isinstance(k,str) for k in keys) or keys-set(papers):
            raise ValueError('阅读清单引用不存在的 citekey：'+', '.join(map(str,keys-set(papers))))

    def knowledge_map(self, papers):
        cards=self.concepts()
        paper_concepts={k:set(v.get('concept_ids',[])) for k,v in papers.items()}
        sources=[f'10_literature/papers/{k}/meta.yaml' for k in papers]
        for key in papers:
            file=self.base/'papers'/key/'analysis.yaml'
            if file.exists():
                data=self.ops.load(file)
                paper_concepts[key].update(x['id'] for x in data.get('concepts',[]) if isinstance(x,dict) and 'id' in x)
                sources.append(file.relative_to(self.p).as_posix())
        counts=Counter(c for refs in paper_concepts.values() for c in refs)
        for concept_id,card in cards.items():
            for paper in set(card.get('papers',[])):
                if paper in paper_concepts and concept_id not in paper_concepts[paper]: counts[concept_id]+=1
        nodes=set(cards)|set(counts)
        missing=set(nodes)-set(cards)
        adjacency={n:set() for n in nodes}
        prereqs={n:set() for n in nodes}
        for n,card in cards.items():
            prereqs[n]=set(card.get('prerequisites',[]))
            for other in card.get('prerequisites',[])+card.get('related',[])+card.get('contrasts',[]):
                if other not in nodes: missing.add(other); continue
                adjacency[n].add(other);adjacency[other].add(n)
        lines=['# 知识网络','', '> 根据本地论文引用与概念卡声明关系生成；频次按不同论文数计，聚类不表示语义推断。','', '## 高频概念排名','']
        ranking=sorted(nodes,key=lambda n:(-counts[n],n))
        for n in ranking: lines += [f'- [{n}](concepts/{n}.md)：{counts[n]} 篇论文；状态 {cards.get(n,{}).get("status",TODO)}']
        if not ranking:lines += [TODO]
        lines += ['', '## 高频但尚未理解的概念','']
        unlearned=[n for n in ranking if counts[n]>0 and cards.get(n,{}).get('status')!='understood']
        lines += [f'- {n}：{counts[n]} 篇论文' for n in unlearned] or [TODO]
        lines += ['', '## 概念前置关系','']
        relations=[f'- {parent} → {child}' for child in sorted(prereqs) for parent in sorted(prereqs[child])]
        lines += relations or [TODO]
        lines += ['', '## 概念聚类','']
        remaining=set(nodes);clusters=[]
        while remaining:
            first=min(remaining); group=set(); stack=[first]
            while stack:
                n=stack.pop()
                if n in group:continue
                group.add(n);stack.extend(adjacency[n]-group)
            remaining-=group;clusters.append(sorted(group))
        lines += [f'- 连通组 {i}：'+', '.join(group) for i,group in enumerate(clusters,1)] or [TODO]
        lines += ['', '## 新概念/旧概念分布','']
        types=Counter(c.get('type',TODO) for c in cards.values())
        for label in ['foundational','classic','current','emerging']:lines += [f'- {label}：{types[label]}']
        lines += ['说明：依据概念卡 type 分类，不以年份自动推断新旧。','', '## 推荐学习顺序','']
        pending=set(cards);ordered=[]
        while pending:
            ready=sorted([n for n in pending if prereqs[n].issubset(set(ordered))],key=lambda n:(-counts[n],n))
            if not ready:break
            ordered.extend(ready);pending-=set(ready)
        lines += [f'{i}. [{n}](concepts/{n}.md)' for i,n in enumerate(ordered,1)] or [TODO]
        if pending:lines += ['无法排序（循环或缺失前置卡）：'+', '.join(sorted(pending))]
        lines += ['', '## 孤立概念','']
        lines += [f'- {n}' for n in sorted(nodes) if not adjacency[n]] or [TODO]
        lines += ['', '## 当前知识网络缺口','']
        gaps=[f'- 缺少概念卡：{n}' for n in sorted(missing)]
        gaps += [f'- 尚未理解：{n}' for n in sorted(cards) if cards[n].get('status')!='understood']
        if pending:gaps += ['- 前置图存在阻断；需核对循环和未定义关系。']
        lines += gaps or [TODO]
        sources += [f'10_literature/concepts/{n}.md' for n in cards]
        info,body=self.generated('\n'.join(lines)+'\n',sources)
        write_markdown(self.base/'knowledge-map.md',info,body)

    def validate(self):
        papers=self.papers();cards=self.concepts()
        legacy_project=any((self.base/name).exists() for name in ['catalog','collections','synthesis'])
        for name in ['README.md','concepts','reading-list.md','knowledge-map.md']:
            if not (self.base/name).exists():
                if legacy_project or any((self.base/'papers'/k/'note.md').exists() for k in papers):
                    warnings.warn(f'旧项目缺少 {name}；运行 index 合并新骨架，保留原件。',UserWarning)
                else:raise ValueError(f'文献模块缺少 {name}')
        for key,meta in papers.items():
            folder=self.base/'papers'/key
            old=[f for f in LEGACY if (folder/f).exists()]
            for name in old:warnings.warn(f'迁移提示：{key}/{name} 原件保留，映射见文献说明。',UserWarning)
            if meta.get('citekey')!=key:raise ValueError('citekey 与目录不一致')
            if old and any(not (folder/f).exists() for f in ['reading.md','analysis.yaml']):
                warnings.warn(f'{key} 尚未迁移；运行 index 安全合并。',UserWarning)
                self.ops.refs(self.p,meta)
                continue
            self.ops.contract(self.root,'paper',meta)
            for name in ['meta.yaml','translation.md','reading.md','analysis.yaml','source']:
                if not (folder/name).exists():raise ValueError(f'{key} 缺少 {name}')
            if isinstance(meta['year'],str) and meta['year']!=TODO:raise ValueError('year 只能是整数或 TODO(user)')
            self.ops.refs(self.p,meta)
            for ref in meta['source_files']:
                if not self.ops.contained(self.p,ref).is_file():raise ValueError('source_files 文件不存在')
            analysis=self.ops.load(folder/'analysis.yaml')
            self.ops.contract(self.root,'analysis',analysis)
            if analysis['paper']!=key:raise ValueError('analysis.paper 与目录不一致')
            self.ops.refs(self.p,analysis)
            ids=[f['id'] for f in analysis['formulas']]
            if len(ids)!=len(set(ids)):raise ValueError('公式 ID 重复')
            if any(i not in ids for i in meta['formula_ids']):raise ValueError('meta.formula_ids 未在 analysis 中定义')
            for f in analysis['formulas']:
                self.ops.slug(f['id'])
                if isinstance(f['confidence'],str) and f['confidence']!=TODO:raise ValueError('公式 confidence 不合法')
                for cid in f['related_concepts']:
                    if cid not in cards:raise ValueError('公式关联概念卡不存在')
            ids=[c['id'] for c in analysis['concepts']]
            if len(ids)!=len(set(ids)):raise ValueError('论文概念 ID 重复')
            for cid in set(ids+meta['concept_ids']):
                self.ops.slug(cid)
                if cid not in cards:raise ValueError(f'概念卡不存在：{cid}')
            for name in ['translation.md','reading.md']:
                info,body=markdown(folder/name)
                self.ops.refs(self.p,info)
                self.check_concept_links(body,folder,cards)
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
            if card['concept_id']!=cid:raise ValueError('概念 ID 与文件名不一致')
            self.ops.refs(self.p,card)
            for field in ['prerequisites','related','contrasts']:
                for linked in card[field]:
                    if linked not in cards:raise ValueError(f'概念 {cid} 引用缺失卡：{linked}')
            for key in card['papers']:
                if key not in papers:raise ValueError('概念引用论文不存在')
            if meaningful(card['first_defined_in']) and card['first_defined_in'] not in papers:
                raise ValueError('first_defined_in 需指向本地 citekey 或 TODO(user)')
            self.check_concept_links(markdown(self.base/'concepts'/(cid+'.md'))[1],self.base/'concepts',cards)
        if (self.base/'reading-list.md').exists():self.check_reading_list(papers)
        for name in ['catalog','collections','synthesis']:
            if (self.base/name).exists():warnings.warn(f'旧 {name}/ 保留，需人工迁移。',UserWarning)

    def check_concept_links(self,body,folder,cards):
        for link in re.findall(r'\]\(([^)]+)\)',body):
            clean=unquote(link.split('#',1)[0])
            if 'concepts/' not in clean:continue
            target=self.ops.contained(self.p,(folder/clean).resolve())
            if not target.is_file() or target.stem not in cards or target.parent!=self.base/'concepts':
                raise ValueError('Markdown 概念链接不存在或位置错误')
