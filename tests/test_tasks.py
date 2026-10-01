"""闭环在隔离目录验证；只用 mock/人工 fixture，无真实网络与密钥。"""
import copy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tools import wf, tasks, registry, literature


class TaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in ('config', 'workflow'):
            shutil.copytree(wf.ROOT / rel, self.root / rel)
        shutil.copyfile(self.root/'config/models.example.yaml', self.root/'config/models.local.yaml')
        self.project = wf.init(self.root, 'unit', 'fixture')
        self.paper = wf.new_paper(self.root, 'unit', 'Sample2026')
        self.source = self.paper / '01_source/input.md'
        self.source.write_text('# Selected\nONLY_SELECTED\n# Unrelated\nWHOLE_PAPER_SECRET\n', encoding='utf-8')
        self.meta = wf.load(self.paper/'meta.yaml')
        self.meta['source_files'] = [self.source.relative_to(self.project).as_posix()]
        wf.save(self.paper/'meta.yaml', self.meta)
        wf.index(self.root, 'unit')
        self.source_id = next(k for k,v in registry.load_index(self.project)['artifacts'].items() if v['path']==self.source.relative_to(self.project).as_posix())

    def task(self, identifier='check', kind='verification', inputs=None):
        data = dict(task_id=identifier, task_type=kind, objective='Check explicit fixture',
                    inputs=inputs or [{'id':'paper:Sample2026'}, {'id':self.source_id, 'anchor':'Selected'}],
                    allowed_paths=['30_outputs'], context={}, source_refs=[])
        wf.save(self.root/'task.yaml', data)
        return data

    def execute(self, identifier='check'):
        self.task(identifier)
        return tasks.execute(self.root, self.project, 'task.yaml', wf)

    def payload(self, identifier='check', attempt=1, content=None):
        task = wf.load(self.project/'.runs'/identifier/'task.yaml')
        return {'result':dict(task_id=identifier,attempt=attempt,status='submitted',summary='Fixture summary',
                    created_artifacts=[],updated_artifacts=[],evidence=[{'id':self.source_id,'anchor':'Selected'}],
                    unresolved_issues=[],confidence='low',self_check={x:'passed' for x in task['acceptance_criteria']}),
                'artifacts':[dict(id=task['outputs'][0]['id'],type='artifact',content=content or '# Verification fixture\n\nVerified fixture only.\n',mode='replace')]}

    def submit(self, identifier='check', attempt=1):
        return tasks.submit(self.root,self.project,identifier,attempt,self.payload(identifier,attempt),wf)

    def decision(self, identifier='check', attempt=1, decision='accept'):
        task=wf.load(self.project/'.runs'/identifier/'task.yaml')
        criteria=task['acceptance_criteria']
        review=dict(task_id=identifier,attempt=attempt,reviewer='main',decision=decision,
                    passed_criteria=criteria if decision=='accept' else criteria[1:],
                    failed_criteria=[] if decision=='accept' else criteria[:1],issues=[],required_changes=[],
                    evidence_checks=[{'ref':{'id':self.source_id,'anchor':'Selected'},'status':'verified'}],
                    next_action='apply' if decision=='accept' else 'repair',reason='Fixture review by manual main')
        if decision=='revise':
            review['issues']=[{'criterion':criteria[0],'description':'Repair fixture source attribution'}]
            review['required_changes']=[{'criterion':criteria[0],'description':'Keep source anchor explicit','artifact_id':task['outputs'][0]['id']}]
        return review

    def test_contract_missing_input_blocks_before_dispatch(self):
        self.task(kind='literature-extract',inputs=[{'id':'paper:Sample2026'}])
        with patch('tools.tasks.adapters.execute') as call:
            with self.assertRaisesRegex(ValueError,'缺少输入'):
                tasks.execute(self.root,self.project,'task.yaml',wf)
            call.assert_not_called()
        self.assertFalse((self.project/'.runs/check').exists())

    def test_missing_contract_and_acceptance_block(self):
        self.task(kind='imaginary')
        with self.assertRaisesRegex(ValueError,'合同'):
            tasks.execute(self.root,self.project,'task.yaml',wf)
        self.task()
        book=wf.load(self.root/'workflow/task-contracts.yaml')
        book['tasks']['verification']['acceptance']=[]
        wf.save(self.root/'workflow/task-contracts.yaml',book)
        with self.assertRaisesRegex(ValueError,'验收标准'):
            tasks.execute(self.root,self.project,'task.yaml',wf)

    def test_minimal_anchored_context_and_cache(self):
        data=self.task()
        tasks.prepare(self.root,self.project,data,wf)
        directory=tasks.context(self.root,self.project,'check',wf)
        body=(directory/'context.md').read_text(encoding='utf-8')
        self.assertIn('ONLY_SELECTED',body)
        self.assertNotIn('WHOLE_PAPER_SECRET',body)
        before={f.name:f.read_bytes() for f in directory.iterdir() if f.is_file()}
        tasks.context(self.root,self.project,'check',wf)
        self.assertEqual(before,{f.name:f.read_bytes() for f in directory.iterdir() if f.is_file()})

    def test_context_hash_change_blocks(self):
        data=self.task();tasks.prepare(self.root,self.project,data,wf)
        self.source.write_text('changed input',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash'):
            tasks.context(self.root,self.project,'check',wf)

    def test_context_large_file_is_reference_only(self):
        self.source.write_text('z'*300000,encoding='utf-8');wf.index(self.root,'unit')
        data=self.task(inputs=[{'id':self.source_id}]);tasks.prepare(self.root,self.project,data,wf)
        directory=tasks.context(self.root,self.project,'check',wf)
        self.assertIn('large-file-reference-only',(directory/'context.md').read_text(encoding='utf-8'))
        self.assertLess((directory/'context.md').stat().st_size,10000)

    def test_manual_execution_no_key_is_not_submitted(self):
        directory=self.execute()
        self.assertEqual(tasks.state(self.root,self.project,'check',wf)['status'],'waiting-manual')
        for name in ('prompt.md','response.md','result.yaml','artifact-index.yaml','self-check.md'):
            self.assertTrue((directory/name).is_file())
        self.assertEqual(wf.load(directory/'result.yaml')['status'],'pending')

    def test_submitted_artifacts_registered_but_not_official(self):
        self.execute();result=self.submit()
        self.assertEqual(result['status'],'submitted')
        for ref in result['created_artifacts']:
            self.assertEqual(registry.resolve(self.project,ref,wf)['id'],ref['id'])
        self.assertFalse((self.project/'30_outputs/check-verification.md').exists())
        self.assertEqual(tasks.state(self.root,self.project,'check',wf)['status'],'submitted')

    def test_review_bundle_minimal_and_all_outputs_resolve(self):
        self.execute();self.submit()
        directory=tasks.review_bundle(self.root,self.project,'check',1,wf)
        body=(directory/'review-bundle.md').read_text(encoding='utf-8')
        self.assertIn('Fixture summary',body)
        self.assertNotIn('ONLY_SELECTED',body)
        self.assertNotIn('WHOLE_PAPER_SECRET',body)
        self.assertNotIn('Verified fixture only.',body)
        self.assertTrue((directory/'evidence.yaml').exists())

    def test_accept_requires_explicit_main_all_criteria(self):
        self.execute();self.submit();tasks.review_bundle(self.root,self.project,'check',1,wf)
        with self.assertRaises((ValueError,FileNotFoundError)):
            tasks.accept(self.root,self.project,'check',1,wf)
        bad=self.decision();bad['passed_criteria']=[]
        with self.assertRaisesRegex(ValueError,'全部标准'):
            tasks.record_review(self.root,self.project,'check',1,bad,wf)

    def test_accept_updates_index_graph_and_is_idempotent(self):
        self.execute();self.submit()
        tasks.record_review(self.root,self.project,'check',1,self.decision(),wf)
        tasks.accept(self.root,self.project,'check',1,wf)
        index=registry.load_index(self.project)
        self.assertEqual(index['tasks']['task:check']['status'],'accepted')
        self.assertTrue(registry.resolve(self.project,'artifact:check:verification',wf)['path'].startswith('30_outputs/'))
        import json
        graph=json.loads((self.project/'10_literature/knowledge-graph.json').read_text(encoding='utf-8'))
        self.assertIn('task:check',{n['id'] for n in graph['nodes']})
        self.assertTrue(all(e['source'] in index['artifacts'] and e['target'] in index['artifacts'] for e in graph['edges']))
        first=(self.project/'30_outputs/check-verification.md').read_bytes()
        tasks.accept(self.root,self.project,'check',1,wf)
        self.assertEqual(first,(self.project/'30_outputs/check-verification.md').read_bytes())

    def test_accept_rejects_changed_source(self):
        self.execute();self.submit();tasks.record_review(self.root,self.project,'check',1,self.decision(),wf)
        self.source.write_text('# Selected\nchanged\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash'):
            tasks.accept(self.root,self.project,'check',1,wf)
        self.assertFalse((self.project/'30_outputs/check-verification.md').exists())

    def test_accept_preserves_manual_target_after_submit(self):
        self.execute();self.submit();tasks.record_review(self.root,self.project,'check',1,self.decision(),wf)
        path=self.project/'30_outputs/check-verification.md';path.write_text('MANUAL_KEEP',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'变化'):
            tasks.accept(self.root,self.project,'check',1,wf)
        self.assertEqual(path.read_text(),'MANUAL_KEEP')

    def test_revision_only_issues_and_relevant_draft(self):
        self.execute();self.submit();review=self.decision(decision='revise')
        wf.save(self.root/'review.yaml',review)
        directory=tasks.revise(self.root,self.project,'check',1,'review.yaml',wf)
        body=(directory/'context.md').read_text(encoding='utf-8')
        self.assertIn('Repair fixture source attribution',body)
        self.assertIn('Verified fixture only.',body)
        self.assertNotIn('ONLY_SELECTED',body)
        self.assertNotIn('WHOLE_PAPER_SECRET',body)

    def test_revision_subjective_without_criterion_is_rejected(self):
        self.execute();self.submit();review=self.decision(decision='revise');review['issues']=[{'description':'not elegant'}]
        with self.assertRaisesRegex(ValueError,'criterion'):
            tasks.record_review(self.root,self.project,'check',1,review,wf)

    def test_revision_stops_at_max_attempts(self):
        self.execute()
        for attempt in range(1,4):
            self.submit(attempt=attempt);review=self.decision(attempt=attempt,decision='revise')
            wf.save(self.root/'review.yaml',review)
            directory=tasks.revise(self.root,self.project,'check',attempt,'review.yaml',wf)
            if attempt<3:
                self.assertIsNotNone(directory)
                tasks.execute(self.root,self.project,'task.yaml',wf)
        self.assertIsNone(directory)
        self.assertEqual(tasks.state(self.root,self.project,'check',wf)['status'],'blocked')

    def test_result_wrong_identity_cannot_register(self):
        self.execute();payload=self.payload();payload['artifacts'][0]['id']='artifact:invented'
        with self.assertRaisesRegex(ValueError,'合同输出'):
            tasks.submit(self.root,self.project,'check',1,payload,wf)
        self.assertNotIn('artifact:invented',registry.load_index(self.project)['artifacts'])

    def test_external_failure_is_private_manual_fallback(self):
        self.task()
        with patch('tools.tasks.adapters.execute',side_effect=RuntimeError('DO_NOT_LOG_SECRET')):
            directory=tasks.execute(self.root,self.project,'task.yaml',wf,True)
        execution=wf.load(directory/'execution.yaml')
        self.assertEqual(execution['adapter'],'manual')
        self.assertNotIn('DO_NOT_LOG_SECRET',(directory/'execution.yaml').read_text())

    def test_cli_all_task_commands(self):
        self.task()
        with patch.object(wf,'ROOT',self.root):
            self.assertEqual(wf.main(['validate','--contracts']),0)
            self.assertEqual(wf.main(['index','unit','--json']),0)
            self.assertEqual(wf.main(['task','run','unit','task.yaml']),0)
            self.assertEqual(wf.main(['context','unit','check']),0)
            self.assertEqual(wf.main(['task','status','unit','check']),0)
            wf.save(self.root/'result.yaml',self.payload())
            self.assertEqual(wf.main(['task','submit','unit','check','--attempt','1','--result','result.yaml']),0)
            self.assertEqual(wf.main(['task','review','unit','check','--attempt','1']),0)
            wf.save(self.root/'review.yaml',self.decision())
            self.assertEqual(wf.main(['task','review','unit','check','--attempt','1','--review','review.yaml']),0)
            self.assertEqual(wf.main(['task','accept','unit','check','--attempt','1']),0)
            self.assertEqual(wf.main(['validate','--links','unit']),0)

    def test_nested_formula_context_extracts_one_node(self):
        text='formulas:\n- {id: a, meaning: SELECTED}\n- {id: b, meaning: OMITTED}\n'
        selected=tasks.select_anchor(text,'formulas[0]')
        self.assertIn('SELECTED',selected);self.assertNotIn('OMITTED',selected)

    def test_accept_failure_rolls_back_formal_files_state_and_index(self):
        self.execute();self.submit();tasks.record_review(self.root,self.project,'check',1,self.decision(),wf)
        paths=[self.project/'project.yaml',self.project/'INDEX.json',self.project/'.runs/check/status.yaml',self.project/'10_literature/knowledge-graph.json']
        before={path:path.read_bytes() for path in paths}
        with patch.object(wf,'index',side_effect=OSError('fixture graph failure')):
            with self.assertRaises(OSError):tasks.accept(self.root,self.project,'check',1,wf)
        for path,content in before.items():self.assertEqual(path.read_bytes(),content)
        self.assertFalse((self.project/'30_outputs/check-verification.md').exists())
        self.assertFalse((self.project/'.runs/check/final/acceptance.yaml').exists())

    def test_core_object_cannot_be_overwritten_as_arbitrary_artifact(self):
        task=self.task();task['allowed_paths']=['.']
        task['outputs']=[{'id':'artifact:check:verification','type':'artifact','path':'project.yaml'}]
        wf.save(self.root/'task.yaml',task)
        original=(self.project/'project.yaml').read_bytes()
        with self.assertRaisesRegex(ValueError,'核心对象'):
            tasks.execute(self.root,self.project,'task.yaml',wf)
        self.assertEqual(original,(self.project/'project.yaml').read_bytes())

    def test_generic_artifact_dangling_links_cannot_be_accepted(self):
        self.execute();payload=self.payload(content='---\nid: artifact:check:verification\nlinks:\n- {rel: uses, target: concept:missing, evidence: [{id: paper:Sample2026}], confidence: low, status: candidate}\n---\n\n# Fixture\n')
        tasks.submit(self.root,self.project,'check',1,payload,wf)
        tasks.record_review(self.root,self.project,'check',1,self.decision(),wf)
        with self.assertRaisesRegex(ValueError,'悬空'):
            tasks.accept(self.root,self.project,'check',1,wf)
        self.assertFalse((self.project/'30_outputs/check-verification.md').exists())


if __name__=='__main__':
    unittest.main()
