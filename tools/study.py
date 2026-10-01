"""论文学习交付与分段翻译规划。无模型、网络或新依赖；使用既有合同闭环。"""
import hashlib
from pathlib import Path
import re

try:
    from . import literature, registry, storage
except ImportError:
    import literature, registry, storage

DELIVERIES = {
    'summary': ('summary.md', 'literature-synthesis', [
        '阅读导航', '全局定位', '全文主线', '方法与证据', '公式与机制', '结果与意义',
        '代表文献与前因后果', '知识框架', '局限与待核验', '与研究方向的关系', '来源索引']),
    'concept-guide': ('concept-guide.md', 'literature-learning-guide', [
        '学习导航', '底层原理', '概念频次与层次', '从原理到器件', '公式逐步解释',
        '对照论文学习', '代表文献导读', '知识网络', '自测与常见误区', '来源与缺口']),
}

def hash_text(text):
    return 'sha256:' + hashlib.sha256(text.encode('utf-8')).hexdigest()

def split_lines(text, max_chars=5500):
    """Disjoint inclusive line ranges; no dropped lines or silent truncation."""
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or not 500 <= max_chars <= 10000:
        raise ValueError('segment_chars 必须是500–10000之间的整数')
    lines = text.splitlines()
    ranges, start, count = [], 0, 0
    for n, line in enumerate(lines):
        if len(line) > max_chars:
            raise ValueError('单行超过片段限制；先将原文另存为有段落/换行的文本，不截断原件')
        size = len(line) + (1 if n > start else 0)
        if count + size > max_chars and n > start:
            ranges.append((start + 1, n))
            start, count = n, 0
        count += len(line) + (1 if n > start else 0)
    if lines:
        ranges.append((start + 1, len(lines)))
    return ranges

def paper_record(project, citekey, ops, index):
    ref = registry.resolve(project, 'paper:' + citekey, ops, index=index)
    folder = ops.contained(project, ref['path']).parent
    return ref, folder, ops.load(folder / 'meta.yaml')

def plan(root, project, citekey, ops, dry_run=False, segment_chars=5500):
    """Write reviewable task packets and one coverage ledger; never call providers."""
    index = registry.build(root, project, ops, write=not dry_run)
    paper, folder, meta = paper_record(project, citekey, ops, index)
    key = meta['citekey']
    token = hashlib.sha256(paper['id'].encode()).hexdigest()[:12]
    task_folder = f'00_inbox/study-{token}'
    prefix = folder.relative_to(project).as_posix()
    segments, packets, source_seen = [], {}, set()
    for source in meta.get('source_files', []):
        path = literature.resolve_path(project, source.split('#', 1)[0], ops)
        if path.suffix.lower() not in {'.md', '.txt'} or path in source_seen:
            continue
        source_seen.add(path)
        if not path.is_file() or path.stat().st_size > 1_000_000:
            raise ValueError('翻译源缺失或超过1MB；请先提取分段文本')
        text = path.read_text(encoding='utf-8-sig')
        matches = [dict(ref, id=identifier) for identifier, ref in index['artifacts'].items() if ref['path'] == path.relative_to(project).as_posix() and not ref.get('anchor')]
        if not matches:
            raise ValueError('原文尚未登记；先运行 index')
        reference = matches[0]
        for start, end in split_lines(text, segment_chars):
            selected = '\n'.join(text.splitlines()[start-1:end])
            sid = 'segment-' + hashlib.sha256((reference['id'] + f':{start}:{end}:' + hash_text(selected)).encode()).hexdigest()[:16]
            tid = f'translate-{token}-{len(segments)+1:03}'
            filename = f'{task_folder}/{tid}.yaml'
            segment = dict(id=sid, source_ref=dict(id=reference['id'], path=reference['path'], anchor=f'L{start}-{end}', hash=reference['hash']),
                           text_hash=hash_text(selected), task_id=tid, task_file=filename)
            segments.append(segment)
            packet = dict(task_id=tid, task_type='literature-translate', objective='逐段完整翻译当前原文片段，保持章节/段落/公式/图表/引用编号；不要总结替代。跨片段句子按来源原序衔接。',
                          inputs=[dict(id=paper['id'], anchor='L1-3'), segment['source_ref']],
                          outputs=[dict(id='translation:' + key, type='paper.translation', mode='append')],
                          allowed_paths=[prefix], context=dict(task_type='literature-translate', paper_citekey=key),
                          constraints=dict(response_format='json', append_only=True, require_complete_context=True, segment_id=sid,
                                           source_anchor=segment['source_ref']['anchor'],
                                           markers=f'完整content以 <!-- translation:{sid} --> 开始，以 <!-- /translation:{sid} --> 结束；仅正文片段，不含front matter。',
                                           coverage='正文与图注逐段译；作者姓名、参考书目、公式、图内数值/型号可原样保留并说明；页眉页脚/坐标刻度明确列为出版信息或图内标注，不冒充遗漏正文。'))
            packets[filename] = packet
    if not segments:
        raise ValueError('没有已登记的UTF-8原文；先归档文本并填写meta.source_files')
    for kind, (name, task_type, headings) in DELIVERIES.items():
        tid = f'{kind}-{token}'
        filename = f'{task_folder}/{tid}.yaml'
        inputs = [dict(id=paper['id'], anchor='L1-3'), dict(id='analysis:' + key, anchor='overview'),
                  dict(id='analysis:' + key, anchor='extraction'), dict(id='reading:' + key, anchor='1. 全局定位')]
        if kind == 'concept-guide':
            inputs += [dict(id='analysis:' + key, anchor='formulas'), dict(id='analysis:' + key, anchor='concepts')]
        packets[filename] = dict(task_id=tid, task_type=task_type,
            objective='根据已核验成果生成可通读的' + ('综合总结' if kind == 'summary' else '底层原理到论文的概念学习指南') + '；重要结论有证据，全文及外部文献范围明确，不将索引当作科学结论。',
            inputs=inputs, allowed_paths=[prefix], context=dict(task_type=task_type, paper_citekey=key),
            constraints=dict(response_format='json', required_sections=headings,
                             scope='只覆盖实际输入；不足时明确缺口，主模型编排补充必要章节/卡/参考文献摘录后再派发。'))
    ledger = dict(schema_version=1, generated_by='wf.study', paper_id=paper['id'], segments=segments,
                  translation_ref='translation:' + key, expected_sources=[s['source_ref']['path'] for s in segments])
    ledger_path = f'{prefix}/02_translation/coverage.yaml'
    paths = {filename: packet for filename, packet in packets.items()}
    paths[ledger_path] = ledger
    # Preflight every target before writing anything; existing task/content is immutable.
    for rel, data in paths.items():
        path = ops.contained(project, rel)
        if path.exists() and ops.load(path) != data:
            raise ValueError('已有不同任务/覆盖清单，原件保留；请另建任务或核验源变化：' + rel)
    if not dry_run:
        for rel, data in paths.items():
            path = ops.contained(project, rel)
            if not path.exists():
                ops.save(path, data)
    return dict(paper_id=paper['id'], dry_run=dry_run, segments=len(segments), task_files=list(packets),
                coverage=ledger_path, deliveries=[f'{prefix}/06_synthesis/{v[0]}' for v in DELIVERIES.values()],
                next_action='先确认全局预读；串行翻译→真实评审/accept→覆盖核对→综合/指南；本命令未执行模型或核验科学内容。')

def coverage(root, project, citekey, ops):
    index = registry.build(root, project, ops, write=False)
    paper, folder, meta = paper_record(project, citekey, ops, index)
    ledger = ops.load(folder / '02_translation/coverage.yaml')
    if ledger.get('paper_id') != paper['id'] or ledger.get('schema_version') != 1:
        raise ValueError('覆盖清单身份或版本不符')
    text = literature.paper_path(folder, 'translation.md').read_text(encoding='utf-8-sig')
    ids, ranges, errors, accepted = set(), {}, [], 0
    rows = ledger.get('segments')
    if not isinstance(rows, list) or not rows:
        raise ValueError('覆盖清单没有片段')
    for row in rows:
        sid = row['id']
        if sid in ids:
            errors.append('重复片段ID：' + sid)
        ids.add(sid)
        ref = registry.resolve(project, row['source_ref'], ops, index=index)
        match = re.fullmatch(r'L(\d+)-(\d+)', ref['anchor'])
        if not match:
            raise ValueError('片段必须使用明确行号范围')
        start, end = map(int, match.groups())
        file = ops.contained(project, ref['path'])
        lines = file.read_text(encoding='utf-8-sig').splitlines()
        if start < 1 or end < start or end > len(lines) or hash_text('\n'.join(lines[start-1:end])) != row['text_hash']:
            errors.append('片段原文发生变化：' + sid)
        ranges.setdefault(ref['path'], []).append((start, end))
        begin, finish = f'<!-- translation:{sid} -->', f'<!-- /translation:{sid} -->'
        match_content = re.search(re.escape(begin) + r'([\s\S]*?)' + re.escape(finish), text)
        if text.count(begin) != 1 or text.count(finish) != 1 or not match_content or not match_content[1].strip():
            errors.append('缺少、重复或空翻译片段：' + sid)
        state = ops.load(project / '.runs' / row['task_id'] / 'status.yaml') if (project / '.runs' / row['task_id'] / 'status.yaml').exists() else {}
        if state.get('status') == 'accepted':
            attempt = state['attempt']
            task = ops.load(project / '.runs' / row['task_id'] / 'task.yaml')
            receipt = ops.load(project / '.runs' / row['task_id'] / 'final/acceptance.yaml')
            if task.get('constraints', {}).get('segment_id') == sid and receipt.get('decision') == 'accept':
                accepted += 1
            else:
                errors.append('验收与片段不匹配：' + sid)
        else:
            errors.append('片段未经过真实accept：' + sid)
    actual_markers = re.findall(r'<!-- translation:([\w-]+) -->', text)
    if set(actual_markers) != ids:
        errors.append('译文含清单外片段或缺失清单片段')
    expected_paths = {literature.resolve_path(project, s.split('#',1)[0], ops).relative_to(project).as_posix()
                      for s in meta['source_files'] if Path(s.split('#',1)[0]).suffix.lower() in {'.md','.txt'}}
    if set(ranges) != expected_paths:
        errors.append('覆盖清单未覆盖meta.source_files中的全部文本来源')
    for rel, intervals in ranges.items():
        position = 1
        for start, end in sorted(intervals):
            if start != position:
                errors.append('原文范围有缺口或重叠：' + rel)
            position = end + 1
        if position != len(ops.contained(project, rel).read_text(encoding='utf-8-sig').splitlines()) + 1:
            errors.append('原文末尾未覆盖：' + rel)
    return dict(paper_id=paper['id'], expected=len(rows), accepted=accepted,
                structural_coverage=not errors, errors=sorted(set(errors)),
                scientific_note='范围和验收记录检查不证明译文忠实；须逐段核对原文、术语、数字和图注。')

def validate_delivery(root, project, path, kind, paper_id, ops):
    info, body = literature.markdown(path)
    ops.contract(root, 'study_delivery', info)
    if info['paper_id'] != paper_id:
        raise ValueError('综合交付指向另一篇论文')
    headings = [title for _, title in re.findall(r'^##\s+(\d+)\.\s*(.+?)\s*$', body, re.M)]
    expected = DELIVERIES[kind][2]
    if headings != expected:
        raise ValueError('综合交付缺少规定章节或顺序不符：' + kind)
    if not info['source_refs']:
        raise ValueError('综合交付缺少来源')
    ops.refs(project, info)
    return info
