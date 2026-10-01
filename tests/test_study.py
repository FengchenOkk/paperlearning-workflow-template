"""通读交付、最小输入和全文翻译覆盖的离线回归；不读取个人配置或调用API。"""
import contextlib
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import wf, study, tasks, registry, literature

class StudyTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        shutil.copytree(wf.ROOT/'workflow/layouts',self.root/'workflow/layouts')
        shutil.copytree(wf.ROOT/'workflow/prompts',self.root/'workflow/prompts')
        for name in ['README.md','schemas.yaml','task-contracts.yaml']:
            shutil.copyfile(wf.ROOT/'workflow'/name,self.root/'workflow'/name)
        (self.root/'config').mkdir()
        shutil.copyfile(wf.ROOT/'.env.example',self.root/'.env.example')
        shutil.copyfile(wf.ROOT/'.gitignore',self.root/'.gitignore')
        for name in ['models','zotero']:
            shutil.copyfile(wf.ROOT/f'config/{name}.example.yaml',self.root/f'config/{name}.example.yaml')
        with contextlib.redirect_stdout(io.StringIO()):
            wf.bootstrap(self.root);self.p=wf.init(self.root,'study','offline fixture')
            self.paper=wf.new_paper(self.root,'study','Sample2026')
        self.source=self.paper/'01_source/source.md'
        self.source.write_text('# Source\n\n' + ('Paragraph with explicit text and [1].\n'*33),encoding='utf-8')
        meta=wf.load(self.paper/'meta.yaml');meta['source_files']=[self.source.relative_to(self.p).as_posix()]
        wf.save(self.paper/'meta.yaml',meta)
        a=wf.load(self.paper/'04_analysis/analysis.yaml')
        a['overview'].update(object='fixture',core_problem='fixture',why_important='fixture',position='fixture')
        wf.save(self.paper/'04_analysis/analysis.yaml',a)
        path=self.paper/'03_reading/reading.md'
        path.write_text(path.read_text(encoding='utf-8').replace('TODO(user)','Fixture'),encoding='utf-8')
        wf.index(self.root,'study')

    def snapshot(self):
        return {f.relative_to(self.root).as_posix():f.read_bytes() for f in self.root.rglob('*') if f.is_file()}

    def start(self, packet):
        path=self.p/'00_inbox/current.yaml';wf.save(path,packet)
        tasks.execute(self.root,self.p,path.relative_to(self.root).as_posix(),wf)
        return wf.load(self.p/'.runs'/packet['task_id']/'task.yaml')

    def finish(self, packet, content):
        task=self.start(packet);tid=task['task_id'];out=task['outputs'][0]
        payload=dict(result=dict(task_id=tid,attempt=1,status='submitted',summary='OFFLINE FIXTURE',
                     created_artifacts=[],updated_artifacts=[],evidence=task['inputs'],unresolved_issues=[],confidence='low',
                     self_check={c:'fixture' for c in task['acceptance_criteria']}),
                     artifacts=[dict(id=out['id'],type=out['type'],mode=out['mode'],content=content)])
        tasks.submit(self.root,self.p,tid,1,payload,wf)
        review=dict(task_id=tid,attempt=1,reviewer='main',decision='accept',passed_criteria=task['acceptance_criteria'],
                    failed_criteria=[],issues=[],required_changes=[],evidence_checks=[dict(ref=r,status='verified') for r in task['inputs']],
                    next_action='apply fixture',reason='Synthetic test review, no scientific claim')
        tasks.record_review(self.root,self.p,tid,1,review,wf)
        return tasks.accept(self.root,self.p,tid,1,wf)

    def test_split_covers_every_line_without_overlap(self):
        text='\n'.join(f'{n} '+'x'*110 for n in range(24))
        ranges=study.split_lines(text,500)
        self.assertEqual([n for a,b in ranges for n in range(a,b+1)],list(range(1,25)))
        self.assertTrue(all(len('\n'.join(text.splitlines()[a-1:b]))<=500 for a,b in ranges))
        with self.assertRaisesRegex(ValueError,'单行'):study.split_lines('x'*501,500)

    def test_plan_dry_run_is_read_only_and_rerun_preserves(self):
        before=self.snapshot()
        preview=study.plan(self.root,self.p,'Sample2026',wf,True,500)
        self.assertEqual(before,self.snapshot())
        real=study.plan(self.root,self.p,'Sample2026',wf,False,500)
        self.assertEqual(preview['task_files'],real['task_files'])
        written=self.snapshot()
        study.plan(self.root,self.p,'Sample2026',wf,False,500)
        self.assertEqual(written,self.snapshot())
        self.assertFalse((self.paper/'06_synthesis').exists())

    def test_changed_plan_does_not_overwrite_existing_task(self):
        first=study.plan(self.root,self.p,'Sample2026',wf,False,500)
        task=self.p/first['task_files'][0]
        data=wf.load(task);data['objective']='manual custom instruction';wf.save(task,data)
        before=self.snapshot()
        with self.assertRaisesRegex(ValueError,'原件保留'):study.plan(self.root,self.p,'Sample2026',wf,False,500)
        self.assertEqual(before,self.snapshot())

    def test_yaml_field_anchor_excludes_unrelated_large_data(self):
        self.assertEqual(tasks.select_anchor('overview:\n  object: selected\nextraction:\n  method: UNRELATED\n','overview'), 'object: selected\n')
        self.assertEqual(tasks.select_anchor('# overview\nmarkdown fixture\n','overview'),'# overview\nmarkdown fixture\n')

    def test_complete_context_blocks_provider_before_truncated_input(self):
        self.source.write_text('z'*20000,encoding='utf-8');wf.index(self.root,'study')
        ref=next(k for k,v in registry.load_index(self.p)['artifacts'].items() if v['path']==self.source.relative_to(self.p).as_posix())
        packet=dict(task_id='too-large',task_type='literature-translate',objective='fixture',
                    inputs=[dict(id='paper:Sample2026'),dict(id=ref)],allowed_paths=[self.paper.relative_to(self.p).as_posix()],
                    constraints=dict(require_complete_context=True),context=dict(paper_citekey='Sample2026'))
        with patch('tools.tasks.adapters.execute') as call:
            with self.assertRaisesRegex(ValueError,'完整上下文'):self.start(packet)
            call.assert_not_called()

    def test_both_delivery_contracts_are_colocated_and_reviewed(self):
        plan=study.plan(self.root,self.p,'Sample2026',wf)
        for kind,(name,task_type,headings) in study.DELIVERIES.items():
            packet=next(wf.load(self.p/f) for f in plan['task_files'] if wf.load(self.p/f)['task_type']==task_type)
            info=dict(id='artifact:Sample2026:'+kind,type='artifact',paper_id='paper:Sample2026',generated_by='fixture',model_role='literature-reader',
                      prompt_version='fixture',source_refs=[self.source.relative_to(self.p).as_posix()],created_at='2026-01-01',scope='fixture',links=[])
            if kind=='concept-guide':info['id']='artifact:Sample2026:concept-guide'
            body='# Fixture\n\n'+'\n\n'.join(f'## {n}. {h}\n\nFixture evidence.' for n,h in enumerate(headings,1))
            self.finish(packet,'---\n'+tasks.dump(info)+'---\n\n'+body)
            path=self.paper/'06_synthesis'/name
            self.assertTrue(path.is_file())
            study.validate_delivery(self.root,self.p,path,kind,'paper:Sample2026',wf)
            if kind=='concept-guide':
                execution=wf.load(self.p/'.runs'/packet['task_id']/'attempts/1/execution.yaml')
                self.assertEqual(execution['requested_role'],'knowledge-builder')
                self.assertEqual(execution['effective_role'],'literature-reader')
        with contextlib.redirect_stdout(io.StringIO()):wf.validate(self.root,'study')

    def test_delivery_missing_section_cannot_write_formal_file(self):
        plan=study.plan(self.root,self.p,'Sample2026',wf)
        packet=wf.load(self.p/plan['task_files'][-2])
        info=dict(id='artifact:Sample2026:summary',type='artifact',paper_id='paper:Sample2026',generated_by='fixture',model_role='literature-reader',
                  prompt_version='fixture',source_refs=[self.source.relative_to(self.p).as_posix()],created_at='2026-01-01',scope='fixture',links=[])
        with self.assertRaisesRegex(ValueError,'规定章节'):
            self.finish(packet,'---\n'+tasks.dump(info)+'---\n\n# Incomplete fixture')
        self.assertFalse((self.paper/'06_synthesis/summary.md').exists())

    def test_coverage_requires_accept_and_detects_omissions(self):
        plan=study.plan(self.root,self.p,'Sample2026',wf,False,500)
        self.assertFalse(study.coverage(self.root,self.p,'Sample2026',wf)['structural_coverage'])
        ledger=wf.load(self.p/plan['coverage'])
        for segment in ledger['segments']:
            sid=segment['id'];packet=wf.load(self.p/segment['task_file'])
            self.finish(packet,f'\n<!-- translation:{sid} -->\nFixture translation.\n<!-- /translation:{sid} -->\n')
        result=study.coverage(self.root,self.p,'Sample2026',wf)
        self.assertTrue(result['structural_coverage'],result['errors'])
        self.assertEqual(result['accepted'],result['expected'])
        path=self.paper/'02_translation/translation.md'
        path.write_text(path.read_text(encoding='utf-8').replace('Fixture translation.','',1),encoding='utf-8')
        self.assertFalse(study.coverage(self.root,self.p,'Sample2026',wf)['structural_coverage'])

    def test_translation_marker_missing_blocks_formal_append(self):
        plan=study.plan(self.root,self.p,'Sample2026',wf)
        packet=wf.load(self.p/plan['task_files'][0])
        before=(self.paper/'02_translation/translation.md').read_bytes()
        with self.assertRaisesRegex(ValueError,'翻译片段标记'):self.finish(packet,'Translation with no marker.')
        self.assertEqual(before,(self.paper/'02_translation/translation.md').read_bytes())

    def test_complete_revision_splits_long_draft_without_losing_lines(self):
        packet=dict(task_id='long-repair',task_type='literature-synthesis',objective='offline repair fixture',
                    inputs=[dict(id='paper:Sample2026'),dict(id='analysis:Sample2026',anchor='overview'),dict(id='reading:Sample2026',anchor='1. 全局定位')],
                    allowed_paths=[self.paper.relative_to(self.p).as_posix()],context=dict(paper_citekey='Sample2026'),
                    constraints=dict(require_complete_context=True))
        task=self.start(packet);out=task['outputs'][0]
        content='\n'.join(f'draft-only-{n:04} '+('x'*70) for n in range(180))
        self.assertGreater(len(content),task['context_limits']['max_file_chars'])
        payload=dict(result=dict(task_id=task['task_id'],attempt=1,status='submitted',summary='OFFLINE FIXTURE',
                     created_artifacts=[],updated_artifacts=[],evidence=task['inputs'],unresolved_issues=[],confidence='low',
                     self_check={c:'fixture' for c in task['acceptance_criteria']}),
                     artifacts=[dict(id=out['id'],type=out['type'],mode=out['mode'],content=content)])
        tasks.submit(self.root,self.p,task['task_id'],1,payload,wf)
        problem=dict(criterion='coherent_full_paper',detail='Synthetic fixture requires repair',artifact_id=out['id'])
        review=dict(task_id=task['task_id'],attempt=1,reviewer='main',decision='revise',passed_criteria=[],
                    failed_criteria=['coherent_full_paper'],issues=[problem],required_changes=[problem],evidence_checks=[],
                    next_action='repair fixture',reason='Offline fixture, no scientific claim')
        path=self.p/'00_inbox/repair.yaml';wf.save(path,review)
        with patch('tools.tasks.adapters.execute') as call:
            directory=tasks.revise(self.root,self.p,task['task_id'],1,path.relative_to(self.root).as_posix(),wf)
            call.assert_not_called()
        manifest=wf.load(directory/'manifest.yaml');text=(directory/'context.md').read_text(encoding='utf-8')
        self.assertGreater(len(manifest['inputs']),1)
        self.assertTrue(all(row['included'] and not row['truncated'] for row in manifest['inputs']))
        for n in range(180):self.assertEqual(text.count(f'draft-only-{n:04}'),1)
        self.assertFalse((self.paper/'06_synthesis/summary.md').exists())

if __name__=='__main__':unittest.main()
