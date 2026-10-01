"""评审与增量返修的独立离线回归；仅复制公开配置和模板。"""
import contextlib
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import registry, tasks, wf


class TaskReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='paper-review-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        for name in ('models.example.yaml', 'models.local.yaml'):
            shutil.copyfile(wf.ROOT / 'config/models.example.yaml', self.root / 'config' / name)
        shutil.copytree(wf.ROOT / 'workflow', self.root / 'workflow', ignore=shutil.ignore_patterns('vendor'))
        self.silent = contextlib.redirect_stdout(io.StringIO())
        self.silent.__enter__()
        self.addCleanup(self.silent.__exit__, None, None, None)
        self.project = wf.init(self.root, 'review-unit', 'Offline fixture')
        self.paper = wf.new_paper(self.root, self.project.name, 'Example2026')
        self.source = self.paper / '01_source/input.md'
        self.source.write_text('# Scope\nSOURCE_FIXTURE\n# Other\nUNRELATED_SOURCE\n', encoding='utf-8')
        meta = wf.load(self.paper / 'meta.yaml')
        meta['source_files'] = [self.source.relative_to(self.project).as_posix()]
        wf.save(self.paper / 'meta.yaml', meta)
        wf.index(self.root, self.project.name)
        self.source_id = next(key for key, value in registry.load_index(self.project)['artifacts'].items()
                              if value['path'] == self.source.relative_to(self.project).as_posix())

    def prepare(self, kind='verification'):
        self.identifier = 'fixture-review'
        task = dict(task_id=self.identifier, task_type=kind, objective='Review supplied fixture only',
                    inputs=[{'id': 'paper:Example2026'}, {'id': self.source_id, 'anchor': 'Scope'}],
                    allowed_paths=[self.paper.relative_to(self.project).as_posix()] if kind == 'literature-first-pass' else ['30_outputs'],
                    context={})
        wf.save(self.root / 'task.yaml', task)
        tasks.execute(self.root, self.project, 'task.yaml', wf)
        self.folder = self.project / '.runs' / self.identifier
        return wf.load(self.folder / 'task.yaml')

    def payload(self, normalized, artifacts, attempt=1):
        return {'result': dict(task_id=self.identifier, attempt=attempt, status='submitted', summary='Fixture summary',
                               created_artifacts=[], updated_artifacts=[],
                               evidence=[{'id': self.source_id, 'anchor': 'Scope'}], unresolved_issues=[], confidence='low',
                               self_check={key: 'unknown' for key in normalized['acceptance_criteria']}),
                'artifacts': artifacts}

    def submit_report(self):
        normalized = self.prepare()
        content = '# Fixture report\n\nNot a scientific acceptance.\n'
        output = normalized['outputs'][0]
        tasks.submit(self.root, self.project, self.identifier, 1,
                     self.payload(normalized, [dict(id=output['id'], type='artifact', content=content, mode='replace')]), wf)
        return normalized

    def decision(self, normalized, revise=False):
        criteria = normalized['acceptance_criteria']
        result = dict(task_id=self.identifier, attempt=1, reviewer='main', decision='revise' if revise else 'accept',
                      passed_criteria=criteria[1:] if revise else criteria,
                      failed_criteria=criteria[:1] if revise else [], issues=[], required_changes=[],
                      evidence_checks=[{'ref': {'id': self.source_id, 'anchor': 'Scope'}, 'status': 'verified'}],
                      next_action='repair' if revise else 'apply', reason='Explicit offline fixture reviewer')
        if revise:
            result['issues'] = [{'criterion': criteria[0], 'description': 'Repair reading draft'}]
            result['required_changes'] = [{'criterion': criteria[0], 'description': 'Repair this output only',
                                          'artifact_id': 'reading:Example2026'}]
        return result

    def failed_subagent_revision(self):
        normalized = self.submit_report()
        review = self.decision(normalized, revise=True)
        review['required_changes'][0]['artifact_id'] = normalized['outputs'][0]['id']
        wf.save(self.root/'review.yaml', review)
        tasks.revise(self.root,self.project,self.identifier,1,'review.yaml',wf)
        tasks.execute(self.root,self.project,'task.yaml',wf)
        tasks.submit(self.root,self.project,self.identifier,2,
            self.payload(normalized,[dict(id=normalized['outputs'][0]['id'],type='artifact',content='# Fixture repair\n\nFailed child repair fixture.\n')],attempt=2),wf)
        review['attempt'] = 2
        wf.save(self.root/'review.yaml',review)
        return normalized, review

    def test_failed_child_revision_automatically_starts_main_session_handoff(self):
        normalized, _ = self.failed_subagent_revision()
        directory = tasks.revise(self.root,self.project,self.identifier,2,'review.yaml',wf)
        status = tasks.state(self.root,self.project,self.identifier,wf)
        self.assertEqual(status['attempt'],3)
        self.assertEqual(status['execution_target'],'main')
        self.assertEqual(status['main_attempts'],1)
        self.assertEqual(registry.load_index(self.project)['tasks']['task:'+self.identifier]['execution_target'],'main')
        self.assertEqual(status['status'],'waiting-manual')
        execution = wf.load(self.folder/'attempts/3/execution.yaml')
        self.assertEqual(execution['effective_role'],'orchestrator')
        self.assertEqual(execution['requested_profile'],'main')
        self.assertEqual(execution['execution_kind'],'main-repair')
        self.assertIn('子模型返修',execution['takeover_reason'])
        content = (directory/'context.md').read_text(encoding='utf-8')
        self.assertIn('Failed child repair fixture.',content)
        self.assertNotIn('UNRELATED_SOURCE',content)
        self.assertFalse((self.project/normalized['outputs'][0]['path']).exists())

    def test_main_api_repair_uses_configured_main_and_remains_draft_until_accept(self):
        normalized, _ = self.failed_subagent_revision()
        config = wf.load(self.root/'config/models.example.yaml')
        config['orchestrator'] = dict(profile='my-main')
        config['model_profiles']['my-main'] = dict(adapter='command',command=['python','-c','pass'],timeout_seconds=30)
        payload = self.payload(normalized,[dict(id=normalized['outputs'][0]['id'],type='artifact',content='# Main repaired fixture\n\nMain repair draft.\n')],attempt=3)
        with patch('tools.tasks.adapters.execute',return_value=('draft',tasks.dump(payload))) as call:
            tasks.revise(self.root,self.project,self.identifier,2,'review.yaml',wf,True,config)
        settings, prompt, _, execute_external = call.call_args.args
        self.assertEqual(settings['profile'],'my-main')
        self.assertTrue(execute_external)
        self.assertIn('当前职责：主模型接手返修',prompt)
        self.assertEqual(tasks.state(self.root,self.project,self.identifier,wf)['status'],'submitted')
        self.assertEqual(wf.load(self.folder/'attempts/3/result.yaml')['generated_by'],'main')
        self.assertEqual(wf.load(self.folder/'attempts/3/result.yaml')['model_role'],'orchestrator')
        self.assertFalse((self.project/normalized['outputs'][0]['path']).exists())
        review = self.decision(normalized);review['attempt']=3
        tasks.record_review(self.root,self.project,self.identifier,3,review,wf)
        tasks.accept(self.root,self.project,self.identifier,3,wf)
        self.assertIn('Main repair draft.',(self.project/normalized['outputs'][0]['path']).read_text(encoding='utf-8'))

    def test_main_repair_without_execute_keeps_external_calls_in_dry_run(self):
        self.failed_subagent_revision()
        config = wf.load(self.root/'config/models.example.yaml')
        config['orchestrator'] = dict(profile='my-main')
        config['model_profiles']['my-main'] = dict(adapter='command',command=['python','-c','pass'],timeout_seconds=30)
        with patch('tools.tasks.adapters.execute',return_value=('dry-run',None)) as call:
            tasks.revise(self.root,self.project,self.identifier,2,'review.yaml',wf,config_override=config)
        self.assertFalse(call.call_args.args[3])
        self.assertEqual(tasks.state(self.root,self.project,self.identifier,wf)['status'],'dry-run')

    def test_main_repair_failure_has_bounded_attempts(self):
        normalized, review = self.failed_subagent_revision()
        tasks.revise(self.root,self.project,self.identifier,2,'review.yaml',wf)
        tasks.submit(self.root,self.project,self.identifier,3,
            self.payload(normalized,[dict(id=normalized['outputs'][0]['id'],type='artifact',content='# Still unresolved\n\nFixture only.\n')],attempt=3),wf)
        review['attempt'] = 3
        wf.save(self.root/'review.yaml',review)
        with patch('tools.tasks.adapters.execute') as call:
            self.assertIsNone(tasks.revise(self.root,self.project,self.identifier,3,'review.yaml',wf))
            call.assert_not_called()
        status = tasks.state(self.root,self.project,self.identifier,wf)
        self.assertEqual(status['status'],'blocked')
        self.assertIn('主模型返修',status['reason'])

    def test_retry_main_handoff_keeps_repair_context_and_main_profile(self):
        self.failed_subagent_revision()
        directory=tasks.revise(self.root,self.project,self.identifier,2,'review.yaml',wf)
        before=(directory/'context.md').read_bytes()
        with patch('tools.tasks.adapters.execute',return_value=('waiting-manual',None)) as call:
            target=tasks.execute(self.root,self.project,'task.yaml',wf)
        self.assertEqual(target.name,'3')
        self.assertEqual(call.call_args.args[0]['profile'],'main')
        self.assertIn('Failed child repair fixture.',call.call_args.args[1])
        self.assertEqual(before,(directory/'context.md').read_bytes())
        self.assertEqual(tasks.state(self.root,self.project,self.identifier,wf)['main_attempts'],1)

    def test_changed_original_source_blocks_main_repair_before_model_call(self):
        self.failed_subagent_revision()
        self.source.write_text('# Scope\nCHANGED\n',encoding='utf-8')
        with patch('tools.tasks.adapters.execute') as call:
            with self.assertRaisesRegex(ValueError,'hash'):
                tasks.revise(self.root,self.project,self.identifier,2,'review.yaml',wf)
            call.assert_not_called()

    def test_subagent_attempt_limit_also_starts_main_repair(self):
        book = wf.load(self.root/'workflow/task-contracts.yaml')
        book['tasks']['verification']['max_attempts'] = 1
        wf.save(self.root/'workflow/task-contracts.yaml',book)
        normalized = self.submit_report()
        review = self.decision(normalized,revise=True)
        review['required_changes'][0]['artifact_id']=normalized['outputs'][0]['id']
        wf.save(self.root/'review.yaml',review)
        tasks.revise(self.root,self.project,self.identifier,1,'review.yaml',wf)
        status=tasks.state(self.root,self.project,self.identifier,wf)
        self.assertEqual(status['execution_target'],'main')
        self.assertEqual(status['attempt'],2)
        self.assertIn('子模型已达尝试上限',status['takeover_reason'])

    def test_contract_changed_after_submission_cannot_be_reviewed(self):
        self.submit_report()
        book = wf.load(self.root / 'workflow/task-contracts.yaml')
        book['tasks']['verification']['acceptance'].append('additional_required_check')
        wf.save(self.root / 'workflow/task-contracts.yaml', book)
        with self.assertRaisesRegex(ValueError, '合同'):
            tasks.review_bundle(self.root, self.project, self.identifier, 1, wf)
        self.assertFalse((self.project / '30_outputs/fixture-review-verification.md').exists())

    def test_output_ref_cannot_disguise_paper_metadata_as_report(self):
        task = dict(task_id='wrong-output', task_type='verification', objective='Explicit wrong-output fixture',
                    inputs=[{'id': 'paper:Example2026'}], outputs=[{'id': 'paper:Example2026', 'type': 'artifact'}],
                    allowed_paths=[self.paper.relative_to(self.project).as_posix()], context={})
        wf.save(self.root / 'wrong-task.yaml', task)
        with patch('tools.tasks.adapters.execute') as external:
            with self.assertRaises(ValueError):
                tasks.execute(self.root, self.project, 'wrong-task.yaml', wf)
            external.assert_not_called()
        self.assertFalse((self.project / '.runs/wrong-output').exists())

    def test_contract_changed_after_main_review_cannot_be_applied(self):
        normalized = self.submit_report()
        tasks.record_review(self.root, self.project, self.identifier, 1, self.decision(normalized), wf)
        book = wf.load(self.root / 'workflow/task-contracts.yaml')
        book['tasks']['verification']['acceptance'].append('additional_required_check')
        wf.save(self.root / 'workflow/task-contracts.yaml', book)
        with self.assertRaisesRegex(ValueError, '合同'):
            tasks.accept(self.root, self.project, self.identifier, 1, wf)
        self.assertEqual(tasks.state(self.root, self.project, self.identifier, wf)['status'], 'reviewed')

    def test_api_accept_without_supplied_evidence_stays_manual(self):
        normalized = self.submit_report()
        response = tasks.dump(self.decision(normalized))
        with patch('tools.tasks.adapters.execute', return_value=('draft', response)) as external:
            directory = tasks.review(self.root, self.project, self.identifier, 1, wf, execute_external=True)
        external.assert_called_once()
        self.assertFalse((self.folder / 'reviews/1.yaml').exists())
        self.assertEqual(wf.load(directory / 'execution.yaml')['status'], 'waiting-manual')
        self.assertEqual((directory / 'response.md').read_text(encoding='utf-8'), response)

    def test_unstructured_api_review_is_retained_for_manual_review(self):
        self.submit_report()
        response = 'Review draft without the requested structured YAML.'
        with patch('tools.tasks.adapters.execute', return_value=('draft', response)):
            directory = tasks.review(self.root, self.project, self.identifier, 1, wf, execute_external=True)
        self.assertEqual(wf.load(directory / 'execution.yaml')['status'], 'waiting-manual')
        self.assertEqual((directory / 'response.md').read_text(encoding='utf-8'), response)
        self.assertFalse((self.folder / 'reviews/1.yaml').exists())

    def test_multi_output_revision_keeps_untouched_draft_without_resending_it(self):
        normalized = self.prepare('literature-first-pass')
        analysis = wf.load(self.paper / '04_analysis/analysis.yaml')
        analysis['overview']['object'] = 'UNCHANGED_ANALYSIS_DRAFT'
        artifacts = [dict(id='reading:Example2026', type='reading', content='# Draft reading\n\nREADING_DRAFT\n'),
                     dict(id='analysis:Example2026', type='analysis', content=tasks.dump(analysis))]
        tasks.submit(self.root, self.project, self.identifier, 1, self.payload(normalized, artifacts), wf)
        previous = wf.load(self.folder / 'attempts/1/artifact-index.yaml')['artifacts']
        previous_analysis = next(item for item in previous if item['target_id'] == 'analysis:Example2026')
        previous_bytes = (self.project / previous_analysis['path']).read_bytes()
        wf.save(self.root / 'review.yaml', self.decision(normalized, revise=True))
        directory = tasks.revise(self.root, self.project, self.identifier, 1, 'review.yaml', wf)
        context = (directory / 'context.md').read_text(encoding='utf-8')
        self.assertIn('READING_DRAFT', context)
        self.assertNotIn('UNCHANGED_ANALYSIS_DRAFT', context)
        self.assertNotIn('SOURCE_FIXTURE', context)
        tasks.execute(self.root, self.project, 'task.yaml', wf)
        artifacts = [dict(id='reading:Example2026', type='reading', content='# Draft reading\n\nREVISED_READING_DRAFT\n')]
        tasks.submit(self.root, self.project, self.identifier, 2, self.payload(normalized, artifacts, attempt=2), wf)
        current = wf.load(self.folder / 'attempts/2/artifact-index.yaml')['artifacts']
        self.assertEqual({item['target_id'] for item in current}, {'reading:Example2026', 'analysis:Example2026'})
        current_analysis = next(item for item in current if item['target_id'] == 'analysis:Example2026')
        self.assertEqual((self.project / current_analysis['path']).read_bytes(), previous_bytes)
        self.assertNotIn('UNCHANGED_ANALYSIS_DRAFT', (self.paper / '04_analysis/analysis.yaml').read_text(encoding='utf-8'))

    def test_review_bundle_contains_target_ref_and_candidate_link_changes(self):
        normalized = self.prepare()
        output = normalized['outputs'][0]
        header = dict(id=output['id'], links=[dict(rel='generated-from', target='paper:Example2026',
                      evidence=[{'id': self.source_id, 'anchor': 'Scope'}], confidence='low', status='candidate')])
        content = '---\n' + tasks.dump(header) + '---\n\n# Draft report\n\nFixture link proposal.\n'
        tasks.submit(self.root, self.project, self.identifier, 1,
                     self.payload(normalized, [dict(id=output['id'], type='artifact', content=content)]), wf)
        directory = tasks.review_bundle(self.root, self.project, self.identifier, 1, wf)
        bundle = wf.load(directory / 'links.yaml')
        self.assertEqual(len(bundle['links']), 1)
        self.assertEqual(bundle['links'][0]['source'], output['id'])
        self.assertEqual(bundle['links'][0]['target'], 'paper:Example2026')
        self.assertEqual(bundle['links'][0]['status'], 'candidate')
        report = (directory / 'review-bundle.md').read_text(encoding='utf-8')
        self.assertIn('target_ref:', report)
        self.assertIn('30_outputs/fixture-review-verification.md', report)
        self.assertNotIn('SOURCE_FIXTURE', report)

    def test_accepted_generic_artifact_links_enter_index_and_graph(self):
        normalized = self.prepare()
        output = normalized['outputs'][0]
        link = dict(rel='uses', target='paper:Example2026', evidence=[{'id': self.source_id, 'anchor': 'Scope'}],
                    confidence='low', status='candidate')
        content = '---\n' + tasks.dump(dict(id=output['id'], links=[link])) + '---\n\n# Artifact draft\n\nFixture link.\n'
        tasks.submit(self.root, self.project, self.identifier, 1,
                     self.payload(normalized, [dict(id=output['id'], type='artifact', content=content)]), wf)
        tasks.record_review(self.root, self.project, self.identifier, 1, self.decision(normalized), wf)
        tasks.accept(self.root, self.project, self.identifier, 1, wf)
        index = registry.load_index(self.project)
        self.assertTrue(any(item['source'] == output['id'] and item['target'] == 'paper:Example2026'
                            for item in index['links']))
        import json
        graph = json.loads((self.project / '10_literature/knowledge-graph.json').read_text(encoding='utf-8'))
        self.assertTrue(any(item['source'] == output['id'] and item['target'] == 'paper:Example2026'
                            and item['status'] == 'candidate' for item in graph['edges']))

    def test_reproduction_context_can_select_embedded_formula_principle_and_concept(self):
        analysis = wf.load(self.paper / '04_analysis/analysis.yaml')
        analysis['overview']['object'] = 'UNRELATED_ANALYSIS_OVERVIEW'
        analysis['formulas'] = [dict(id='eq-1', label='Eq. 1', latex='x=1', name_zh='fixture formula',
            plain_meaning='FORMULA_FIXTURE', symbols=[], assumptions=[], derivation_steps=[], intuition='fixture',
            special_cases=[], related_concepts=[], source_refs=[self.source.relative_to(self.project).as_posix()], confidence='low')]
        analysis['first_principles'] = [dict(id='fixture-principle', statement='PRINCIPLE_FIXTURE',
            source_refs=[self.source.relative_to(self.project).as_posix()], concept_ids=[])]
        wf.save(self.paper / '04_analysis/analysis.yaml', analysis)
        wf.new_concept(self.root, self.project.name, 'fixture-concept')
        claim = wf.new_claim(self.root, self.project.name, 'Example2026', 'main-result')
        wf.index(self.root, self.project.name)
        index = registry.load_index(self.project)
        claim_id = next(key for key, value in index['artifacts'].items() if value['type'] == 'claim')
        formula_id = next(key for key, value in index['artifacts'].items() if value['type'] == 'formula')
        principle_id = next(key for key, value in index['artifacts'].items() if value['type'] == 'principle')
        inputs = [{'id': claim_id}, {'id': 'artifact:review-unit:research-profile'}, {'id': formula_id},
                  {'id': principle_id}, {'id': 'concept:fixture-concept'}]
        task = dict(task_id='repro-context', task_type='repro-feasibility', objective='Read explicit fixture objects',
                    inputs=inputs, allowed_paths=[claim.relative_to(self.project).as_posix()], context={})
        tasks.prepare(self.root, self.project, task, wf)
        directory = tasks.context(self.root, self.project, 'repro-context', wf)
        context = (directory / 'context.md').read_text(encoding='utf-8')
        self.assertIn('FORMULA_FIXTURE', context)
        self.assertIn('PRINCIPLE_FIXTURE', context)
        self.assertNotIn('UNRELATED_ANALYSIS_OVERVIEW', context)


if __name__ == '__main__':
    unittest.main()
