"""编号目录、迁移、只读 Zotero 与可追溯候选图谱的离线验收。"""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools import wf, literature, zotero, knowledge, storage


class LiteratureUpgradeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for rel in ['config','workflow/layouts','workflow/prompts']:
            shutil.copytree(wf.ROOT/rel,self.root/rel)
        for rel in ['workflow/README.md','workflow/literature.md','workflow/reproduction.md','workflow/schemas.yaml','.gitignore','.env.example']:
            shutil.copyfile(wf.ROOT/rel,self.root/rel)
        (self.root/'tools').mkdir(); (self.root/'tests').mkdir()
        shutil.copyfile(self.root/'config/models.example.yaml',self.root/'config/models.local.yaml')
        with contextlib.redirect_stdout(io.StringIO()):
            wf.bootstrap(self.root)
            wf.init(self.root,'research','测试研究')
        self.project = self.root/'projects/research'
        self.base = self.project/'10_literature'

    def fixture(self,name):
        return json.loads((wf.ROOT/'tests/fixtures/zotero'/name).read_text(encoding='utf-8'))

    def exporter(self,payload=None,format='better-bibtex-json'):
        if payload is None:
            payload = self.fixture('better-bibtex.json')
        file = self.project/'00_inbox/export.json'
        storage.write_text(file,json.dumps(payload,ensure_ascii=False))
        config = wf.load(self.root/'config/zotero.example.yaml')
        config['zotero'].update(enabled=True,mode='export')
        config['zotero']['export'].update(path=str(file),format=format)
        wf.save(self.root/'config/zotero.local.yaml',config)
        return config

    def snapshot(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def paper(self,key='sample'):
        return wf.new_paper(self.root,'research',key)

    def test_numbered_structure_and_safe_better_bibtex_names(self):
        paper = self.paper('Smith_2025.Method')
        self.assertEqual({p.name for p in paper.iterdir()}, {'meta.yaml','01_source','02_translation','03_reading','04_analysis','05_notes'})
        for filename in ['02_translation/translation.md','03_reading/reading.md','04_analysis/analysis.yaml','05_notes/notes.md']:
            self.assertTrue((paper/filename).is_file())
        with self.assertRaises(ValueError):self.paper('smith_2025.method')
        for key in ['../escape','con','bad:name','last.']:
            with self.assertRaises(ValueError):self.paper(key)
        wf.validate(self.root,'research')

    def test_migration_copies_originals_and_reports_conflicts(self):
        folder = self.base/'papers/old'
        folder.mkdir(); (folder/'source').mkdir()
        original = b'original source bytes'
        (folder/'source/original.txt').write_bytes(original)
        wf.save(folder/'meta.yaml',dict(citekey='old',title='Old',authors=[],year=2020,status='read',source_refs=[]))
        storage.write_text(folder/'translation.md','old translation')
        storage.write_text(folder/'reading.md','old reading')
        storage.write_text(folder/'note.md','old notes')
        before = self.snapshot()
        report = wf.migrate(self.root,'research',True)
        self.assertEqual(before,self.snapshot()); self.assertTrue(report['copied'])
        wf.migrate(self.root,'research')
        self.assertEqual((folder/'01_source/original.txt').read_bytes(),original)
        self.assertEqual((folder/'source/original.txt').read_bytes(),original)
        self.assertEqual((folder/'02_translation/translation.md').read_text(),'old translation')
        self.assertEqual((folder/'05_notes/notes.md').read_text(),'old notes')
        self.assertEqual(wf.load(folder/'meta.yaml')['status'],'deep-read')
        self.assertTrue(list((self.project/'.runs').glob('*/meta.before.yaml')))
        storage.write_text(folder/'03_reading/reading.md','manual newer content')
        report = wf.migrate(self.root,'research')
        self.assertTrue(report['conflicts'])
        self.assertEqual((folder/'03_reading/reading.md').read_text(),'manual newer content')
        self.assertEqual((folder/'reading.md').read_text(),'old reading')

    def test_legacy_task_paths_resolve_after_originals_removed(self):
        paper = self.paper()
        analysis = wf.load(paper/'04_analysis/analysis.yaml')
        analysis['overview'].update(object='对象',core_problem='问题',why_important='重要性',position='位置')
        wf.save(paper/'04_analysis/analysis.yaml',analysis)
        task = wf.load(self.root/'workflow/layouts/task.yaml')
        task.update(task_id='legacy-path',inputs=['10_literature/papers/sample/analysis.yaml'],
                    source_refs=['10_literature/papers/sample/analysis.yaml'],context={'task_type':'literature-translate','paper_citekey':'sample'})
        wf.save(self.root/'task.yaml',task)
        result = wf.run(self.root,'research','task.yaml')
        self.assertEqual(wf.load(result/'run.yaml')['status'],'waiting-manual')

    def test_local_and_web_api_fixture_parsing(self):
        local,errors = zotero.parse(self.fixture('local-api.json'),mode='local')
        self.assertFalse(errors); self.assertEqual(local[0]['citekey'],'LocalPaper2024')
        self.assertEqual(local[0]['doi'],'10.0000/local')
        self.assertEqual(local[0]['attachment_paths'],['missing-local.pdf'])
        web,errors = zotero.parse(self.fixture('web-api.json'),mode='web',library_id='123')
        self.assertFalse(errors); self.assertEqual(web[0]['citekey'],'zotero-WEB00001')
        self.assertEqual(web[0]['year'],2025); self.assertEqual(web[0]['version'],8)

    def test_better_bibtex_and_csl_json_fixture_parsing(self):
        rows,errors = zotero.parse(self.fixture('better-bibtex.json'))
        self.assertFalse(errors); self.assertEqual(rows[0]['citekey'],'MockSurvey2025')
        self.assertEqual(rows[0]['authors'],['Example Author'])
        self.assertEqual(rows[0]['collection_keys'],['MOCKCOLL'])
        rows,errors = zotero.parse(self.fixture('csl.json'),format='csl-json')
        self.assertFalse(errors); self.assertEqual(rows[0]['year'],2025)
        self.assertEqual(rows[0]['authors'],['CSL Author'])

    def test_api_pagination_and_read_only_headers_without_real_network(self):
        cfg = zotero.config(self.root,wf); cfg.update(enabled=True,mode='web')
        cfg['web'].update(library_id='123',api_key_env='TEST_ZOTERO_KEY')
        calls = []
        def reply(url,timeout,key):
            calls.append((url,key))
            if '/collections?' in url:return [{'key':'WEBCOLL','data':{'name':'Fixture collection'}}]
            return self.fixture('web-api.json')
        with patch.dict(os.environ,{'TEST_ZOTERO_KEY':'mock-test-credential'}),patch.object(zotero,'get_json',side_effect=reply):
            rows,errors = zotero.fetch(self.root,cfg,wf)
        self.assertFalse(errors); self.assertEqual(rows[0]['collection_names']['WEBCOLL'],'Fixture collection')
        self.assertTrue(all(url.startswith('https://api.zotero.org/users/123/') for url,_ in calls))
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = io.BytesIO(json.dumps(self.fixture('web-api.json')).encode())
            zotero.get_json('https://api.zotero.org/users/123/items',10,'mock-test-credential')
            request = opener.return_value.open.call_args.args[0]
            self.assertEqual(request.get_method(),'GET')
            self.assertEqual(request.get_header('Zotero-api-key'),'mock-test-credential')
            self.assertEqual(request.get_header('Zotero-api-version'),'3')

    def test_local_api_fetch_and_no_proxy(self):
        cfg = zotero.config(self.root,wf); cfg['enabled'] = True
        def reply(url,timeout,key):
            self.assertIsNone(key)
            return [] if '/collections?' in url else self.fixture('local-api.json')
        with patch.object(zotero,'get_json',side_effect=reply):
            rows,_ = zotero.fetch(self.root,cfg,wf)
        self.assertEqual(len(rows),1)
        cfg['local']['base_url']='http://example.com/api/users/0'
        with self.assertRaisesRegex(ValueError,'loopback'):zotero.fetch(self.root,cfg,wf)

    def test_local_attachment_endpoint_and_fallback(self):
        cfg=zotero.config(self.root,wf);cfg['enabled']=True
        payload=self.fixture('local-api.json');payload[1]['data'].pop('path')
        def reply(url,timeout,key):return [] if '/collections?' in url else copy.deepcopy(payload)
        with patch.object(zotero,'get_json',side_effect=reply),patch.object(zotero,'local_attachment_path',return_value='mock-local.pdf') as attachment:
            rows,errors=zotero.fetch(self.root,cfg,wf)
        self.assertFalse(errors);self.assertEqual(rows[0]['attachment_paths'],['mock-local.pdf'])
        self.assertTrue(attachment.call_args.args[0].endswith('/items/LOCALPDF/file/view/url'))
        with patch.object(zotero,'get_json',side_effect=reply),patch.object(zotero,'local_attachment_path',side_effect=zotero.Unavailable('fixture')):
            rows,errors=zotero.fetch(self.root,cfg,wf)
        self.assertTrue(errors);self.assertTrue(rows[0]['attachment_paths'][0].startswith('zotero://open-pdf/'))

    def test_api_pagination_reads_all_pages(self):
        cfg=zotero.config(self.root,wf);cfg['enabled']=True
        calls=[]
        def reply(url,timeout,key):
            calls.append(url)
            if '/collections?' in url:return []
            return self.fixture('local-api.json')[:1]*100 if 'start=0' in url else self.fixture('local-api.json')[:1]
        with patch.object(zotero,'get_json',side_effect=reply):rows,errors=zotero.fetch(self.root,cfg,wf)
        self.assertFalse(errors);self.assertEqual(len(rows),101)
        self.assertTrue(any('start=100' in url for url in calls))

    def test_optional_attachment_copy_never_overwrites_existing_pdf(self):
        local=self.root/'original.pdf';local.write_bytes(b'mock pdf')
        payload=self.fixture('better-bibtex.json');payload['items'][0]['attachments']=[{'path':str(local)}]
        cfg=self.exporter(payload);cfg['zotero']['sync']['attachment_mode']='copy'
        wf.save(self.root/'config/zotero.local.yaml',cfg)
        zotero.sync(self.root,self.project,wf)
        target=self.base/'papers/MockSurvey2025/01_source/attachments/original.pdf'
        self.assertEqual(target.read_bytes(),b'mock pdf')
        local.write_bytes(b'changed source')
        report=zotero.sync(self.root,self.project,wf)
        self.assertTrue(report['errors']);self.assertEqual(target.read_bytes(),b'mock pdf')
        self.assertEqual(local.read_bytes(),b'changed source')

    def test_formula_meaning_alias_and_principle_source_validation(self):
        paper=self.paper();card=wf.new_concept(self.root,'research','base')
        data=wf.load(paper/'04_analysis/analysis.yaml')
        data['formulas']=[dict(id='eq-1',label='1',latex='x=1',name_zh='mock',meaning='alias',symbols=[],assumptions=[],
             derivation_steps=[],intuition='mock',special_cases=[],related_concepts=[],source_refs=['research-profile.yaml'],confidence='TODO(user)')]
        wf.save(paper/'04_analysis/analysis.yaml',data);wf.validate(self.root,'research')
        data['first_principles']=[dict(id='base',statement='test statement',source_refs=[])]
        wf.save(paper/'04_analysis/analysis.yaml',data)
        with self.assertRaisesRegex(ValueError,'source_refs'):wf.validate(self.root,'research')

    def test_sync_preserves_manual_fields_and_all_reading_content(self):
        config = self.exporter()
        options = wf.load(self.project/'project.yaml')
        options['zotero']['category_map']={'MOCKCOLL':'我的分类'}
        wf.save(self.project/'project.yaml',options)
        report = zotero.sync(self.root,self.project,wf)
        self.assertEqual(len(report['created']),2)
        paper = self.base/'papers/MockSurvey2025'
        meta = wf.load(paper/'meta.yaml')
        self.assertEqual(meta['categories'],['我的分类'])
        self.assertEqual(meta['topic_tags'],['mock-topic'])
        self.assertEqual(meta['translation_status'],'none')
        self.assertFalse(list((paper/'01_source').rglob('*.pdf')))
        meta['title']='手工标题'; meta['categories'].append('人工分类'); meta['status']='reading'
        wf.save(paper/'meta.yaml',meta)
        content = {}
        for rel in ['02_translation/translation.md','03_reading/reading.md','04_analysis/analysis.yaml','05_notes/notes.md']:
            content[rel]=(paper/rel).read_bytes()
        payload = self.fixture('better-bibtex.json'); payload['items'][0]['title']='Zotero changed title'
        self.exporter(payload)
        zotero.sync(self.root,self.project,wf)
        meta = wf.load(paper/'meta.yaml')
        self.assertEqual(meta['title'],'手工标题'); self.assertEqual(meta['status'],'reading')
        self.assertIn('人工分类',meta['categories'])
        for rel,original in content.items():self.assertEqual((paper/rel).read_bytes(),original)
        old_meta=(paper/'meta.yaml').read_bytes(); old_links=(paper/'01_source/source-links.yaml').read_bytes()
        report=zotero.sync(self.root,self.project,wf)
        self.assertEqual(report['updated'],[])
        self.assertEqual((paper/'meta.yaml').read_bytes(),old_meta)
        self.assertEqual((paper/'01_source/source-links.yaml').read_bytes(),old_links)
        wf.validate(self.root,'research')

    def test_sync_updates_owned_metadata_and_keeps_existing_citekey(self):
        self.exporter();zotero.sync(self.root,self.project,wf)
        payload=self.fixture('better-bibtex.json')
        payload['items'][0]['title']='Updated source title'
        payload['items'][0]['citationKey']='ChangedCitekey'
        self.exporter(payload)
        report=zotero.sync(self.root,self.project,wf)
        self.assertIn('MockSurvey2025',report['updated'])
        self.assertEqual(wf.load(self.base/'papers/MockSurvey2025/meta.yaml')['title'],'Updated source title')
        self.assertFalse((self.base/'papers/ChangedCitekey').exists())

    def test_duplicate_doi_and_weak_title_year_never_overwrite(self):
        payload=self.fixture('better-bibtex.json')
        payload['items'][1]['DOI']=payload['items'][0]['DOI']
        self.exporter(payload)
        report=zotero.sync(self.root,self.project,wf)
        self.assertEqual(len(report['duplicates']),2);self.assertFalse(report['created'])
        paper=self.paper('manual-paper');meta=wf.load(paper/'meta.yaml')
        meta.update(title='MOCK survey: example research workflow',year=2025)
        wf.save(paper/'meta.yaml',meta)
        self.exporter()
        report=zotero.sync(self.root,self.project,wf)
        self.assertEqual(len(report['duplicates']),1)
        self.assertFalse((self.base/'papers/MockSurvey2025').exists())
        self.assertEqual(wf.load(paper/'meta.yaml'),meta)

    def test_collection_tag_filter_and_invalid_citekey_fallback(self):
        payload=self.fixture('better-bibtex.json')
        payload['items'][0]['citationKey']='not:safe'
        self.exporter(payload)
        options=wf.load(self.project/'project.yaml');options['zotero']['collections']=['NOT_PRESENT']
        wf.save(self.project/'project.yaml',options)
        self.assertFalse(zotero.sync(self.root,self.project,wf)['created'])
        options['zotero'].update(collections=[],tag_filter=['mock-topic'])
        wf.save(self.project/'project.yaml',options)
        report=zotero.sync(self.root,self.project,wf)
        self.assertIn('zotero-MOCK0001',report['created'])

    def test_zotero_and_key_unavailable_leave_everything_unchanged(self):
        before=self.snapshot()
        with patch('urllib.request.build_opener',side_effect=AssertionError('不能访问真实 API')):
            self.assertFalse(zotero.status(self.root,self.project,wf)['available'])
            self.assertTrue(zotero.sync(self.root,self.project,wf)['errors'])
        self.assertEqual(before,self.snapshot())
        cfg=wf.load(self.root/'config/zotero.example.yaml')
        cfg['zotero'].update(enabled=True,mode='web');cfg['zotero']['web'].update(library_id='123',api_key_env='MISSING_ZOTERO_KEY')
        wf.save(self.root/'config/zotero.local.yaml',cfg)
        before=self.snapshot()
        with patch.dict(os.environ,{},clear=True),patch('urllib.request.build_opener',side_effect=AssertionError('缺 Key 不联网')):
            self.assertTrue(zotero.sync(self.root,self.project,wf)['errors'])
        self.assertEqual(before,self.snapshot());wf.validate(self.root,'research')

    def test_network_error_is_redacted_and_does_not_write(self):
        cfg=wf.load(self.root/'config/zotero.example.yaml');cfg['zotero']['enabled']=True
        wf.save(self.root/'config/zotero.local.yaml',cfg);before=self.snapshot();capture=io.StringIO()
        with patch('urllib.request.build_opener',side_effect=OSError('sensitive-private-error')),contextlib.redirect_stdout(capture):
            report=zotero.sync(self.root,self.project,wf)
        self.assertTrue(report['errors']);self.assertNotIn('sensitive-private-error',capture.getvalue())
        self.assertEqual(before,self.snapshot())

    def test_invalid_zotero_config_does_not_block_offline_doctor(self):
        storage.write_text(self.root/'config/zotero.local.yaml','zotero: [invalid]')
        capture=io.StringIO()
        with patch('urllib.request.build_opener',side_effect=AssertionError('offline 不联网')),contextlib.redirect_stdout(capture):
            wf.doctor(self.root,True)
        self.assertIn('手动工作流仍可用',capture.getvalue())

    def test_duplicate_item_keys_report_without_creating_papers(self):
        payload=self.fixture('better-bibtex.json')
        payload['items'][1]['itemKey']=payload['items'][0]['itemKey']
        self.exporter(payload);report=zotero.sync(self.root,self.project,wf)
        self.assertFalse(report['created']);self.assertEqual(len(report['duplicates']),2)

    def test_api_redirect_cannot_forward_credentials(self):
        handler=zotero.NoRedirect()
        with self.assertRaises(zotero.Unavailable):
            handler.redirect_request(None,None,302,'redirect',{},'https://example.org/untrusted')

    def test_broken_analysis_is_reported_without_stopping_other_papers(self):
        a=self.paper('alpha');b=self.paper('beta')
        storage.write_text(a/'04_analysis/analysis.yaml','concepts: invalid')
        graph=wf.graph(self.root,'research')
        self.assertIn('paper:beta',[n['id'] for n in graph['nodes']])
        self.assertTrue(graph['scan_issues'])

    def test_repeated_migration_does_not_create_new_backup(self):
        folder=self.base/'papers/old';folder.mkdir();(folder/'source').mkdir()
        meta=wf.load(self.root/'workflow/layouts/paper/meta.yaml');meta['citekey']='old'
        meta.pop('zotero');wf.save(folder/'meta.yaml',meta)
        analysis=wf.load(self.root/'workflow/layouts/paper/04_analysis/analysis.yaml');analysis['paper']='old'
        analysis.pop('first_principles');analysis.pop('review_similarity');wf.save(folder/'analysis.yaml',analysis)
        wf.migrate(self.root,'research')
        before={p.relative_to(self.project/'.runs').as_posix():p.read_bytes() for p in (self.project/'.runs').rglob('*') if p.is_file()}
        report=wf.migrate(self.root,'research')
        after={p.relative_to(self.project/'.runs').as_posix():p.read_bytes() for p in (self.project/'.runs').rglob('*') if p.is_file()}
        self.assertEqual(before,after);self.assertFalse(report['conflicts'])

    def graph_fixture(self):
        for cid in ['base','principle','other']:
            card=wf.new_concept(self.root,'research',cid)
            info,body=literature.markdown(card)
            if cid=='principle':info.update(is_first_principle=True,canonical_statement='Mock principle',prerequisites=['base'])
            literature.write_markdown(card,info,body)
        for key,concepts in [('alpha',['base','principle']),('beta',['base','principle','other']),('gamma',['other'])]:
            paper=self.paper(key);meta=wf.load(paper/'meta.yaml');meta.update(paper_role='survey',concept_ids=concepts,topic_tags=['mock-topic'])
            wf.save(paper/'meta.yaml',meta)
            analysis=wf.load(paper/'04_analysis/analysis.yaml')
            if key!='gamma':
                analysis['first_principles']=[dict(id='principle',statement='Mock principle',source_refs=['research-profile.yaml'])]
                analysis['review_similarity']=dict(core_problem='sample estimation problem',method_summary='sample statistical method',key_concepts=['base'])
            wf.save(paper/'04_analysis/analysis.yaml',analysis)
        return wf.graph(self.root,'research')

    def test_graph_nodes_edges_principle_and_review_clusters(self):
        graph=self.graph_fixture()
        self.assertEqual({n['type'] for n in graph['nodes']},{'paper','concept','principle','topic'})
        kinds={e['type'] for e in graph['edges']}
        self.assertTrue({'similar-first-principle','similar-review','similar-concept-set','prerequisite','belongs-to-topic'}.issubset(kinds))
        for edge in graph['edges']:
            self.assertTrue(edge['evidence']);self.assertIn(edge['confidence'],['low','medium','high'])
            if edge['type'].startswith('similar-'):self.assertEqual(edge['status'],'candidate')
        self.assertTrue(any(c['type']=='similar-first-principle' for c in graph['clusters']))
        self.assertTrue(any(c['type']=='similar-review' for c in graph['clusters']))
        self.assertLess(graph['learning_path'].index('concept:base'),graph['learning_path'].index('concept:principle'))
        self.assertEqual(graph['concept_frequency']['base'],2)
        wf.index(self.root,'research');wf.validate(self.root,'research')
        for name in ['INDEX.md','10_literature/knowledge-map.md','10_literature/reading-list.md']:
            self.assertEqual(literature.markdown(self.project/name)[0]['schema_version'],1)

    def test_manual_map_regions_and_verified_edges_survive_regeneration(self):
        graph=self.graph_fixture();path=self.base/'knowledge-map.md'
        info,body=literature.markdown(path)
        literature.write_markdown(path,info,'人工前言\n'+body+'\n人工结尾\n')
        edge=next(e for e in graph['edges'] if e['type']=='similar-concept-set')
        edge.update(status='verified',reviewed_by='human',review_note='manually checked')
        storage.write_text(self.base/'knowledge-graph.json',json.dumps(graph))
        new=wf.graph(self.root,'research')
        self.assertTrue(any(e['status']=='verified' for e in new['edges']))
        body=literature.markdown(path)[1]
        self.assertTrue(body.startswith('人工前言'));self.assertIn('人工结尾',body)
        card=self.base/'concepts/base.md';info,body=literature.markdown(card);info['canonical_statement']='Changed scientific definition'
        literature.write_markdown(card,info,body)
        new=wf.graph(self.root,'research')
        self.assertFalse(any(e['status']=='verified' for e in new['edges']))
        invalidated=[e for e in new['edges'] if e.get('review_invalidated')]
        self.assertTrue(invalidated);self.assertEqual(invalidated[0]['review_note'],'manually checked')
        new=wf.graph(self.root,'research')
        self.assertTrue(any(e.get('review_note')=='manually checked' for e in new['edges']))

    def test_all_dry_runs_do_not_write_or_create_logs(self):
        self.exporter();self.graph_fixture();before=self.snapshot()
        zotero.sync(self.root,self.project,wf,True)
        wf.index(self.root,'research',True)
        wf.graph(self.root,'research',True)
        wf.migrate(self.root,'research',True)
        self.assertEqual(before,self.snapshot())
        with patch.object(wf,'ROOT',self.root):
            for args in [['graph','research','--dry-run'],['index','research','--dry-run'],['migrate','research','--dry-run'],['zotero','sync','research','--dry-run']]:
                self.assertEqual(wf.main(args),0)
        self.assertEqual(before,self.snapshot())

    def test_damaged_item_does_not_stop_other_items_or_graph_scan(self):
        payload=self.fixture('better-bibtex.json');payload['items'].insert(0,{'title':None})
        self.exporter(payload);report=zotero.sync(self.root,self.project,wf)
        self.assertEqual(len(report['created']),2);self.assertTrue(report['errors'])
        storage.write_text(self.base/'papers/MockSurvey2025/meta.yaml','title: [')
        wf.index(self.root,'research')
        graph=json.loads((self.base/'knowledge-graph.json').read_text(encoding='utf-8'))
        self.assertIn('paper:MockSurvey2026',[n['id'] for n in graph['nodes']])
        self.assertTrue(graph['scan_issues'])
        with self.assertRaises(ValueError):wf.validate(self.root,'research')

    def test_graph_validation_rejects_missing_evidence_and_auto_similarity(self):
        graph=self.graph_fixture();path=self.base/'knowledge-graph.json'
        broken=copy.deepcopy(graph);broken['edges'][0]['evidence']=[]
        storage.write_text(path,json.dumps(broken))
        with self.assertRaisesRegex(ValueError,'证据'):wf.validate(self.root,'research')
        edge=next(e for e in graph['edges'] if e['type'].startswith('similar-'));edge['status']='auto'
        storage.write_text(path,json.dumps(graph))
        with self.assertRaisesRegex(ValueError,'相似关系'):wf.validate(self.root,'research')

    def test_atomic_write_failure_preserves_original(self):
        path=self.root/'important.txt';path.write_bytes(b'original')
        with patch('os.replace',side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):storage.write_text(path,'replacement')
        self.assertEqual(path.read_bytes(),b'original')
        self.assertFalse(list(self.root.glob('.important.txt-*.tmp')))

    def test_secret_scan_distinguishes_function_calls_from_literal_keys(self):
        storage.write_text(self.root/'example.py','authorization = compute_authorization_header_value(\n    choices,\n)\n')
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):self.assertTrue(wf.share_check(self.root,True))
        secret='MOCK'+'Q'*30
        storage.write_text(self.root/'public.json',json.dumps({'api_key':secret}))
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):self.assertFalse(wf.share_check(self.root,True))
        self.assertNotIn(secret,capture.getvalue());self.assertIn('public.json',capture.getvalue())

    @unittest.skipUnless(shutil.which('git'),'Git 用于实际忽略规则验收')
    def test_zotero_config_and_numbered_sources_are_ignored_and_keys_redacted(self):
        def git(*args):return subprocess.run(['git','-C',str(self.root),*args],capture_output=True,check=True)
        git('init','--quiet')
        for rel in ['config/zotero.local.yaml','projects/research/10_literature/papers/sample/01_source/paper.md']:
            self.assertTrue(git('check-ignore','--no-index','--',rel).stdout)
        self.assertEqual(subprocess.run(['git','-C',str(self.root),'check-ignore','--','config/zotero.example.yaml'],capture_output=True).returncode,1)
        git('add','--force','--','config/zotero.local.yaml')
        secret='MOCK'+'A'*30
        storage.write_text(self.root/'public-note.txt','ZOTERO_API_KEY='+secret)
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):self.assertFalse(wf.share_check(self.root,True))
        self.assertIn('config/zotero.local.yaml',capture.getvalue());self.assertIn('疑似密钥',capture.getvalue())
        self.assertNotIn(secret,capture.getvalue())


if __name__=='__main__':
    unittest.main()
