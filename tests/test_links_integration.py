"""ID 索引与 Zotero/图谱的离线连接验收；不使用真实库或 API。"""
import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools import knowledge, literature, registry, storage, wf, zotero


class LinksIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for rel in ['config','workflow/layouts','workflow/prompts']:
            shutil.copytree(wf.ROOT/rel,self.root/rel)
        for rel in ['workflow/README.md','workflow/literature.md','workflow/reproduction.md','workflow/schemas.yaml',
                    'workflow/task-contracts.yaml','.gitignore','.env.example']:
            if (wf.ROOT/rel).is_file():shutil.copyfile(wf.ROOT/rel,self.root/rel)
        (self.root/'tools').mkdir(); (self.root/'tests').mkdir()
        shutil.copyfile(self.root/'config/models.example.yaml',self.root/'config/models.local.yaml')
        with contextlib.redirect_stdout(io.StringIO()):
            wf.bootstrap(self.root); wf.init(self.root,'research','连接测试')
        self.project = self.root/'projects/research'
        self.base = self.project/'10_literature'

    def snapshot(self):
        return {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def exporter(self,payload=None):
        if payload is None:
            payload = json.loads((wf.ROOT/'tests/fixtures/zotero/better-bibtex.json').read_text(encoding='utf-8'))
        export = self.project/'00_inbox/mock-export.json'
        storage.write_text(export,json.dumps(payload,ensure_ascii=False))
        cfg = wf.load(self.root/'config/zotero.example.yaml')
        cfg['zotero'].update(enabled=True,mode='export')
        cfg['zotero']['export']['path']=str(export)
        wf.save(self.root/'config/zotero.local.yaml',cfg)
        return payload

    def graph_fixture(self):
        card = wf.new_concept(self.root,'research','base')
        for key in ['alpha','beta']:
            paper = wf.new_paper(self.root,'research',key,refresh=False)
            data = wf.load(paper/'meta.yaml'); data['concept_ids']=['base']
            wf.save(paper/'meta.yaml',data)
        graph = wf.graph(self.root,'research')
        return graph,card

    def test_every_graph_reference_resolves_in_machine_index(self):
        graph,_ = self.graph_fixture()
        index = registry.load_index(self.project)
        self.assertEqual(graph['connection_model'],'source-links-v1')
        for node in graph['nodes']:registry.resolve(self.project,node['id'],wf,index=index)
        for edge in graph['edges']:
            self.assertIn(edge['source'],index['artifacts']);self.assertIn(edge['target'],index['artifacts'])
            self.assertTrue(any(link['source']==edge['source'] and link['target']==edge['target'] and
                                link['rel']==edge['type'] for link in index['links']))

    def test_zotero_slash_tag_survives_sync_graph_and_validation(self):
        payload = self.exporter()
        payload['items'][0]['tags'] = [{'tag': '/unread'}, {'tag': 'unread'}]
        self.exporter(payload)
        with contextlib.redirect_stdout(io.StringIO()):
            report = zotero.sync(self.root, self.project, wf)
            graph = wf.graph(self.root, 'research')
        self.assertFalse(report['errors'])
        meta = wf.load(self.base / 'papers/MockSurvey2025/meta.yaml')
        self.assertEqual(meta['topic_tags'], ['/unread', 'unread'])
        self.assertEqual(meta['zotero']['tags'], ['/unread', 'unread'])
        index = registry.load_index(self.project)
        self.assertEqual(index['issues'], [])
        for node in graph['nodes']:
            self.assertTrue(registry.valid_id(node['id']))
            registry.resolve(self.project, node['id'], wf, index=index)
        with contextlib.redirect_stdout(io.StringIO()):
            wf.validate(self.root, 'research')

    def test_candidates_persist_in_source_and_source_review_wins(self):
        graph,_ = self.graph_fixture()
        edge = next(edge for edge in graph['edges'] if edge['type']=='similar-concept-set')
        file = self.base/'papers/alpha/meta.yaml'
        data = wf.load(file)
        link = next(link for link in data['links'] if link['rel']=='similar-concept-set')
        self.assertEqual(link['status'],'candidate')
        link.update(status='verified',reviewed_by='main',review_note='已核对来源')
        wf.save(file,data)
        graph = wf.graph(self.root,'research')
        edge = next(edge for edge in graph['edges'] if edge['type']=='similar-concept-set')
        self.assertEqual(edge['status'],'verified')
        # 修改生成图谱不会覆盖已经存在的源核验。
        edge['status']='candidate'
        storage.write_text(self.base/'knowledge-graph.json',json.dumps(graph))
        new = wf.graph(self.root,'research')
        self.assertEqual(next(e for e in new['edges'] if e['type']=='similar-concept-set')['status'],'verified')

    def test_scientific_input_change_expires_source_review_and_retains_audit(self):
        _,card = self.graph_fixture()
        file = self.base/'papers/alpha/meta.yaml'; data = wf.load(file)
        link = next(link for link in data['links'] if link['rel']=='similar-concept-set')
        link.update(status='verified',reviewed_by='verifier',review_note='原核验记录')
        wf.save(file,data);wf.graph(self.root,'research')
        info,body = literature.markdown(card)
        literature.write_markdown(card,info,body+'\n新增概念适用边界。\n')
        graph = wf.graph(self.root,'research')
        link = next(link for link in wf.load(file)['links'] if link['rel']=='similar-concept-set')
        self.assertEqual(link['status'],'candidate');self.assertTrue(link['review_invalidated'])
        self.assertEqual(link['review_note'],'原核验记录');self.assertTrue(link['audit'])
        self.assertTrue(any(e.get('review_invalidated') for e in graph['edges']))

    def test_dangling_link_is_reported_and_not_added_to_graph(self):
        self.graph_fixture()
        file = self.base/'papers/alpha/meta.yaml';data=wf.load(file)
        data['links'].append(dict(rel='uses',target='concept:missing',status='candidate',confidence='low',
            evidence=[dict(file=file.relative_to(self.project).as_posix(),field='links',source_refs=[])]))
        wf.save(file,data)
        graph = wf.graph(self.root,'research')
        index = registry.load_index(self.project)
        self.assertTrue(registry.validate(index,self.project,wf))
        self.assertFalse(any(e['target']=='concept:missing' for e in graph['edges']))
        self.assertTrue(any('悬空' in issue for issue in graph['scan_issues']))

    def test_id_and_legacy_string_evidence_are_normalized_through_index(self):
        self.graph_fixture();file=self.base/'papers/alpha/meta.yaml';data=wf.load(file)
        data['links'].append(dict(rel='contrasts',target='paper:beta',status='candidate',confidence='high',
            evidence=[{'id':'paper:alpha'},'research-profile.yaml',{'id':'analysis:alpha','anchor':'overview'}]))
        wf.save(file,data);graph=wf.graph(self.root,'research')
        edge=next(edge for edge in graph['edges'] if edge['type']=='contrasts')
        self.assertEqual(edge['evidence'][0]['file'],'10_literature/papers/alpha/meta.yaml')
        self.assertEqual(edge['evidence'][1]['field'],'source')
        self.assertEqual(edge['evidence'][0]['source_ref'],{'id':'paper:alpha'})
        self.assertEqual(edge['evidence'][2]['field'],'overview')
        knowledge.validate(literature.Library(self.root,self.project,wf))

    def test_links_only_concepts_feed_similarity_and_learning_order(self):
        wf.new_concept(self.root,'research','base')
        for key in ['alpha','beta']:
            folder=wf.new_paper(self.root,'research',key,refresh=False)
            file=folder/'meta.yaml';data=wf.load(file)
            data['links']=[dict(rel='uses',target='concept:base',status='candidate',confidence='high',
                evidence=[dict(file=file.relative_to(self.project).as_posix(),field='links',source_refs=[])])]
            self.assertEqual(data['concept_ids'],[]);wf.save(file,data)
        graph=wf.graph(self.root,'research')
        self.assertEqual(graph['concept_frequency']['base'],2)
        self.assertTrue(any(e['type']=='similar-concept-set' for e in graph['edges']))
        self.assertEqual(wf.load(self.base/'papers/alpha/meta.yaml')['concept_ids'],[])

    def test_formula_and_claim_are_resolvable_graph_nodes(self):
        self.graph_fixture()
        file = self.base/'papers/alpha/04_analysis/analysis.yaml';data=wf.load(file)
        data['formulas']=[dict(id='eq-1',latex='x=1',source_refs=['research-profile.yaml'])]
        wf.save(file,data)
        claim = wf.new_claim(self.root,'research','alpha','first-claim')
        graph = wf.graph(self.root,'research');index=registry.load_index(self.project)
        self.assertIn('formula:alpha:eq-1',index['artifacts'])
        self.assertTrue(any(n['type']=='formula' for n in graph['nodes']))
        self.assertTrue(any(n['type']=='claim' for n in graph['nodes']))
        self.assertTrue(claim.exists())

    def test_repeated_graph_generation_has_stable_bytes_and_keeps_manual_map(self):
        self.graph_fixture();file=self.base/'knowledge-map.md'
        info,body=literature.markdown(file)
        literature.write_markdown(file,info,'人工研究判断\n'+body+'\n人工后记\n')
        wf.graph(self.root,'research')
        before=(self.base/'knowledge-graph.json').read_bytes()
        map_before=file.read_bytes()
        wf.graph(self.root,'research')
        self.assertEqual(before,(self.base/'knowledge-graph.json').read_bytes())
        self.assertEqual(map_before,file.read_bytes())
        body=literature.markdown(file)[1]
        self.assertTrue(body.startswith('人工研究判断'));self.assertIn('人工后记',body)

    def test_zotero_key_alias_keeps_stable_id_when_citekey_changes(self):
        payload=self.exporter();zotero.sync(self.root,self.project,wf)
        file=self.base/'papers/MockSurvey2025/meta.yaml';identity=wf.load(file)['id']
        payload['items'][0]['citationKey']='NewCitationKey'
        self.exporter(payload);zotero.sync(self.root,self.project,wf)
        data=wf.load(file);index=registry.load_index(self.project)
        self.assertEqual(data['id'],identity)
        self.assertEqual(index['aliases']['zotero:MOCK0001'],identity)
        self.assertEqual(index['aliases']['citekey:NewCitationKey'],identity)
        self.assertEqual(index['aliases']['citekey:MockSurvey2025'],identity)
        self.assertFalse((self.base/'papers/NewCitationKey').exists())
        registry.resolve(self.project,'zotero:MOCK0001',wf)

    def test_paper_and_concept_moves_keep_ids_and_graph_connections(self):
        self.graph_fixture()
        paper=self.base/'papers/alpha';moved=self.base/'papers/relocated-alpha'
        self.assertIn(self.project.resolve(),paper.resolve().parents)
        self.assertIn(self.project.resolve(),moved.resolve().parents)
        paper.rename(moved)
        card=self.base/'concepts/base.md';new_card=self.base/'concepts/relocated-base.md'
        card.rename(new_card)
        graph=wf.graph(self.root,'research');index=registry.load_index(self.project)
        self.assertEqual(index['artifacts']['paper:alpha']['path'],'10_literature/papers/relocated-alpha/meta.yaml')
        self.assertEqual(index['artifacts']['concept:base']['path'],'10_literature/concepts/relocated-base.md')
        self.assertTrue(any(edge['source']=='paper:alpha' and edge['target']=='concept:base' for edge in graph['edges']))
        self.assertEqual(graph['concept_frequency']['base'],2)
        self.assertFalse(paper.exists())

    def test_zotero_sync_uses_current_path_after_paper_move(self):
        self.exporter();zotero.sync(self.root,self.project,wf)
        paper=self.base/'papers/MockSurvey2025';moved=self.base/'papers/relocated-survey'
        self.assertIn(self.project.resolve(),paper.resolve().parents)
        self.assertIn(self.project.resolve(),moved.resolve().parents)
        paper.rename(moved)
        wf.index(self.root,'research')
        report=zotero.sync(self.root,self.project,wf)
        self.assertFalse(report['created']);self.assertFalse(paper.exists())
        self.assertEqual(wf.load(moved/'meta.yaml')['id'],'paper:MockSurvey2025')
        self.assertEqual(registry.resolve(self.project,'zotero:MOCK0001',wf)['path'],
                         '10_literature/papers/relocated-survey/meta.yaml')

    def test_collection_rename_keeps_topic_identity_and_evidence(self):
        payload=self.exporter();zotero.sync(self.root,self.project,wf)
        file=self.base/'papers/MockSurvey2025/meta.yaml'
        before={link['target'] for link in wf.load(file)['links'] if link.get('generated_by')=='wf-zotero'}
        payload['collections']['MOCKCOLL']['name']='新的集合名称'
        self.exporter(payload);zotero.sync(self.root,self.project,wf)
        data=wf.load(file);index=registry.load_index(self.project)
        after={link['target'] for link in data['links'] if link.get('generated_by')=='wf-zotero'}
        self.assertEqual(before,after)
        for target in after:
            self.assertEqual(index['artifacts'][target]['type'],'topic')
            self.assertTrue(any(link['target']==target and link['evidence'] for link in data['links']))

    def test_config_default_sync_preview_has_no_file_changes(self):
        self.exporter();before=self.snapshot()
        report=zotero.sync(self.root,self.project,wf,dry_run=None)
        self.assertTrue(report['dry_run']);self.assertTrue(report['created'])
        self.assertEqual(before,self.snapshot())

    def test_explicit_deferred_hash_reports_pending_without_refreshing_index(self):
        self.exporter();cfg=wf.load(self.root/'config/zotero.local.yaml')
        cfg['zotero']['sync']['update_hash']=False;wf.save(self.root/'config/zotero.local.yaml',cfg)
        before=(self.project/'INDEX.json').read_bytes()
        report=zotero.sync(self.root,self.project,wf)
        self.assertTrue(report['index_update_pending'])
        self.assertEqual(before,(self.project/'INDEX.json').read_bytes())
        wf.index(self.root,'research')
        self.assertIn('paper:MockSurvey2025',registry.load_index(self.project)['artifacts'])

    def test_sync_cannot_overwrite_manual_link_or_reading(self):
        payload=self.exporter();zotero.sync(self.root,self.project,wf)
        file=self.base/'papers/MockSurvey2025/meta.yaml';data=wf.load(file)
        target=next(link['target'] for link in data['links'] if link.get('generated_by')=='wf-zotero')
        data['links']=[link for link in data['links'] if link.get('target')!=target]
        manual=dict(rel='belongs-to-topic',target=target,status='verified',confidence='high',
                    evidence=[dict(file='research-profile.yaml',field='direction',source_refs=[])],reviewed_by='human')
        data['links'].append(manual);wf.save(file,data)
        reading=self.base/'papers/MockSurvey2025/03_reading/reading.md'
        storage.write_text(reading,reading.read_text(encoding='utf-8')+'\n人工精读材料\n');original=reading.read_bytes()
        self.exporter(payload);zotero.sync(self.root,self.project,wf)
        self.assertEqual(reading.read_bytes(),original)
        saved=next(link for link in wf.load(file)['links'] if link.get('target')==target and not link.get('generated_by'))
        for key,value in manual.items():self.assertEqual(saved[key],value)

    def test_explicit_verified_link_expires_when_evidence_file_changes(self):
        _,card=self.graph_fixture();file=self.base/'papers/alpha/meta.yaml';data=wf.load(file)
        link=next(link for link in data['links'] if link['rel']=='uses' and link['target']=='concept:base')
        link.update(status='verified',reviewed_by='main',review_note='核验了概念证据')
        wf.save(file,data);wf.graph(self.root,'research')
        info,body=literature.markdown(card);literature.write_markdown(card,info,body+'\n概念定义发生变化\n')
        graph=wf.graph(self.root,'research')
        source=next(link for link in wf.load(file)['links'] if link['rel']=='uses' and link['target']=='concept:base')
        self.assertEqual(source['status'],'candidate');self.assertTrue(source['review_invalidated'])
        self.assertTrue(source['audit']);self.assertEqual(source['review_note'],'核验了概念证据')


if __name__=='__main__':unittest.main()
