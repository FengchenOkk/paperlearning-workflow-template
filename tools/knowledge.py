"""确定性、可解释的本地知识图谱；相似性始终是待核验候选。"""
from collections import Counter, defaultdict, deque
from itertools import combinations
import hashlib
import json
import math
import re
try:
    from . import literature, storage, registry
except ImportError:
    import literature, storage, registry


def tokens(text):
    if not literature.meaningful(text):
        return set()
    text = str(text).lower()
    result = set(re.findall(r'[a-z0-9]+', text))
    for chunk in re.findall(r'[\u4e00-\u9fff]+', text):
        result.update(chunk[i:i+2] for i in range(max(1,len(chunk)-1)))
    return result


def jaccard(a,b):
    return len(a & b)/len(a | b) if a | b else 0.0


def groups(edges, kind):
    neighbors = defaultdict(set)
    for edge in edges:
        if edge['type'] != kind:
            continue
        a,b = edge['source'],edge['target']
        neighbors[a].add(b); neighbors[b].add(a)
    result = []
    pending = set(neighbors)
    while pending:
        stack = [min(pending)]; component = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node); stack.extend(neighbors[node]-component)
        pending -= component
        result.append({'id': f'{kind}:{len(result)+1}', 'type': kind, 'nodes': sorted(component)})
    return result


def _legacy_candidates(library, papers=None, index=None):
    papers = library.papers() if papers is None else papers
    cards = library.concepts()
    # 新对象只写 links 时，旧相似算法也通过索引获得概念/原理集合。
    if index:
        paper_keys={_canonical(index,meta.get('id','paper:'+key)):key for key,meta in papers.items()}
        card_keys={_canonical(index,card.get('id','concept:'+key)):key for key,card in cards.items()}
        for link in index.get('links',[]):
            source,target=(_canonical(index,link.get(field)) for field in ['source','target'])
            if source in paper_keys and target in card_keys and link.get('rel') in ['introduces','uses','contrasts','extends']:
                values=papers[paper_keys[source]].setdefault('concept_ids',[])
                if card_keys[target] not in values:values.append(card_keys[target])
            if source in paper_keys and isinstance(target,str) and target.startswith('principle:') and link.get('rel')=='uses':
                values=papers[paper_keys[source]].setdefault('first_principle_ids',[])
                value=target.split(':',1)[-1]
                if value not in values:values.append(value)
            if source in card_keys and target in card_keys and link.get('rel')=='prerequisite':
                values=cards[card_keys[source]].setdefault('prerequisites',[])
                if card_keys[target] not in values:values.append(card_keys[target])
    nodes, edges, sources = {}, {}, set()
    paper_concepts = {key:set(meta.get('concept_ids',[])) for key,meta in papers.items()}
    principles = defaultdict(set)
    reviews = {}
    missing, errors = set(), []

    def node(identifier, kind, label, **data):
        nodes.setdefault(identifier,dict(id=identifier,type=kind,label=label,**data))

    def evidence(file, field, refs=None):
        sources.add(file)
        return dict(file=file,field=field,source_refs=refs or [])

    def add(a,b,kind,weight=1.0,proof=None,candidate=False,confidence='medium'):
        if a == b:
            return
        key = (a,b,kind)
        edge = edges.setdefault(key,dict(source=a,target=b,type=kind,weight=round(weight,6),
                    confidence=confidence,evidence=[],status='candidate' if candidate else 'auto'))
        for item in proof or []:
            if item not in edge['evidence']:
                edge['evidence'].append(item)

    for cid,card in cards.items():
        file = (library.concept_path(cid).relative_to(library.p).as_posix() if hasattr(library,'concept_path')
                else f'10_literature/concepts/{cid}.md')
        sources.add(file)
        node('concept:'+cid,'concept',cid,status=card.get('status',literature.TODO),concept_type=card.get('type'))
        if card.get('is_first_principle'):
            node('principle:'+cid,'principle',cid)
            add('principle:'+cid,'concept:'+cid,'uses',proof=[evidence(file,'is_first_principle')])
        for key in card.get('papers',[]):
            if key in paper_concepts:
                paper_concepts[key].add(cid)
        for field,kind in [('prerequisites','prerequisite'),('related','related'),('contrasts','contrasts'),
                           ('extends','extends'),('replaces','replaces')]:
            for other in card.get(field,[]):
                if other not in cards:
                    missing.add(other)
                    continue
                a,b = ('concept:'+other,'concept:'+cid) if field=='prerequisites' else ('concept:'+cid,'concept:'+other)
                add(a,b,kind,proof=[evidence(file,field)])

    for key,meta in papers.items():
        pid = 'paper:'+key
        folder = library.paper_folder(key) if hasattr(library,'paper_folder') else library.base/'papers'/key
        file = (folder/'meta.yaml').relative_to(library.p).as_posix()
        node(pid,'paper',key,title=meta.get('title'),paper_role=meta.get('paper_role'),status=meta.get('status'),
             reading_status=meta.get('reading_status'),analysis_status=meta.get('analysis_status'))
        sources.add(file)
        for topic in sorted(set(meta.get('categories',[])+meta.get('topic_tags',[]))):
            node('topic:'+topic,'topic',topic)
            add(pid,'topic:'+topic,'belongs-to-topic',proof=[evidence(file,'categories/topic_tags')])
        for name in ['translation.md','reading.md']:
            text_file = literature.paper_path(folder,name)
            if text_file.is_file():
                sources.add(text_file.relative_to(library.p).as_posix())
        path = literature.paper_path(folder,'analysis.yaml')
        if path.is_file():
            rel = path.relative_to(library.p).as_posix(); sources.add(rel)
            try:
                library.ops.contained(library.p,path)
                analysis = library.ops.load(path)
                if not isinstance(analysis.get('concepts',[]),list) or not isinstance(analysis.get('first_principles',[]),list):
                    raise ValueError('分析字段需要列表')
                for index,item in enumerate(analysis.get('concepts',[])):
                    if not isinstance(item,dict) or not isinstance(item.get('id'),str):
                        raise ValueError('概念条目损坏')
                    cid = item['id']; paper_concepts[key].add(cid)
                    if cid not in cards:
                        missing.add(cid); node('concept:'+cid,'concept',cid,missing=True)
                    kind = {'introduced':'introduces','used':'uses','compared':'contrasts','extended':'extends'}.get(item.get('role'),'uses')
                    add(pid,'concept:'+cid,kind,proof=[evidence(rel,f'concepts[{index}]',item.get('source_refs',[]))])
                for index,item in enumerate(analysis.get('first_principles',[])):
                    if not isinstance(item,dict) or not isinstance(item.get('id'),str):
                        raise ValueError('第一性原理条目损坏')
                    principle = item['id']; principles[key].add(principle)
                    node('principle:'+principle,'principle',principle)
                    add(pid,'principle:'+principle,'uses',proof=[evidence(rel,f'first_principles[{index}]',item.get('source_refs',[]))])
                    for cid in item.get('concept_ids',[principle]):
                        if cid not in cards:
                            missing.add(cid); node('concept:'+cid,'concept',cid,missing=True)
                        add('principle:'+principle,'concept:'+cid,'uses',proof=[evidence(rel,f'first_principles[{index}].concept_ids')])
                if meta.get('paper_role')=='survey':
                    review = analysis.get('review_similarity',{})
                    if not isinstance(review,dict):
                        raise ValueError('review_similarity 需要对象')
                    reviews[key] = (tokens(review.get('core_problem')),tokens(review.get('method_summary')),
                                    set(review.get('key_concepts',[])),rel)
            except (ValueError,TypeError,KeyError,OSError):
                errors.append(f'分析损坏：{key}；跳过无法解析的关联，修复后重新生成。')
        # meta 和概念卡的声明也计入频次，不重复计同一论文。
        for cid in sorted(paper_concepts[key]):
            if cid not in cards:
                missing.add(cid); node('concept:'+cid,'concept',cid,missing=True)
            if not any((pid,'concept:'+cid,kind) in edges for kind in ['introduces','uses','contrasts','extends']):
                proof = [evidence(file,'concept_ids')]
                if index:
                    linked=[item for link in index.get('links',[]) if _canonical(index,link.get('source'))==_canonical(index,pid)
                            and _canonical(index,link.get('target'))==_canonical(index,'concept:'+cid)
                            for item in link.get('evidence',[]) if isinstance(item,dict)]
                    if linked:proof=linked
                if cid in cards and key in cards[cid].get('papers',[]):
                    card_file=(library.concept_path(cid).relative_to(library.p).as_posix() if hasattr(library,'concept_path')
                               else f'10_literature/concepts/{cid}.md')
                    proof.append(evidence(card_file,'papers'))
                add(pid,'concept:'+cid,'uses',proof=proof)
        for principle in meta.get('first_principle_ids',[]):
            principles[key].add(principle); node('principle:'+principle,'principle',principle)
            proof=[evidence(file,'first_principle_ids')]
            if index:
                linked=[item for link in index.get('links',[]) if _canonical(index,link.get('source'))==_canonical(index,pid)
                        and _canonical(index,link.get('target'))==_canonical(index,'principle:'+principle)
                        for item in link.get('evidence',[]) if isinstance(item,dict)]
                if linked:proof=linked
            add(pid,'principle:'+principle,'uses',proof=proof)

    counts = Counter(cid for cids in paper_concepts.values() for cid in cids)
    idf = {cid:1+math.log((1+len(papers))/(1+count)) for cid,count in counts.items()}
    for a,b in combinations(sorted(papers),2):
        ca,cb = paper_concepts[a],paper_concepts[b]
        common = ca & cb
        if common:
            union = ca | cb
            ordinary = jaccard(ca,cb)
            weighted = sum(idf[c] for c in common)/sum(idf[c] for c in union)
            proof = [dict(item,shared_concepts=sorted(common),jaccard=round(ordinary,6),idf_jaccard=round(weighted,6))
                     for edge in list(edges.values()) if edge['source'] in ['paper:'+a,'paper:'+b] and edge['target'] in {'concept:'+c for c in common}
                     for item in edge['evidence']]
            add('paper:'+a,'paper:'+b,'similar-concept-set',(ordinary+weighted)/2,proof,candidate=True)
        shared = principles[a] & principles[b]
        if shared:
            add('paper:'+a,'paper:'+b,'similar-first-principle',1.0,
                [dict(item,shared_principles=sorted(shared)) for edge in list(edges.values())
                 if edge['source'] in ['paper:'+a,'paper:'+b] and edge['target'] in {'principle:'+p for p in shared}
                 for item in edge['evidence']],candidate=True)
        if a in reviews and b in reviews:
            ra,rb = reviews[a],reviews[b]
            scores = [jaccard(ra[i],rb[i]) for i in range(3)]
            score = sum(scores)/3
            if score >= .25:
                add('paper:'+a,'paper:'+b,'similar-review',score,
                    [dict(file=reviews[key][3],field='review_similarity',source_refs=[],
                          component_scores=[round(x,6) for x in scores]) for key in [a,b]],candidate=True)
    # 概念共现只报告候选，不静默建立同义/合并关系。
    cooccurrence = defaultdict(list)
    for key,cids in paper_concepts.items():
        for pair in combinations(sorted(cids),2):
            cooccurrence[pair].append(key)
    for (a,b),keys in sorted(cooccurrence.items()):
        add('concept:'+a,'concept:'+b,'co-occurs',len(keys)/max(1,len(papers)),
            [item for edge in list(edges.values()) if edge['source'] in {'paper:'+key for key in keys}
             and edge['target'] in ['concept:'+a,'concept:'+b] for item in edge['evidence']],candidate=True)

    prerequisites = {cid:set(card.get('prerequisites',[])) for cid,card in cards.items()}
    pending, order = set(cards), []
    while pending:
        ready = sorted((cid for cid in pending if prerequisites[cid].issubset(order)),key=lambda cid:(-counts[cid],cid))
        if not ready:
            break
        order.extend(ready); pending -= set(ready)
    for name in ['reading-list.md','matrix.md']:
        if (library.base/name).is_file():
            sources.add(f'10_literature/{name}')
    graph = dict(schema_version=1,generated_by='wf',generated_at=library.ops.now(),generated_from=sorted(sources),
                 nodes=[nodes[key] for key in sorted(nodes)],edges=[edges[key] for key in sorted(edges)],
                 clusters=groups(edges.values(),'similar-first-principle')+groups(edges.values(),'similar-review'),
                 learning_path=['concept:'+cid for cid in order],concept_frequency=dict(sorted(counts.items())),
                 missing_concepts=sorted(missing),blocked_learning=sorted(pending),scan_issues=library.scan_issues+errors,
                 algorithm={'concept_similarity':'mean(Jaccard, IDF-weighted Jaccard); IDF=1+ln((1+N)/(1+df))',
                            'review_similarity':'mean(Jaccard(problem tokens), Jaccard(method tokens), Jaccard(key concepts)); threshold=0.25',
                            'first_principle':'shared stable id; candidate weight=1; id equality does not prove scientific equivalence'})
    # 只保留输入未变化、证据未变化的人工核验；输入变化降回 candidate。
    receipts = {}
    for rel in sorted(sources):
        path = library.p/rel
        try:
            library.ops.contained(library.p,path)
        except ValueError:
            graph['scan_issues'].append('来源越过项目边界：'+rel+'；未读取。')
            continue
        if not path.is_file():
            continue
        content = path.read_bytes()
        if path.suffix in ['.yaml','.yml']:
            try:
                data = dict(library.ops.load(path))
                data.pop('updated_at',None)
                data.pop('link_audit',None)
                if isinstance(data.get('links'),list):
                    data['links'] = [link for link in data['links'] if isinstance(link,dict) and
                                     link.get('generated_by') not in ['wf-knowledge','wf-registry']]
                content = json.dumps(data,ensure_ascii=False,sort_keys=True).encode('utf-8')
            except (ValueError,OSError,TypeError):
                pass
        if path.suffix=='.md':
            try:
                info,body = literature.markdown(path)
                if path.name=='reading-list.md':
                    manual = {k:info.get(k) for k in ['reading_notes','topic_paths','reading_order']}
                    body = re.sub(r'<!-- wf:reading-list:begin -->.*?<!-- wf:reading-list:end -->','',body,flags=re.S)
                else:
                    manual = {k:v for k,v in info.items() if k not in ['created_at','updated_at','generated_at','generated_by','generated_from','model_role','prompt_version','schema_version','link_audit']}
                    if isinstance(manual.get('links'),list):
                        manual['links'] = [link for link in manual['links'] if isinstance(link,dict) and
                                           link.get('generated_by') not in ['wf-knowledge','wf-registry']]
                content = (body+json.dumps(manual,sort_keys=True,ensure_ascii=False)).encode('utf-8')
            except (ValueError,OSError,TypeError):
                graph['scan_issues'].append('Markdown 格式损坏：'+rel+'；保留原件，请人工修复。')
        receipts[rel] = hashlib.sha256(content).hexdigest()
    graph['input_hashes'] = receipts
    old_path = library.base/'knowledge-graph.json'
    if old_path.is_file():
        try:
            old = json.loads(old_path.read_text(encoding='utf-8-sig'))
            if not isinstance(old,dict) or not isinstance(old.get('edges',[]),list):
                raise ValueError('旧图谱格式损坏')
            audited = {(e['source'],e['target'],e['type']):e for e in old.get('edges',[])
                       if isinstance(e,dict) and (e.get('status')=='verified' or e.get('review_invalidated'))}
            for edge in graph['edges']:
                prior = audited.get((edge['source'],edge['target'],edge['type']))
                if not prior:
                    continue
                valid=old.get('input_hashes')==receipts and prior.get('evidence')==edge['evidence'] and prior.get('weight')==edge['weight'] and prior.get('status')=='verified'
                if valid:
                    edge['status']='verified'
                else:
                    edge['review_invalidated']=True
                for field in ['reviewed_by','reviewed_at','review_note']:
                    if field in prior:
                        edge[field]=prior[field]
        except (ValueError,KeyError,TypeError):
            graph['scan_issues'].append('旧图谱损坏，已按本地数据重建；人工核验需重新确认。')
    return graph


def _canonical(index, identifier):
    """只通过机器索引解析 ID/旧别名，不依赖当前位置。"""
    if not isinstance(identifier,str):return None
    aliases = index.get('aliases',{})
    seen = set()
    while identifier in aliases and identifier not in seen:
        seen.add(identifier); identifier = aliases[identifier]
    return identifier


def _graph_evidence(library,index,proof):
    """ID ArtifactRef 与历史路径证据统一解析为可定位的图谱证据。"""
    original=proof
    if isinstance(proof,str):
        identifier=_canonical(index,proof)
        if identifier in index.get('artifacts',{}):proof={'id':identifier}
        else:
            file,mark,anchor=proof.partition('#')
            proof={'file':file,'field':anchor if mark else 'source'}
    if not isinstance(proof,dict):raise ValueError('证据必须为 ArtifactRef 或旧路径')
    if isinstance(proof.get('artifact_ref'),dict):proof=dict(proof['artifact_ref'],**{k:v for k,v in proof.items() if k!='artifact_ref'})
    if proof.get('id'):
        ref=registry.resolve(library.p,proof,library.ops,index=index)
        value=dict(proof,file=ref['path'],field=proof.get('field') or ref.get('anchor') or 'source')
        value['source_ref']=original
    else:
        file=proof.get('file') or proof.get('path')
        if not isinstance(file,str) or not file:raise ValueError('证据缺少 ID 或路径')
        rel,mark,anchor=file.partition('#')
        target=literature.resolve_path(library.p,rel,library.ops)
        if not target.is_file():raise ValueError('证据文件不存在')
        value=dict(proof,file=target.relative_to(library.p).as_posix(),field=proof.get('field') or proof.get('anchor') or (anchor if mark else 'source'))
        if isinstance(original,str) or value['file']!=rel:value['source_ref']=original
    if not isinstance(value['field'],str) or not value['field']:raise ValueError('证据定位不合法')
    return value


def _scientific_hash(file,ops):
    """核验依赖正文与对象属性，排除连接/生成时间以避免自引用哈希。"""
    def clean(data):
        if isinstance(data,dict):
            return {k:clean(v) for k,v in data.items() if k not in
                    ['links','principle_links','link_audit','updated_at','generated_at','synced_at','id_aliases']}
        if isinstance(data,list):return [clean(item) for item in data]
        return data
    if file.suffix=='.md':
        info,body=literature.markdown(file)
        value=json.dumps(clean(info),ensure_ascii=False,sort_keys=True)+'\n'+body
    elif file.suffix in ['.yaml','.yml']:
        value=json.dumps(clean(ops.load(file)),ensure_ascii=False,sort_keys=True)
    else:return hashlib.sha256(file.read_bytes()).hexdigest()
    return hashlib.sha256(value.encode()).hexdigest()


def _expire_source_reviews(library,index):
    """正式源链接的证据变化会使核验失效；历史意见保存在源 audit。"""
    files=sorted({record['path'] for record in index.get('artifacts',{}).values()})
    hashes={}
    changed=False
    def digest(rel):
        if rel not in hashes:
            file=literature.resolve_path(library.p,rel.split('#',1)[0],library.ops)
            hashes[rel]=_scientific_hash(file,library.ops) if file.is_file() else 'missing'
        return hashes[rel]
    for rel in files:
        file=library.ops.contained(library.p,rel)
        if file.suffix not in ['.md','.yaml','.yml'] or not file.is_file():continue
        try:
            info,body=literature.markdown(file) if file.suffix=='.md' else (library.ops.load(file),None)
            before=json.dumps(info,ensure_ascii=False,sort_keys=True)
            def visit(data):
                if isinstance(data,list):
                    for item in data:visit(item)
                elif isinstance(data,dict):
                    for key,value in data.items():
                        if key in ['links','principle_links'] and isinstance(value,list):
                            for link in value:
                                if not isinstance(link,dict) or link.get('status')!='verified' or link.get('generated_by')=='wf-knowledge':continue
                                dependencies={_canonical(index,rel):digest(rel)}
                                target=index['artifacts'].get(_canonical(index,link.get('target')))
                                if target:dependencies[_canonical(index,target['path'])]=digest(target['path'])
                                for proof in link.get('evidence',[]) if isinstance(link.get('evidence',[]),list) else []:
                                    try:
                                        located=_graph_evidence(library,index,proof)
                                        dependencies[_canonical(index,located['file'])]=digest(located['file'])
                                    except (ValueError,OSError,TypeError,KeyError):
                                        dependencies['invalid-evidence']='invalid'
                                fingerprint=hashlib.sha256(json.dumps(dependencies,sort_keys=True).encode()).hexdigest()
                                previous=link.get('review_evidence_hash')
                                if previous and previous!=fingerprint:
                                    receipt={k:link[k] for k in ['reviewed_by','reviewed_at','review_note'] if k in link}
                                    receipt.update(decision='expired',evidence_hash=previous)
                                    link.setdefault('audit',[])
                                    if receipt not in link['audit']:link['audit'].append(receipt)
                                    link.update(status='candidate',review_invalidated=True)
                                else:link['review_evidence_hash']=fingerprint
                                if library.dry_run:
                                    for indexed in index.get('links',[]):
                                        if indexed.get('origin')==rel and indexed.get('rel')==link.get('rel') and indexed.get('target')==link.get('target'):
                                            indexed.update(link)
                        elif key not in ['link_audit','audit']:visit(value)
            visit(info)
            if before!=json.dumps(info,ensure_ascii=False,sort_keys=True) and not library.dry_run:
                if body is None:library.ops.save(file,info)
                else:literature.write_markdown(file,info,body)
                changed=True
        except (ValueError,OSError,TypeError):
            continue
    return changed


def _persist_candidates(library,index,legacy):
    """相似算法的结果写入源 links；图谱不再是关系或核验的源。"""
    receipts={_canonical(index,rel):value for rel,value in legacy['input_hashes'].items()}
    inputs = hashlib.sha256(json.dumps(receipts,sort_keys=True).encode()).hexdigest()
    def comparable(proofs):
        def ref(value):
            if not isinstance(value,str):return value
            path,mark,anchor=value.partition('#')
            return _canonical(index,path)+(mark+anchor if mark else '')
        result=[]
        for proof in proofs:
            item=dict(proof)
            if isinstance(item.get('file'),str):item['file']=ref(item['file'])
            if isinstance(item.get('source_refs'),list):item['source_refs']=[ref(value) for value in item['source_refs']]
            result.append(item)
        return result
    candidates = defaultdict(list)
    for edge in legacy['edges']:
        if not (edge['type'].startswith('similar-') or edge['type']=='co-occurs'):
            continue
        source,target = (_canonical(index,edge[key]) for key in ['source','target'])
        if source not in index['artifacts'] or target not in index['artifacts'] or not edge.get('evidence'):
            continue
        candidates[source].append(dict(rel=edge['type'],target=target,evidence=edge['evidence'],
            confidence=edge['confidence'],weight=edge['weight'],status='candidate',
            generated_by='wf-knowledge',input_hash=inputs))
    old_graph = {}
    path = library.base/'knowledge-graph.json'
    if path.is_file():
        try:
            old_graph = json.loads(path.read_text(encoding='utf-8-sig'))
        except (ValueError,OSError):
            pass
    old_reviews = {( _canonical(index,e.get('source')), _canonical(index,e.get('target')), e.get('type')):e
                   for e in old_graph.get('edges',[]) if isinstance(e,dict) and e.get('status')=='verified'
                   and e.get('reviewed_by') in ['human','main','verifier']}
    migrated = False
    changed = False
    for source,record in sorted(index['artifacts'].items()):
        if source not in candidates and record.get('type') not in ['paper','concept']:
            continue
        file = library.ops.contained(library.p,record['path'])
        if not file.is_file() or file.suffix not in ['.yaml','.yml','.md']:
            continue
        try:
            info,body = literature.markdown(file) if file.suffix=='.md' else (library.ops.load(file),None)
            if not isinstance(info.get('links',[]),list):
                legacy['scan_issues'].append('源 links 损坏，未覆盖：'+record['path']); continue
            previous = info.get('links',[])
            untouched = [link for link in previous if not isinstance(link,dict) or link.get('generated_by')!='wf-knowledge']
            old = {(link.get('rel'),_canonical(index,link.get('target'))):link for link in previous if isinstance(link,dict)}
            output = list(untouched)
            keys = set()
            for link in candidates.get(source,[]):
                key = (link['rel'],link['target']); keys.add(key)
                prior = old.get(key)
                # 手工源关系优先；自动候选不能取代人工关系。
                if prior and prior.get('generated_by')!='wf-knowledge':
                    continue
                if prior:
                    for name in ['reviewed_by','reviewed_at','review_note','review_input_hash','review_invalidated','legacy_graph_review_imported','audit']:
                        if name in prior: link[name] = prior[name]
                    if prior.get('status')=='verified':
                        if prior.get('input_hash')==inputs and comparable(prior.get('evidence',[]))==comparable(link['evidence']):
                            link['status']='verified'
                        else:
                            link['review_invalidated']=True
                            link.setdefault('audit',[])
                            receipt = {k:prior[k] for k in ['reviewed_by','reviewed_at','review_note'] if k in prior}
                            receipt.update(decision='expired',input_hash=prior.get('input_hash'))
                            if receipt not in link['audit']:link['audit'].append(receipt)
                # 兼容上一版人工直接写 graph 的核验：每条关系只迁一次，迁后只认源 links。
                review = old_reviews.get((source,link['target'],link['rel']))
                if (review and not link.get('legacy_graph_review_imported') and
                    old_graph.get('input_hashes')==legacy['input_hashes'] and
                    review.get('evidence')==link['evidence'] and review.get('weight')==link['weight']):
                    link.update(status='verified',legacy_graph_review_imported=True,review_input_hash=inputs)
                    for name in ['reviewed_by','reviewed_at','review_note']:
                        if name in review:link[name]=review[name]
                    migrated = True
                output.append(link)
            removed = [link for key,link in old.items() if link.get('generated_by')=='wf-knowledge' and key not in keys]
            audits = list(info.get('link_audit',[]))
            for link in removed:
                if link.get('reviewed_by') or link.get('audit'):
                    receipt = dict(link,review_invalidated=True,status='candidate',reason='关联依据已变化；从活动 links 移除')
                    if receipt not in audits:audits.append(receipt)
            output.sort(key=lambda link:(str(link.get('rel')),str(link.get('target')),str(link.get('generated_by'))) if isinstance(link,dict) else ('','',''))
            updated = dict(info,links=output)
            if audits:updated['link_audit']=audits
            if updated!=info and not library.dry_run:
                if body is None:library.ops.save(file,updated)
                else:literature.write_markdown(file,updated,body)
                changed=True
            # dry-run 在内存索引中展示新候选，但绝不写文件。
            if library.dry_run:
                index['links'] = [link for link in index.get('links',[]) if not
                                 (link.get('source')==source and link.get('generated_by')=='wf-knowledge')]
                index['links'].extend(dict(link,source=source) for link in output if isinstance(link,dict) and link.get('generated_by')=='wf-knowledge')
        except (ValueError,OSError,TypeError,KeyError):
            legacy['scan_issues'].append('关系源无法解析，保留原文件：'+record['path'])
    if migrated or any(link.get('legacy_graph_review_imported') for link in index.get('links',[])):
        legacy['scan_issues'].append('旧图谱核验已一次性迁入源 links；后续只审核源 links。')
    return changed


def build(library,papers=None):
    """INDEX.json 是节点解析中心，源文件 links 是关系的单一事实源。"""
    index = registry.build(library.root,library.p,library.ops,dry_run=library.dry_run,write=not library.dry_run)
    changed=_expire_source_reviews(library,index)
    if changed and not library.dry_run:index=registry.build(library.root,library.p,library.ops)
    legacy = _legacy_candidates(library,None,index)
    changed=_persist_candidates(library,index,legacy)
    if changed and not library.dry_run:
        index = registry.build(library.root,library.p,library.ops)
    artifacts = index.get('artifacts',{})
    supported = {'paper','concept','principle','formula','claim','topic','task','attempt','artifact'}
    legacy_nodes = {_canonical(index,n['id']):n for n in legacy['nodes']}
    nodes = {}
    for identifier,record in sorted(artifacts.items()):
        kind = record.get('type')
        if kind not in supported:continue
        data = dict(legacy_nodes.get(identifier,{}))
        data.update(id=identifier,type=kind,label=data.get('label',identifier.split(':',1)[-1]),
                    path=record['path'],
                    artifact_ref={'id':identifier,'type':kind,'path':record['path'],'hash':record.get('hash'),'anchor':record.get('anchor')})
        nodes[identifier] = data
    edges = {}
    issues = list(legacy['scan_issues'])+list(index.get('issues',[]))
    for link in index.get('links',[]):
        if not isinstance(link,dict):issues.append('INDEX.links 非对象，已跳过。'); continue
        source,target = (_canonical(index,link.get(key)) for key in ['source','target'])
        if source not in artifacts or target not in artifacts:
            issues.append(f'悬空 link：{source} → {target}；未加入图谱。'); continue
        proof = link.get('evidence',[])
        if not isinstance(proof,list) or not proof:
            issues.append(f'无证据 link：{source} → {target}；未加入图谱。'); continue
        try:
            proof=[_graph_evidence(library,index,item) for item in proof]
        except (ValueError,OSError,TypeError,KeyError):
            issues.append(f'证据定位无效：{source} → {target}；未加入图谱。');continue
        kind = link.get('rel')
        if not isinstance(kind,str):issues.append('link.rel 无效；已跳过。'); continue
        confidence = link.get('confidence','low'); status = link.get('status','candidate')
        if confidence not in ['low','medium','high'] or status not in ['candidate','verified','auto']:
            issues.append(f'link 状态/置信度无效：{source} → {target}；未加入图谱。'); continue
        if kind.startswith('similar-') and status=='auto':status='candidate'
        weight = link.get('weight',1.0)
        if isinstance(weight,bool) or not isinstance(weight,(int,float)) or not math.isfinite(weight) or not 0<=weight<=1:
            issues.append(f'link 权重无效：{source} → {target}；未加入图谱。'); continue
        for identifier in [source,target]:
            if identifier not in nodes:
                record = artifacts[identifier]
                nodes[identifier] = dict(id=identifier,type='artifact',artifact_type=record.get('type'),
                    label=identifier.split(':',1)[-1],artifact_ref={'id':identifier,'path':record['path'],'hash':record.get('hash')})
        if source==target:continue
        edge = dict(source=source,target=target,type=kind,evidence=proof,confidence=confidence,status=status,weight=round(weight,6))
        for field in ['reviewed_by','reviewed_at','review_note','review_invalidated','audit','generated_by','input_hash','legacy_graph_review_imported']:
            if field in link:edge[field]=link[field]
        edges[(source,target,kind)] = edge
    legacy.update(nodes=[nodes[key] for key in sorted(nodes)],edges=[edges[key] for key in sorted(edges)],
        clusters=groups(edges.values(),'similar-first-principle')+groups(edges.values(),'similar-review'),
        learning_path=[_canonical(index,key) for key in legacy['learning_path'] if _canonical(index,key) in nodes],
        scan_issues=sorted(set(issues)),connection_model='source-links-v1',index_ref='INDEX.json',
        generated_from=sorted(set(legacy['generated_from']+['INDEX.json'])))
    old_path = library.base/'knowledge-graph.json'
    if old_path.is_file():
        try:
            old = json.loads(old_path.read_text(encoding='utf-8-sig'))
            comparable = {k:v for k,v in legacy.items() if k!='generated_at'}
            if comparable=={k:v for k,v in old.items() if k!='generated_at'}:
                legacy['generated_at']=old['generated_at']
        except (ValueError,OSError,KeyError):pass
    return legacy


def bridge_scores(graph):
    """无向论文候选网络的 Brandes 中介中心性；只是导航指标。"""
    adjacency = {n['id']:set() for n in graph['nodes'] if n['type']=='paper'}
    for e in graph['edges']:
        if e['type'].startswith('similar-') and e['source'] in adjacency and e['target'] in adjacency:
            adjacency[e['source']].add(e['target']); adjacency[e['target']].add(e['source'])
    scores = dict.fromkeys(adjacency,0.0)
    for start in sorted(adjacency):
        stack, queue = [], deque([start])
        parents = {n:[] for n in adjacency}; count = dict.fromkeys(adjacency,0.0); count[start] = 1
        distance = dict.fromkeys(adjacency,-1); distance[start] = 0
        while queue:
            v = queue.popleft(); stack.append(v)
            for w in sorted(adjacency[v]):
                if distance[w]<0:
                    queue.append(w); distance[w] = distance[v]+1
                if distance[w]==distance[v]+1:
                    count[w] += count[v]; parents[w].append(v)
        dependency = dict.fromkeys(adjacency,0.0)
        while stack:
            w = stack.pop()
            for v in parents[w]:
                dependency[v] += count[v]/count[w]*(1+dependency[w])
            if w!=start:
                scores[w] += dependency[w]/2
    return scores


def render(graph):
    cards = {n['label']:n for n in graph['nodes'] if n['type']=='concept'}
    counts = graph['concept_frequency']
    lines = ['## 高频概念','']
    for cid in sorted(cards,key=lambda c:(-counts.get(c,0),c)):
        link=cards[cid].get('path',f'10_literature/concepts/{cid}.md').removeprefix('10_literature/')
        lines.append(f'- [{cid}]({link})：{counts.get(cid,0)} 篇论文；状态 {cards[cid].get("status",literature.TODO)}')
    lines += ['','## 高频但尚未理解的概念','']
    lines += [f'- {cid}' for cid in sorted(cards) if counts.get(cid,0)>0 and cards[cid].get('status')!='understood'] or [literature.TODO]
    for heading,kind in [('第一性原理网络','similar-first-principle'),('相似综述聚类','similar-review')]:
        lines += ['',f'## {heading}','']
        lines += ['- '+', '.join(c['nodes'])+'（候选）' for c in graph['clusters'] if c['type']==kind] or [literature.TODO]
    lines += ['','## 概念前置关系','']
    lines += [f'- {e["source"]} → {e["target"]}' for e in graph['edges'] if e['type']=='prerequisite'] or [literature.TODO]
    lines += ['','## 概念聚类','', '仅展示声明关系及候选相似，不自动合并概念。', '', '## 新概念/旧概念分布','']
    types = Counter(n.get('concept_type') for n in cards.values())
    lines += [f'- {kind}：{types[kind]}' for kind in ['foundational','classic','current','emerging']]
    lines += ['','## 核心桥梁论文','', '按候选网络中介中心性排序；不表示论文质量或已核验影响。']
    scores = bridge_scores(graph)
    lines += [f'- {key}：{score:.3f}' for key,score in sorted(scores.items(),key=lambda item:(-item[1],item[0])) if score>0] or [literature.TODO]
    lines += ['','## 推荐学习顺序','']
    node_paths={node['id']:node.get('path',f'10_literature/concepts/{node["id"].split(":",1)[1]}.md').removeprefix('10_literature/') for node in graph['nodes']}
    lines += [f'{i}. [{key.split(":",1)[1]}]({node_paths[key]})' for i,key in enumerate(graph['learning_path'],1)] or [literature.TODO]
    if graph['blocked_learning']:
        lines += ['无法排序（循环或缺失前置卡）：'+', '.join(graph['blocked_learning'])]
    lines += ['','## 待验证关联','']
    lines += [f'- {e["source"]} ↔ {e["target"]}：{e["type"]}，权重 {e["weight"]}，置信度 {e["confidence"]}；证据见 knowledge-graph.json'
              for e in graph['edges'] if e['status']=='candidate'] or [literature.TODO]
    lines += ['','## 知识缺口','', '## 当前知识网络缺口','']
    lines += [f'- 缺少概念卡：{cid}' for cid in graph['missing_concepts']]
    lines += [f'- 尚未理解：{cid}' for cid,n in sorted(cards.items()) if n.get('status')!='understood']
    lines += [f'- 尚未完成精读/分析：{n["label"]}' for n in graph['nodes'] if n['type']=='paper' and
              (n.get('reading_status')!='complete' or n.get('analysis_status')!='complete')]
    lines += ['- '+issue for issue in graph['scan_issues']]
    if graph['blocked_learning']:
        lines += ['- 前置图存在阻断；需核对循环和未定义关系。']
    lines += ['','## 孤立概念与孤立论文','', '## 孤立概念','']
    degrees = Counter(n for edge in graph['edges'] for n in [edge['source'],edge['target']])
    lines += ['- '+n['id'] for n in graph['nodes'] if n['type'] in ['concept','paper'] and not degrees[n['id']]] or [literature.TODO]
    return '\n'.join(lines)+'\n'


def generate(library,papers=None):
    graph = build(library,papers)
    path = library.base/'knowledge-graph.json'
    library.ops.contained(library.p,path)
    if library.dry_run:
        print(f'预览图谱：{len(graph["nodes"])} 个节点、{len(graph["edges"])} 条边；未写文件。')
    else:
        storage.write_text(path,json.dumps(graph,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+'\n')
    map_path = library.base/'knowledge-map.md'
    info,body = literature.markdown(map_path) if map_path.exists() else ({},'# 知识网络\n\n<!-- GENERATED:BEGIN -->\n<!-- GENERATED:END -->\n')
    start,end = '<!-- GENERATED:BEGIN -->','<!-- GENERATED:END -->'
    block = start+'\n'+render(graph)+end
    if start not in body or end not in body:
        # 兼容原来整文件生成的图；无生成元数据的手工正文始终保留。
        if info.get('generated_by')=='wf':
            body = '# 知识网络\n\n'+block+'\n'
        else:
            body += '\n\n'+block+'\n'
    else:
        body = re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda _:block,body,count=1,flags=re.S)
    generated,_ = library.generated('',graph['generated_from'])
    generated['generated_at']=graph['generated_at']
    if info.get('created_at'):generated['created_at']=info['created_at']
    info.update(generated)
    library.write(map_path,info,body)
    return graph


def validate(library):
    path = library.base/'knowledge-graph.json'
    if not path.exists():
        raise ValueError('缺少 knowledge-graph.json；请运行 graph 或 index')
    try:
        graph = json.loads(path.read_text(encoding='utf-8-sig'))
    except ValueError:
        raise ValueError('knowledge-graph.json JSON 损坏') from None
    if not isinstance(graph,dict) or graph.get('schema_version')!=1 or any(k not in graph for k in ['generated_by','generated_at','generated_from','nodes','edges','clusters','learning_path']):
        raise ValueError('图谱缺少 schema 版本或生成来源')
    if any(not isinstance(graph[k],list) for k in ['generated_from','nodes','edges','clusters','learning_path']):
        raise ValueError('图谱节点、边、来源、学习顺序必须为列表')
    if any(not isinstance(n,dict) or not isinstance(n.get('id'),str) or n.get('type') not in ['paper','concept','principle','topic','formula','claim','task','attempt','artifact'] for n in graph['nodes']):
        raise ValueError('图谱节点格式不合法')
    ids = [n['id'] for n in graph['nodes']]
    if len(ids)!=len(set(ids)):
        raise ValueError('图谱节点 ID 重复')
    index = registry.load_index(library.p)
    if any(identifier not in index.get('artifacts',{}) for identifier in ids):
        raise ValueError('图谱节点无法通过 INDEX.json 解析；请重新运行 index')
    for edge in graph['edges']:
        if not isinstance(edge,dict) or any(k not in edge for k in ['source','target','type','weight','confidence','evidence','status']):
            raise ValueError('图谱边缺少证据或置信度')
        if edge['source'] not in ids or edge['target'] not in ids:
            raise ValueError('图谱边引用不存在的节点')
        if not isinstance(edge['weight'],(int,float)) or isinstance(edge['weight'],bool) or not math.isfinite(edge['weight']) or not 0<=edge['weight']<=1:
            raise ValueError('图谱边权重不合法')
        if edge['confidence'] not in ['low','medium','high'] or edge['status'] not in ['auto','candidate','verified'] or not isinstance(edge['evidence'],list) or not edge['evidence'] or not isinstance(edge['type'],str):
            raise ValueError('图谱边证据、置信度或状态不合法')
        if edge['type'].startswith('similar-') and edge['status']=='auto':
            raise ValueError('相似关系只能为 candidate 或人工 verified')
        for proof in edge['evidence']:
            if not isinstance(proof,dict) or not proof.get('field') or not proof.get('file'):
                raise ValueError('图谱证据需要文件和字段定位')
            if not literature.resolve_path(library.p,proof['file'].split('#',1)[0],library.ops).is_file():
                raise ValueError('图谱证据来源文件不存在')
    library.ops.refs(library.p,{'source_refs':graph['generated_from']})
