"""Zotero 只读获取与增量入库；不发送写请求，不调用模型。"""
import copy
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import quote, urlparse, urlencode, unquote
try:
    from . import adapters, literature, storage, registry
except ImportError:
    import adapters, literature, storage, registry


class Unavailable(ValueError):
    pass


def config(root,ops):
    example = root/'config/zotero.example.yaml'
    path = root/'config/zotero.local.yaml'
    result = copy.deepcopy(ops.load(example)['zotero'])
    if path.is_file():
        local = ops.load(path).get('zotero',{})
        if not isinstance(local,dict):
            raise ValueError('zotero 配置必须为对象')
        try:
            ops.reject_credentials(local)
        except ValueError:
            raise ValueError('Zotero 配置不得保存密钥；请使用 api_key_env 和本地 .env') from None
        for key,value in local.items():
            if isinstance(value,dict) and isinstance(result.get(key),dict):
                result[key].update(value)
            else:
                result[key] = value
    if result.get('mode') not in ['local','web','export'] or not isinstance(result.get('enabled'),bool) or any(not isinstance(result.get(k),dict) for k in ['local','web','export','sync']):
        raise ValueError('Zotero enabled/mode 不合法')
    if result['export'].get('format') not in ['better-bibtex-json','csl-json']:
        raise ValueError('Zotero export.format 必须为 better-bibtex-json 或 csl-json')
    sync = result['sync']
    if sync.get('direction')!='read_only' or sync.get('attachment_mode') not in ['link','copy']:
        raise ValueError('Zotero 只支持 read_only 与 link/copy 附件模式')
    for field in ['create_missing_papers','update_metadata','preserve_manual']:
        if not isinstance(sync.get(field),bool):
            raise ValueError('Zotero sync 开关必须为布尔值')
    for field in ['use_index_json','preserve_aliases','link_collections_to_topics','link_tags_to_topics','update_hash','dry_run_default']:
        sync.setdefault(field,True)
        if not isinstance(sync[field],bool):
            raise ValueError('Zotero sync 连接开关必须为布尔值')
    return result


def project_options(project,ops):
    options = dict(collections=[],category_map={},tag_filter=[],ignore_tags=[])
    overrides = ops.load(project/'project.yaml').get('zotero',{})
    if not isinstance(overrides,dict):
        raise ValueError('项目 Zotero 配置必须为对象')
    options.update(overrides)
    for field in ['collections','tag_filter','ignore_tags']:
        if not isinstance(options[field],list) or any(not isinstance(x,str) for x in options[field]):
            raise ValueError('项目 Zotero 筛选字段必须为字符串列表')
    if not isinstance(options['category_map'],dict) or any(not isinstance(k,str) or not isinstance(v,(str,list)) or isinstance(v,list) and any(not isinstance(x,str) for x in v) for k,v in options['category_map'].items()):
        raise ValueError('category_map 必须为 collection → 分类字符串/列表')
    return options


def normalize_doi(value):
    value = str(value or '').strip().lower()
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)','',value)


def normalize_title(value):
    return re.sub(r'[^\w]+','',str(value or '').casefold())


def parse(payload,mode='export',format='better-bibtex-json',library_type='user',library_id='0'):
    """API 包装对象、Better BibTeX JSON、CSL-JSON → 通用条目。"""
    raw_items = payload.get('items',[]) if isinstance(payload,dict) else payload
    if not isinstance(raw_items,list):
        raise ValueError('Zotero 数据需要 items 列表或 JSON 列表')
    collection_members = defaultdict(list)
    collection_names = {}
    if isinstance(payload,dict):
        raw_collections = payload.get('collections',{})
        values = raw_collections.values() if isinstance(raw_collections,dict) else raw_collections if isinstance(raw_collections,list) else []
        for entry in values:
            if not isinstance(entry,dict):
                continue
            key = str(entry.get('key',entry.get('id','')))
            collection_names[key] = str(entry.get('name',key))
            for item in entry.get('items',[]) if isinstance(entry.get('items',[]),list) else []:
                collection_members[str(item)].append(key)
    records,errors,attachments = [],[],defaultdict(list)
    for index,wrapped in enumerate(raw_items):
        try:
            if not isinstance(wrapped,dict):
                raise ValueError('条目不是对象')
            item = wrapped.get('data',wrapped)
            if not isinstance(item,dict):
                raise ValueError('data 不是对象')
            item_type = item.get('itemType',item.get('type',''))
            key = str(wrapped.get('key') or item.get('itemKey') or item.get('key') or item.get('id') or '')
            if item_type in ['attachment','note','annotation']:
                if item_type=='attachment' and item.get('parentItem'):
                    attachment = item.get('path') or item.get('url') or item.get('filename')
                    if attachment:
                        attachments[str(item['parentItem'])].append(str(attachment))
                continue
            title = item.get('title')
            if not isinstance(title,str) or not title.strip():
                raise ValueError('缺少标题')
            for field in ['tags','collections','attachments']:
                if field in item and not isinstance(item[field],list):
                    raise ValueError('条目列表格式错误')
            citekey = item.get('citationKey') or item.get('citation-key') or item.get('citekey')
            if not citekey:
                extra = str(item.get('extra',''))
                match = re.search(r'(?im)^\s*(?:citation\s*key|citekey)\s*:\s*(\S+)',extra)
                citekey = match.group(1) if match else None
            if not citekey and format=='csl-json':
                citekey = item.get('id')
            issued = item.get('issued',{})
            parts = issued.get('date-parts',[]) if isinstance(issued,dict) else []
            date = str(item.get('date',''))
            year_match = re.search(r'\b(1[0-9]{3}|2[0-9]{3})\b',date)
            year = int(parts[0][0]) if parts and parts[0] else int(year_match.group(0)) if year_match else literature.TODO
            if not key:
                fingerprint = normalize_doi(item.get('DOI')) or normalize_title(title)+str(year)
                key = 'EXPORT'+hashlib.sha256(fingerprint.encode()).hexdigest()[:10].upper()
            authors = []
            for person in item.get('creators',item.get('author',[])):
                if not isinstance(person,dict):
                    raise ValueError('作者条目损坏')
                if person.get('creatorType','author') not in ['author','inventor']:
                    continue
                name = person.get('name') or person.get('literal') or ' '.join(str(person.get(k,'')) for k in ['firstName','lastName']).strip() or ' '.join(str(person.get(k,'')) for k in ['given','family']).strip()
                if name:
                    authors.append(name)
            tags = [tag.get('tag') if isinstance(tag,dict) else tag for tag in item.get('tags',[])]
            if any(not isinstance(tag,str) for tag in tags):
                raise ValueError('tag 格式错误')
            collections = [entry.get('key') if isinstance(entry,dict) else entry for entry in item.get('collections',[])]
            collections += collection_members.get(str(item.get('itemID',key)),[])
            collections += collection_members.get(key,[])
            paths = []
            for attachment in item.get('attachments',[]):
                if isinstance(attachment,str):
                    paths.append(attachment)
                elif isinstance(attachment,dict):
                    path = attachment.get('path') or attachment.get('localPath') or attachment.get('url')
                    if path:
                        paths.append(str(path))
            records.append(dict(citekey=str(citekey or 'zotero-'+key),title=title.strip(),authors=authors,year=year,
                venue=item.get('publicationTitle') or item.get('container-title') or literature.TODO,
                doi=normalize_doi(item.get('DOI',item.get('doi'))) or literature.TODO,
                url=item.get('url',item.get('URL')) or literature.TODO,language=item.get('language') or literature.TODO,
                item_key=key,collection_keys=sorted(set(str(c) for c in collections if c)),tags=sorted(set(tags)),
                attachment_paths=sorted(set(paths)),version=wrapped.get('version',item.get('version',literature.TODO)),
                library_type=library_type,library_id=str(library_id),collection_names=collection_names,
                synthetic_item_key=key.startswith('EXPORT')))
        except (ValueError,TypeError,KeyError,IndexError):
            errors.append(f'跳过第 {index+1} 个损坏条目（不显示原始内容）。')
    for row in records:
        row['attachment_paths'] = sorted(set(row['attachment_paths']+attachments[row['item_key']]))
    return records,errors


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        raise Unavailable('Zotero 重定向已拒绝；工作流仍可使用手动入库或离线导出。')


def get_json(url,timeout,key=None):
    headers = {'Accept':'application/json','Zotero-API-Version':'3'}
    if key:
        headers['Zotero-API-Key'] = key
    request = urllib.request.Request(url,headers=headers,method='GET')
    # 本地 Zotero 不经过系统代理；Web Key 永不跟随重定向。
    handlers = [NoRedirect()]
    if urlparse(url).hostname in ['localhost','127.0.0.1','::1']:
        handlers.append(urllib.request.ProxyHandler({}))
    try:
        with urllib.request.build_opener(*handlers).open(request,timeout=timeout) as response:
            payload = response.read(32_000_001)
        if len(payload)>32_000_000:
            raise Unavailable('Zotero 单页响应过大，请缩小资料范围或使用离线导出。')
        return json.loads(payload.decode('utf-8-sig'))
    except (OSError,ValueError) as error:
        raise Unavailable('Zotero 不可用（'+type(error).__name__+'）；检查启动、权限或 Key，或改用 export；原始错误已隐藏。') from None


def local_attachment_path(url,timeout):
    request=urllib.request.Request(url,headers={'Accept':'text/plain','Zotero-API-Version':'3'},method='GET')
    try:
        with urllib.request.build_opener(NoRedirect(),urllib.request.ProxyHandler({})).open(request,timeout=timeout) as response:
            text=response.read(10001).decode('utf-8').strip()
        parsed=urlparse(text)
        if len(text)>10000 or parsed.scheme!='file' or parsed.hostname not in [None,'','localhost']:
            raise ValueError('需要本机 file URL')
        return urllib.request.url2pathname(unquote(parsed.path))
    except (ValueError,OSError):
        raise Unavailable('本地附件路径暂不可用；保留 Zotero 打开链接，不下载 PDF。') from None


def fetch(root,cfg,ops):
    if not cfg['enabled']:
        raise Unavailable('Zotero 未启用；手动入库、模型任务与本地图谱可继续使用。')
    mode = cfg['mode']
    if mode=='export':
        path = cfg['export'].get('path')
        if not literature.meaningful(path):
            raise Unavailable('请填写 Zotero export.path；不影响手动工作流。')
        path = Path(path)
        if not path.is_absolute():
            path = root/path
        try:
            payload = json.loads(path.read_text(encoding='utf-8-sig'))
            return parse(payload,format=cfg['export']['format'],library_type='export',library_id='offline')
        except (ValueError,OSError):
            raise Unavailable('Zotero 导出文件不存在或 JSON 损坏；不影响手动工作流。') from None
    connection = cfg[mode]
    key = None
    if mode=='local':
        base = connection['base_url'].rstrip('/')
        url = urlparse(base)
        if url.scheme!='http' or url.hostname not in ['localhost','127.0.0.1','::1'] or url.username or url.password or url.query or url.fragment or not re.fullmatch(r'/api/(users|groups)/\d+',url.path):
            raise ValueError('本地 Zotero 地址必须为无凭据的 loopback /api/users|groups/<id>')
        library_type = 'group' if '/groups/' in url.path else 'user'
        library_id = url.path.rsplit('/',1)[1]
    else:
        library_type,library_id = connection['library_type'],str(connection['library_id'])
        if library_type not in ['user','group'] or not library_id.isdigit():
            raise ValueError('Web 模式需要 user/group 和数字 library_id')
        variable = connection.get('api_key_env')
        if not isinstance(variable,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',variable):
            raise ValueError('Web 模式需要合法 api_key_env')
        key = adapters.key_value(dict(api_key_env=variable,_env_file=str(root/'.env')))
        if not key:
            raise Unavailable('缺少 Zotero Web Key；可使用本地 API、export 或手动入库。')
        base = f'https://api.zotero.org/{library_type}s/{library_id}'
    timeout = connection.get('timeout_seconds',10)
    if not isinstance(timeout,(int,float)) or isinstance(timeout,bool) or not 0<timeout<=300:
        raise ValueError('Zotero timeout_seconds 必须为 0..300 的正数')
    def pages(endpoint):
        result = []
        for start in range(0,1_000_000,100):
            rows = get_json(base+'/'+endpoint+'?'+urlencode({'format':'json','limit':100,'start':start}),timeout,key)
            if not isinstance(rows,list):
                raise Unavailable('Zotero API 未返回 JSON 列表；请检查端点。')
            result.extend(rows)
            if len(rows)<100:
                return result
        raise Unavailable('Zotero 条目超过同步上限，请按集合导出。')
    raw = pages('items')
    attachment_errors=[]
    for wrapped in raw:
        if not isinstance(wrapped,dict):
            continue
        item=wrapped.get('data',wrapped)
        if not isinstance(item,dict) or item.get('itemType')!='attachment' or not item.get('parentItem'):
            continue
        attachment_key=str(wrapped.get('key',item.get('key','')))
        if not attachment_key:
            continue
        if mode=='local' and (not item.get('path') or str(item['path']).startswith('storage:')) and item.get('linkMode')!='linked_url':
            try:
                item['path']=local_attachment_path(base+'/items/'+quote(attachment_key,safe='')+'/file/view/url',timeout)
            except Unavailable:
                item['path']='zotero://open-pdf/'+('groups/'+library_id if library_type=='group' else 'library')+'/items/'+quote(attachment_key,safe='')
                attachment_errors.append('本地附件路径不可用，已保留 Zotero 打开链接。')
        elif mode=='web' and not item.get('path') and not item.get('url'):
            item['path']='zotero://open-pdf/'+('groups/'+library_id if library_type=='group' else 'library')+'/items/'+quote(attachment_key,safe='')
    collections = pages('collections')
    names = {}
    for wrapped in collections:
        if isinstance(wrapped,dict):
            item = wrapped.get('data',wrapped)
            if isinstance(item,dict):
                names[str(wrapped.get('key',item.get('key','')))] = str(item.get('name',''))
    records,errors = parse(raw,mode=mode,library_type=library_type,library_id=library_id)
    errors.extend(attachment_errors)
    for row in records:
        row['collection_names'] = names
    return records,errors


def status(root,project,ops,doctor=False):
    try:
        cfg = config(root,ops)
        records,errors = fetch(root,cfg,ops)
        if project:
            options = project_options(project,ops)
            records = filter_records(records,options)
        print(f'Zotero 就绪：mode={cfg["mode"]}；只读；{len(records)} 个条目；损坏 {len(errors)} 个。')
        return {'available':True,'count':len(records),'errors':errors}
    except (ValueError,OSError) as error:
        # 配置错误均为本模块固定消息；不输出库内容、HTTP 错误或密钥。
        print('Zotero 状态：'+str(error)+'；基础工作流仍可用。')
        return {'available':False,'count':0,'errors':['Zotero 未就绪']}


def filter_records(records,options):
    result = []
    for row in records:
        if options['collections'] and not set(options['collections']) & set(row['collection_keys']):
            continue
        if options['tag_filter'] and not set(options['tag_filter']).issubset(row['tags']):
            continue
        if set(options['ignore_tags']) & set(row['tags']):
            continue
        result.append(row)
    return result


def _topic(kind,row,value):
    """集合使用不可变 item key；标签用文本指纹，避免中文/空格碰撞。"""
    scope = re.sub(r'[^A-Za-z0-9_-]','-',f'{row["library_type"]}-{row["library_id"]}')
    if kind=='collection':
        safe = re.sub(r'[^A-Za-z0-9_-]','-',str(value))
        if not safe:safe=hashlib.sha256(str(value).encode()).hexdigest()[:12]
        elif safe!=str(value):safe+='-'+hashlib.sha256(str(value).encode()).hexdigest()[:8]
        return f'topic:zotero-{scope}-collection-{safe}'
    label = re.sub(r'[^\w-]+','-',str(value).casefold(),flags=re.UNICODE).strip('-')[:48] or 'tag'
    return f'topic:zotero-{scope}-tag-{label}-{hashlib.sha256(str(value).encode()).hexdigest()[:8]}'


def _identity_links(meta,row,citekey,cfg,meta_path=None):
    meta.setdefault('id','paper:'+citekey)
    meta.setdefault('type','paper')
    meta['zotero_key']=row['item_key']
    if cfg['sync']['preserve_aliases']:
        aliases = list(meta.get('aliases',[]))
        for alias in [f'zotero:{row["item_key"]}',f'zotero:{row["library_type"]}:{row["library_id"]}:{row["item_key"]}',
                      'citekey:'+row['citekey'],'paper:'+row['citekey'],'citekey:'+meta.get('citekey',citekey)]:
            if alias!=meta['id'] and alias not in aliases:aliases.append(alias)
        meta['aliases']=sorted(aliases)
    file = meta_path or f'10_literature/papers/{citekey}/meta.yaml'
    topics = []
    if cfg['sync']['link_collections_to_topics']:
        topics.extend((_topic('collection',row,key),'zotero.collection_keys',key) for key in row['collection_keys'])
    if cfg['sync']['link_tags_to_topics']:
        topics.extend((_topic('tag',row,tag),'zotero.tags',tag) for tag in row['tags'])
    old = meta.get('links',[])
    if not isinstance(old,list):raise ValueError('meta.links 必须为列表')
    links = [link for link in old if not isinstance(link,dict) or link.get('generated_by')!='wf-zotero']
    previous = {(link.get('rel'),link.get('target')):link for link in old if isinstance(link,dict)}
    for target,field,value in topics:
        prior = previous.get(('belongs-to-topic',target))
        if prior and prior.get('generated_by')!='wf-zotero':continue
        link = dict(rel='belongs-to-topic',target=target,
                    evidence=[dict(file=file,field=field,source_refs=[],zotero_value=value)],
                    confidence='high',weight=1.0,status='candidate',generated_by='wf-zotero')
        if prior:
            for name in ['status','reviewed_by','reviewed_at','review_note','audit']:
                if name in prior:link[name]=prior[name]
        links.append(link)
    meta['links']=sorted(links,key=lambda link:(str(link.get('rel')),str(link.get('target')),str(link.get('generated_by'))) if isinstance(link,dict) else ('','',''))
    incoming = {target for target,_,_ in topics}
    old_owned = {link.get('target') for link in old if isinstance(link,dict) and link.get('generated_by')=='wf-zotero'}
    meta['topic_ids']=sorted((set(meta.get('topic_ids',[]))-old_owned)|incoming)


def sync(root,project,ops,dry_run=False):
    # Python 旧 API 默认仍执行；CLI 传 None 应用新的配置默认预览。
    report = dict(schema_version=1,generated_by='wf',generated_at=ops.now(),generated_from=['project.yaml'],
                  mode=None,dry_run=dry_run,created=[],updated=[],unchanged=[],duplicates=[],errors=[],missing_attachments=[])
    try:
        cfg = config(root,ops); options = project_options(project,ops)
        if dry_run is None:dry_run=cfg['sync']['dry_run_default']
        report['dry_run']=dry_run
        records,errors = fetch(root,cfg,ops)
    except (ValueError,OSError) as error:
        print('Zotero 同步未执行：'+str(error)+'；可继续手动入库。')
        report['errors'].append('Zotero 未就绪；无文件变更')
        return report
    report['mode'] = cfg['mode']; report['errors'].extend(errors)
    records = filter_records(records,options)
    library = literature.Library(root,project,ops,dry_run)
    existing = library.papers()
    def paper_folder(citekey):
        if citekey in existing and hasattr(library,'paper_folder'):
            return library.paper_folder(citekey)
        return project/'10_literature/papers'/citekey
    machine_index = None
    if cfg['sync']['use_index_json']:
        # 构建时仅解析；同步错误或预览不能对源文件产生副作用。
        try:
            machine_index = registry.build(root,project,ops,dry_run=True,write=False)
            report['generated_from'].append('INDEX.json')
        except (ValueError,OSError):
            report['errors'].append('机器索引无法解析；保留原件，使用既有 DOI/item key 只读匹配。')
    for issue in library.scan_issues:
        report['errors'].append(issue)
    incoming_dois = defaultdict(list)
    incoming_keys = defaultdict(list)
    for row in records:
        incoming_keys[(row['library_type'],row['library_id'],row['item_key'])].append(row['citekey'])
        if literature.meaningful(row['doi']):
            incoming_dois[normalize_doi(row['doi'])].append(row['item_key'])
    by_doi,by_key,by_title = defaultdict(list),defaultdict(list),defaultdict(list)
    def register(citekey,meta):
        if literature.meaningful(meta.get('doi')):
            by_doi[normalize_doi(meta['doi'])].append(citekey)
        z = meta.get('zotero',{})
        if isinstance(z,dict) and literature.meaningful(z.get('item_key')):
            by_key[(z.get('library_type'),str(z.get('library_id')),z['item_key'])].append(citekey)
        if literature.meaningful(meta.get('title')):
            by_title[(normalize_title(meta['title']),str(meta.get('year')))].append(citekey)
    for citekey,meta in existing.items():
        register(citekey,meta)
    for row in sorted(records,key=lambda r:(r['citekey'],r['item_key'])):
        try:
            if len(incoming_keys[(row['library_type'],row['library_id'],row['item_key'])])>1:
                report['duplicates'].append({'item_key':row['item_key'],'reason':'同一 Zotero item key 重复；请先核对'})
                continue
            if len(incoming_dois.get(normalize_doi(row['doi']),[]))>1:
                report['duplicates'].append({'item_key':row['item_key'],'reason':'导出/API 中 DOI 重复；请先核对'})
                continue
            key_match = by_key.get((row['library_type'],row['library_id'],row['item_key']),[])
            doi_match = by_doi.get(normalize_doi(row['doi']),[]) if literature.meaningful(row['doi']) else []
            alias_match = []
            if machine_index:
                aliases = machine_index.get('aliases',{})
                scoped = f'zotero:{row["library_type"]}:{row["library_id"]}:{row["item_key"]}'
                identifier = aliases.get(scoped) or aliases.get(f'zotero:{row["item_key"]}')
                if identifier:
                    try:
                        ref = registry.resolve(project,identifier,ops,verify_hash=False,index=machine_index)
                        keys=[key for key,meta in existing.items() if meta.get('id','paper:'+key)==ref['id']]
                        if keys:alias_match.extend(keys)
                    except (ValueError,OSError,KeyError):
                        report['errors'].append('Zotero 旧别名解析失败；本条继续核对 DOI/item key。')
            matches = alias_match or key_match or doi_match
            if alias_match and any(set(match)!=set(alias_match) for match in [key_match,doi_match] if match):
                report['duplicates'].append({'item_key':row['item_key'],'reason':'INDEX 别名与 DOI/item key 冲突','candidates':sorted(set(alias_match+key_match+doi_match))})
                continue
            if len(set(matches))>1 or doi_match and key_match and set(doi_match)!=set(key_match):
                report['duplicates'].append({'item_key':row['item_key'],'reason':'DOI/item key 指向多个论文','candidates':sorted(set(doi_match+key_match))})
                continue
            if matches:
                citekey = matches[0]; meta = existing[citekey]
                binding = meta.get('zotero',{})
                if literature.meaningful(binding.get('item_key')) and (binding.get('item_key')!=row['item_key'] or binding.get('library_type')!=row['library_type'] or str(binding.get('library_id'))!=row['library_id']):
                    report['duplicates'].append({'item_key':row['item_key'],'reason':'同 DOI 已绑定另一 Zotero 条目','candidates':[citekey]})
                    continue
            else:
                weak = by_title.get((normalize_title(row['title']),str(row['year'])),[])
                if weak:
                    report['duplicates'].append({'item_key':row['item_key'],'reason':'标题+年份疑似重复；不自动合并','candidates':sorted(weak)})
                    continue
                try:
                    citekey = ops.paper_key(row['citekey'])
                except ValueError:
                    fallback = 'zotero-'+row['item_key']
                    try:
                        citekey = ops.paper_key(fallback)
                    except ValueError:
                        citekey = 'zotero-'+hashlib.sha256(row['item_key'].encode()).hexdigest()[:12]
                    report['errors'].append('条目 citekey 不适合跨平台文件名，已使用稳定 Zotero 后备标识。')
                # Windows 不区分大小写，其他系统亦统一避免跨平台目录碰撞。
                if any(c.casefold()==citekey.casefold() for c in existing):
                    report['duplicates'].append({'item_key':row['item_key'],'reason':'citekey 目录已占用','candidates':[citekey]})
                    continue
                if not cfg['sync']['create_missing_papers']:
                    continue
                meta = ops.load(root/'workflow/templates/paper/meta.yaml')
                meta.update(citekey=citekey,created_at=ops.now())
                if not dry_run:
                    ops.new_paper(root,project.name,citekey,refresh=False)
                    meta = ops.load(project/'10_literature/papers'/citekey/'meta.yaml')
                report['created'].append(citekey)
            original = copy.deepcopy(meta)
            meta.setdefault('project_id','project:'+project.name)
            previous = meta.get('zotero',{}).get('synced_fields',{})
            if cfg['sync']['update_metadata'] or citekey in report['created']:
                for field in ['title','authors','year','venue','doi','url','language']:
                    if not cfg['sync']['preserve_manual'] or not literature.meaningful(meta.get(field)) or meta.get(field)==previous.get(field):
                        meta[field] = row[field]
                categories = []
                for collection in row['collection_keys']:
                    mapped = options['category_map'].get(collection,options['category_map'].get(row['collection_names'].get(collection),row['collection_names'].get(collection,collection)))
                    categories.extend(mapped if isinstance(mapped,list) else [mapped])
                if cfg['sync']['preserve_manual']:
                    meta['categories'] = sorted(set(meta.get('categories',[])+categories))
                    meta['topic_tags'] = sorted(set(meta.get('topic_tags',[])+row['tags']))
                else:
                    meta['categories'] = sorted(set(categories)); meta['topic_tags'] = row['tags']
            z = {field:row[field] for field in ['library_type','library_id','item_key','collection_keys','tags','attachment_paths','version']}
            z['synthetic_item_key'] = row['synthetic_item_key']
            z['synced_fields'] = {field:row[field] for field in ['title','authors','year','venue','doi','url','language']}
            # synced_at 仅在内容变化时推进，重复同步不制造 Git 变更。
            z['synced_at'] = original.get('zotero',{}).get('synced_at',literature.TODO)
            meta['zotero'] = z
            meta_path=(paper_folder(citekey)/'meta.yaml').relative_to(project).as_posix()
            _identity_links(meta,row,citekey,cfg,meta_path)
            changed = meta!=original
            if changed:
                z['synced_at'] = ops.now(); meta['updated_at'] = ops.now()
            attachment_refs = []
            for value in row['attachment_paths']:
                path = Path(value)
                remote = bool(urlparse(value).scheme in ['http','https','zotero'])
                local_exists = not remote and path.is_file()
                if not remote and not local_exists:
                    report['missing_attachments'].append({'paper':citekey,'path':value})
                attachment_refs.append({'path':value,'exists':local_exists,'mode':cfg['sync']['attachment_mode']})
                if cfg['sync']['attachment_mode']=='copy' and local_exists and not dry_run:
                    destination = ops.contained(project,paper_folder(citekey)/'01_source/attachments'/path.name)
                    if destination.exists() and destination.read_bytes()!=path.read_bytes():
                        report['errors'].append(f'{citekey} 附件目标冲突；保留原件，不覆盖。')
                    elif not destination.exists():
                        storage.copy_file(path,destination)
            link_data = dict(schema_version=1,generated_by='wf',generated_from=[meta_path],
                library_type=row['library_type'],library_id=row['library_id'],item_key=row['item_key'],attachments=attachment_refs,
                select_uri=f'zotero://select/{"groups/"+row["library_id"] if row["library_type"]=="group" else "library"}/items/{quote(row["item_key"])}')
            link_data.update(id='artifact:'+meta['id'].split(':',1)[-1]+':source-links',type='artifact',
                             contract_type='paper.source.links',paper_id=meta['id'],links=[])
            links = paper_folder(citekey)/'01_source/source-links.yaml'
            ops.contained(project,links)
            old_links = ops.load(links) if links.is_file() else {}
            old_id=old_links.get('id')
            if isinstance(old_id,str) and old_id.startswith('source-links:'):
                link_data['aliases']=sorted(set(old_links.get('aliases',[])+[old_id]))
            elif old_id:
                link_data['id']=old_id
                if old_links.get('aliases'):link_data['aliases']=old_links['aliases']
            link_data['links']=old_links.get('links',[])
            link_data['generated_at'] = old_links.get('generated_at') or ops.now()
            links_changed = link_data!=old_links
            if links_changed:
                link_data['generated_at'] = ops.now()
            if not dry_run:
                if changed:
                    ops.save(paper_folder(citekey)/'meta.yaml',meta)
                if links_changed:
                    ops.save(links,link_data)
            if citekey not in report['created']:
                report['updated' if changed or links_changed else 'unchanged'].append(citekey)
            existing[citekey] = meta
            if citekey in report['created']:
                register(citekey,meta)
        except (ValueError,OSError,TypeError,KeyError) as error:
            report['errors'].append(f'条目 {row["item_key"]} 处理失败（{type(error).__name__}）；其他条目继续。')
    if not dry_run:
        report['index_update_pending']=not cfg['sync']['update_hash']
        ops.save(project/'00_inbox/zotero-sync-report.yaml',report)
        if cfg['sync']['update_hash']:
            ops.index(root,project.name)
        else:
            print('Zotero 源元数据已同步；索引/图谱待刷新，请运行 wf.py index '+project.name+'。')
    print(f'Zotero {"预览" if dry_run else "同步完成"}：新建 {len(report["created"])}；更新 {len(report["updated"])}；'
          f'未变化 {len(report["unchanged"])}；疑似重复 {len(report["duplicates"])}；损坏/错误 {len(report["errors"])}；附件缺失 {len(report["missing_attachments"])}。')
    return report
