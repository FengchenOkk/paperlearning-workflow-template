"""在隔离临时目录检查文件管理、追溯与外部调用边界。"""
import copy
import contextlib
import io
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tools import wf, adapters, literature

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in ['config','workflow/templates','workflow/prompts','projects/_template']:
            shutil.copytree(wf.ROOT / rel, self.root / rel)
        for rel in ['workflow/README.md','workflow/literature.md','workflow/reproduction.md','workflow/schemas.yaml']:
            shutil.copyfile(wf.ROOT / rel, self.root / rel)
        # 测试始终使用离线模板，不能继承用户真实模型配置或发起付费调用。
        shutil.copyfile(self.root/'config/models.example.yaml',self.root/'config/models.local.yaml')
        shutil.copyfile(wf.ROOT / '.env.example', self.root / '.env.example')
        shutil.copyfile(wf.ROOT / '.gitignore', self.root / '.gitignore')
        (self.root / 'tools').mkdir(); (self.root / 'tests').mkdir()
        shutil.copytree(wf.ROOT/'tests/fixtures',self.root/'tests/fixtures')
        wf.bootstrap(self.root)
        wf.init(self.root, 'test-project', '测试项目')

    def task(self):
        task = wf.load(self.root / 'workflow/templates/task.yaml')
        task.update(task_id='test-task', inputs=['research-profile.yaml'], source_refs=['research-profile.yaml'])
        wf.save(self.root / 'task.yaml', task)
        return task

    def test_bootstrap_preserves_config_and_env(self):
        path = self.root / 'config/models.local.yaml'
        path.write_text('keep: true\n', encoding='utf-8')
        (self.root / '.env').write_text('MODEL_API_KEY=keep\n')
        wf.bootstrap(self.root)
        self.assertEqual(wf.load(path), {'keep':True})
        self.assertEqual((self.root / '.env').read_text(), 'MODEL_API_KEY=keep\n')

    def test_end_to_end_and_index(self):
        paper = wf.new_paper(self.root,'test-project','sample-paper')
        claim = wf.new_claim(self.root,'test-project','sample-paper','main')
        self.assertEqual(wf.load(paper/'meta.yaml')['status'],'unread')
        self.assertIsNone(wf.load(claim/'claim.yaml')['route'])
        wf.validate(self.root,'test-project')
        text = (self.root/'projects/test-project/INDEX.md').read_text(encoding='utf-8')
        self.assertIn('sample-paper--main',text)
        self.task()
        config = wf.models(self.root)
        config['subagents']['literature-reader']['adapter']='mock'
        result=wf.run(self.root,'test-project','task.yaml',config_override=config)
        self.assertEqual(wf.load(result/'run.yaml')['status'],'mock')
        self.assertTrue(wf.load(result/'run.yaml')['input_hashes'])
        self.assertIn('占位', (result/'response.md').read_text(encoding='utf-8'))

    def test_duplicate_creation_preserves_existing(self):
        with self.assertRaises(ValueError): wf.init(self.root,'test-project','覆盖')
        paper=wf.new_paper(self.root,'test-project','sample')
        (paper/'01_source/original.txt').write_text('keep')
        with self.assertRaises(ValueError): wf.new_paper(self.root,'test-project','sample')
        self.assertEqual((paper/'01_source/original.txt').read_text(),'keep')
        wf.new_claim(self.root,'test-project','sample','main')
        with self.assertRaises(ValueError): wf.new_claim(self.root,'test-project','sample','main')

    def test_path_traversal(self):
        with self.assertRaises(ValueError): wf.init(self.root,'../escape','测试')
        task=self.task(); task['inputs']=['../../config/models.local.yaml']
        wf.save(self.root/'task.yaml',task)
        with self.assertRaises(ValueError): wf.run(self.root,'test-project','task.yaml')

    def test_route_contract(self):
        wf.new_paper(self.root,'test-project','sample')
        claim=wf.new_claim(self.root,'test-project','sample','main')
        data=wf.load(claim/'claim.yaml'); data['route']='imaginary'
        wf.save(claim/'claim.yaml',data)
        with self.assertRaises(ValueError): wf.validate(self.root,'test-project')

    def test_source_refs_and_locator(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        data=wf.load(paper/'meta.yaml'); data['source_refs']=['missing.txt#page=1']
        wf.save(paper/'meta.yaml',data)
        with self.assertRaises(ValueError): wf.validate(self.root,'test-project')
        path=self.root/'projects/test-project/missing.txt'; path.write_text('evidence')
        wf.validate(self.root,'test-project')

    def test_manual_prepares_without_response(self):
        self.task()
        result=wf.run(self.root,'test-project','task.yaml')
        self.assertEqual(wf.load(result/'run.yaml')['status'],'waiting-manual')
        self.assertFalse((result/'response.md').exists())

    def test_nested_extraction_source_is_validated(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        data=wf.load(paper/'04_analysis/analysis.yaml')
        data['extraction']['claims']=[{'text':'主张','source_refs':['absent.txt#page=2']}]
        wf.save(paper/'04_analysis/analysis.yaml',data)
        with self.assertRaises(ValueError): wf.validate(self.root,'test-project')

    def test_command_execution_uses_stdin_and_timeout(self):
        config=wf.models(self.root)['subagents']['literature-reader']
        config.update(adapter='command',command=['client','--read-stdin'])
        with patch('subprocess.run') as command:
            command.return_value.returncode=0
            command.return_value.stdout='草稿'
            self.assertEqual(adapters.execute(config,'输入',self.root,True),('draft','草稿'))
            self.assertEqual(command.call_args.kwargs['input'],'输入')
            self.assertFalse(command.call_args.kwargs['shell'])
            self.assertEqual(command.call_args.kwargs['timeout'],600)

    def test_http_request_contract(self):
        import io
        import json
        config=wf.models(self.root)['subagents']['literature-reader']
        config.update(adapter='openai_compatible',model='test',base_url='https://example.com/v1',api_key_env='TEST_MODEL_KEY')
        with patch.dict('os.environ',{'TEST_MODEL_KEY':'test-only'}), patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value=io.BytesIO(b'{"choices":[{"message":{"content":"draft"}}]}')
            self.assertEqual(adapters.execute(config,'input',self.root,True),('draft','draft'))
            request=opener.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url,'https://example.com/v1/chat/completions')
            self.assertEqual(json.loads(request.data)['model'],'test')

    def test_command_dry_run_does_not_execute(self):
        config=wf.models(self.root)['subagents']['literature-reader']
        config.update(adapter='command',command=['python','client.py'])
        with patch('subprocess.run',side_effect=AssertionError('不应执行')):
            self.assertEqual(adapters.execute(config,'prompt',self.root)[0],'dry-run')

    def test_http_dry_run_no_network(self):
        config=wf.models(self.root)['subagents']['literature-reader']
        config.update(adapter='openai_compatible',model='test',base_url='https://example.com/v1',api_key_env='TEST_MODEL_KEY')
        with patch.dict('os.environ',{'TEST_MODEL_KEY':'test-only'}), patch('urllib.request.build_opener',side_effect=AssertionError('不应联网')):
            self.assertEqual(adapters.execute(config,'prompt',self.root)[0],'dry-run')

    def test_failed_execution_is_logged(self):
        self.task()
        with patch.object(adapters,'execute',side_effect=RuntimeError('secret')):
            with self.assertRaises(ValueError): wf.run(self.root,'test-project','task.yaml')
        record=next((self.root/'projects/test-project/.runs').glob('*/run.yaml'))
        self.assertEqual(wf.load(record)['status'],'failed')
        self.assertNotIn('secret',record.read_text())

    def test_keyless_api_config_prepares_and_records_options(self):
        self.task()
        config=wf.models(self.root)
        settings=config['subagents']['literature-reader']
        settings.update(adapter='openai_compatible',model='deepseek-flash',base_url='https://api.deepseek.com',api_key_env='TEST_DEEPSEEK_KEY',
                        request_options={'thinking':{'type':'enabled'},'reasoning_effort':'high','max_tokens':16384})
        wf.save(self.root/'config/models.local.yaml',config)
        with patch.dict('os.environ',{},clear=True), patch('urllib.request.build_opener',side_effect=AssertionError('不应联网')):
            result=wf.run(self.root,'test-project','task.yaml')
            record=wf.load(result/'run.yaml')
            self.assertEqual(record['status'],'waiting-manual')
            self.assertEqual(record['effective_profile'],'manual')
            self.assertEqual(record['requested_model'],'deepseek-flash')
            self.assertEqual(record['requested_adapter'],'openai_compatible')
            self.assertIsNone(record['model'])
            self.assertIn('密钥',record['fallback_reason'])
            self.assertNotIn('request_options',record)
            wf.doctor(self.root,True)
            wf.run(self.root,'test-project','task.yaml',execute_external=True)

    def test_deepseek_http_options_and_final_content(self):
        import io
        import json
        config=wf.models(self.root)['subagents']['literature-reader']
        options={'thinking':{'type':'enabled'},'reasoning_effort':'high','max_tokens':16384}
        config.update(adapter='openai_compatible',model='deepseek-flash',base_url='https://api.deepseek.com',api_key_env='TEST_DEEPSEEK_KEY',request_options=options)
        with patch.dict('os.environ',{'TEST_DEEPSEEK_KEY':'test-only'}), patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value=io.BytesIO(json.dumps({'choices':[{'message':{'content':'最终草稿','reasoning_content':'internal'},'finish_reason':'stop'}]}).encode())
            self.assertEqual(adapters.execute(config,'输入',self.root,True),('draft','最终草稿'))
            request=opener.return_value.open.call_args.args[0]
            body=json.loads(request.data)
            self.assertEqual(request.full_url,'https://api.deepseek.com/chat/completions')
            self.assertEqual({k:body[k] for k in options},options)
            self.assertEqual(body['model'],'deepseek-flash')
            self.assertEqual(body['messages'],[{'role':'user','content':'输入'}])

    def test_http_incomplete_and_empty_output(self):
        import io
        import json
        config=wf.models(self.root)['subagents']['literature-reader']
        config.update(adapter='openai_compatible',model='test',base_url='https://example.com',api_key_env='TEST_MODEL_KEY')
        with patch.dict('os.environ',{'TEST_MODEL_KEY':'test-only'}), patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value=io.BytesIO(json.dumps({'choices':[{'message':{'content':'部分正文'},'finish_reason':'length'}]}).encode())
            self.assertEqual(adapters.execute(config,'输入',self.root,True),('partial','部分正文'))
            opener.return_value.open.return_value=io.BytesIO(b'{"choices":[{"message":{"content":null},"finish_reason":"length"}]}')
            with self.assertRaisesRegex(ValueError,'有效正文'):adapters.execute(config,'输入',self.root,True)

    def test_request_options_cannot_replace_model_or_messages(self):
        config=wf.models(self.root)['subagents']['literature-reader']
        config.update(provider='deepseek',adapter='openai_compatible',model='test',base_url='https://example.com',api_key_env='TEST_MODEL_KEY')
        for options in [{'model':'other'},{'messages':[]},{'max_tokens':True},{'thinking':{'type':'unknown'}},{'reasoning_effort':'invalid'}]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                adapters.check(dict(config,request_options=options),require_credentials=False)

    def test_doctor_offline(self):
        with patch('urllib.request.build_opener',side_effect=AssertionError('不应联网')):
            wf.doctor(self.root,offline=True)

    def test_demo_leaves_projects_untouched(self):
        before=sorted(str(x.relative_to(wf.ROOT/'projects')) for x in (wf.ROOT/'projects').rglob('*'))
        wf.demo(wf.ROOT)
        after=sorted(str(x.relative_to(wf.ROOT/'projects')) for x in (wf.ROOT/'projects').rglob('*'))
        self.assertEqual(before,after)

    def test_four_core_files_and_concept_creation(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        self.assertEqual({x.name for x in paper.iterdir() if x.is_file()},
                         {'meta.yaml'})
        concept=wf.new_concept(self.root,'test-project','first-concept')
        info,body=literature.markdown(concept)
        self.assertEqual(info['concept_id'],'first-concept')
        self.assertEqual(info['status'],'not-started')
        self.assertIn('代表文献迷你综述',body)
        with self.assertRaises(ValueError):wf.new_concept(self.root,'test-project','first-concept')
        wf.validate(self.root,'test-project')

    def test_categories_and_reading_list_do_not_duplicate_papers(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        meta=wf.load(paper/'meta.yaml')
        meta.update(year=2025,paper_role='survey',categories=['优化','统计'],topic_tags=['学习'],reading_priority='a')
        wf.save(paper/'meta.yaml',meta)
        wf.index(self.root,'test-project')
        p=self.root/'projects/test-project'
        index=(p/'INDEX.md').read_text(encoding='utf-8')
        self.assertIn('### 优化',index);self.assertIn('### 统计',index)
        self.assertIn('## 时间线',index);self.assertIn('## 按 paper_role 分类',index)
        text=(p/'10_literature/reading-list.md').read_text(encoding='utf-8')
        self.assertIn('2025',text);self.assertIn('survey',text)
        self.assertEqual(len(list((p/'10_literature/papers').iterdir())),2)  # 论文与 .gitkeep
        self.assertFalse((p/'10_literature/catalog').exists())
        self.assertFalse((p/'10_literature/collections').exists())

    def test_reading_annotations_and_matrix_are_preserved(self):
        wf.new_paper(self.root,'test-project','sample')
        p=self.root/'projects/test-project/10_literature'
        path=p/'reading-list.md';info,body=literature.markdown(path)
        info['reading_notes']={'sample':'先补背景'}
        info['topic_paths']={'我的顺序':['sample']}
        info['reading_order']=['sample']
        literature.write_markdown(path,info,body+'\n人工备注保持。\n')
        (p/'matrix.md').write_text('人工矩阵',encoding='utf-8')
        wf.index(self.root,'test-project')
        after=path.read_text(encoding='utf-8')
        self.assertIn('先补背景',after);self.assertIn('人工备注保持',after)
        self.assertEqual((p/'matrix.md').read_text(encoding='utf-8'),'人工矩阵')

    def test_reading_list_missing_paper(self):
        path=self.root/'projects/test-project/10_literature/reading-list.md'
        info,body=literature.markdown(path);info['reading_notes']={'absent':'读它'}
        literature.write_markdown(path,info,body)
        with self.assertRaisesRegex(ValueError,'citekey'):wf.validate(self.root,'test-project')

    def test_knowledge_counts_deduplicated_and_prerequisite_order(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        base=wf.new_concept(self.root,'test-project','base')
        derived=wf.new_concept(self.root,'test-project','derived')
        info,body=literature.markdown(base);info['status']='understood'
        info['papers']=['sample','sample'];literature.write_markdown(base,info,body)
        info,body=literature.markdown(derived);info['prerequisites']=['base'];info['papers']=['sample']
        literature.write_markdown(derived,info,body)
        meta=wf.load(paper/'meta.yaml');meta['concept_ids']=['base','derived'];wf.save(paper/'meta.yaml',meta)
        data=wf.load(paper/'04_analysis/analysis.yaml')
        data['concepts']=[dict(id='base',role='used',local_meaning='定义',source_refs=[],understanding_status='learning')]
        wf.save(paper/'04_analysis/analysis.yaml',data)
        wf.index(self.root,'test-project');wf.validate(self.root,'test-project')
        text=(self.root/'projects/test-project/10_literature/knowledge-map.md').read_text(encoding='utf-8')
        self.assertIn('base.md)：1 篇论文',text)
        self.assertIn('derived.md)：1 篇论文',text)
        order=text.split('## 推荐学习顺序')[1].split('## 孤立概念')[0]
        self.assertLess(order.index('base'),order.index('derived'))

    def test_cycle_report_does_not_invent_learning_order(self):
        a=wf.new_concept(self.root,'test-project','alpha')
        b=wf.new_concept(self.root,'test-project','beta')
        for path,target in [(a,'beta'),(b,'alpha')]:
            info,body=literature.markdown(path);info['prerequisites']=[target]
            literature.write_markdown(path,info,body)
        wf.index(self.root,'test-project')
        text=(self.root/'projects/test-project/10_literature/knowledge-map.md').read_text(encoding='utf-8')
        self.assertIn('无法排序',text);self.assertIn('循环',text)

    def test_missing_concept_reference(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        data=wf.load(paper/'meta.yaml');data['concept_ids']=['absent'];wf.save(paper/'meta.yaml',data)
        with self.assertRaisesRegex(ValueError,'概念卡'):wf.validate(self.root,'test-project')

    def formula(self):
        return dict(id='eq-1',label='1',latex='x=1',name_zh='示例',plain_meaning='示例',symbols=[],
                    assumptions=[],derivation_steps=[],intuition='示例',special_cases=[],related_concepts=[],
                    source_refs=[],confidence='TODO(user)')

    def test_duplicate_formulas_and_nested_schema(self):
        paper=wf.new_paper(self.root,'test-project','sample');path=paper/'04_analysis/analysis.yaml';data=wf.load(path)
        data['formulas']=[self.formula(),self.formula()];wf.save(path,data)
        with self.assertRaisesRegex(ValueError,'公式 ID 重复'):wf.validate(self.root,'test-project')
        data['formulas']=[self.formula()];del data['formulas'][0]['symbols'];wf.save(path,data)
        with self.assertRaisesRegex(ValueError,'symbols'):wf.validate(self.root,'test-project')

    def test_completion_requires_reading_sections_and_no_translation_todo(self):
        paper=wf.new_paper(self.root,'test-project','sample');meta=wf.load(paper/'meta.yaml')
        meta['reading_status']='complete';wf.save(paper/'meta.yaml',meta)
        (paper/'03_reading/reading.md').write_text('# 很短的精读',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'固定章节'):wf.validate(self.root,'test-project')
        meta.update(reading_status='none',translation_status='complete');wf.save(paper/'meta.yaml',meta)
        with self.assertRaisesRegex(ValueError,'TODO'):wf.validate(self.root,'test-project')
        (paper/'02_translation/translation.md').write_text('# 原文第一节\n\n完整测试译文。',encoding='utf-8')
        wf.validate(self.root,'test-project')

    def test_invalid_status_is_rejected(self):
        paper=wf.new_paper(self.root,'test-project','sample');meta=wf.load(paper/'meta.yaml')
        meta['translation_status']='finished';wf.save(paper/'meta.yaml',meta)
        with self.assertRaisesRegex(ValueError,'translation_status'):wf.validate(self.root,'test-project')

    def test_no_first_pass_blocks_translation_then_allows_prepared_draft(self):
        paper=wf.new_paper(self.root,'test-project','sample');task=self.task()
        task['context']=dict(task_type='literature-translate',paper_citekey='sample')
        task['inputs']=['10_literature/papers/sample/analysis.yaml'];wf.save(self.root/'task.yaml',task)
        with self.assertRaisesRegex(ValueError,'全局定位'):wf.run(self.root,'test-project','task.yaml')
        data=wf.load(paper/'04_analysis/analysis.yaml')
        data['overview'].update(object='对象',core_problem='问题',why_important='重要性',position='位置')
        wf.save(paper/'04_analysis/analysis.yaml',data)
        result=wf.run(self.root,'test-project','task.yaml')
        self.assertEqual(wf.load(result/'run.yaml')['status'],'waiting-manual')
        self.assertEqual(wf.load(paper/'meta.yaml')['translation_status'],'none')

    def test_knowledge_role_fallback_and_actual_log(self):
        task=self.task();task.update(role='knowledge-builder')
        task['context']['task_type']='literature-knowledge';wf.save(self.root/'task.yaml',task)
        config=wf.models(self.root);config['subagents']['literature-reader']['adapter']='mock'
        del config['subagents']['knowledge-builder']
        result=wf.run(self.root,'test-project','task.yaml',config_override=config)
        record=wf.load(result/'run.yaml')
        self.assertEqual(record['requested_role'],'knowledge-builder')
        self.assertEqual(record['effective_role'],'literature-reader')
        self.assertIn('knowledge-builder：概念卡', (result/'prompt.md').read_text(encoding='utf-8'))

    def test_old_model_config_and_schema_task_still_work(self):
        config=wf.load(self.root/'config/models.local.yaml')
        del config['subagents']['knowledge-builder'];del config['fallback']
        for key in list(config['routing']):
            if key in ['literature-first-pass','literature-translate','literature-close-read','literature-formula','literature-context','literature-knowledge']:
                del config['routing'][key]
        wf.save(self.root/'config/models.local.yaml',config)
        before=(self.root/'config/models.local.yaml').read_bytes()
        wf.doctor(self.root,True)
        self.assertEqual(before,(self.root/'config/models.local.yaml').read_bytes())
        task=self.task();task['output_schema']='workflow/schemas/paper.schema.json';wf.save(self.root/'task.yaml',task)
        result=wf.run(self.root,'test-project','task.yaml')
        self.assertTrue((result/'prompt.md').exists())

    def test_legacy_migration_preserves_files_and_reproduction(self):
        p=self.root/'projects/test-project';folder=p/'10_literature/papers/old-paper';folder.mkdir()
        (folder/'source').mkdir()
        old_meta=dict(citekey='old-paper',title='旧论文',authors=[],year=2020,status='read',source_refs=[])
        wf.save(folder/'meta.yaml',old_meta)
        original='旧笔记原文，不得丢失。';(folder/'note.md').write_text(original,encoding='utf-8')
        wf.save(folder/'extraction.yaml',dict(claims=[],method=['旧方法'],data=[],baselines=[],metrics=[],results=[],limitations=[],source_refs=[]))
        with self.assertWarns(UserWarning):wf.validate(self.root,'test-project')
        with self.assertWarns(UserWarning):wf.index(self.root,'test-project')
        self.assertEqual((folder/'note.md').read_text(encoding='utf-8'),original)
        self.assertIn(original,(folder/'03_reading/reading.md').read_text(encoding='utf-8'))
        self.assertEqual(wf.load(folder/'04_analysis/analysis.yaml')['extraction']['method']['legacy_items'],['旧方法'])
        snapshot=next((p/'.runs').glob('*-migration-*/meta.before.yaml'))
        self.assertEqual(wf.load(snapshot),old_meta)
        with self.assertWarns(UserWarning):wf.validate(self.root,'test-project')
        wf.new_claim(self.root,'test-project','old-paper','result')
        self.assertTrue((p/'20_reproduction/old-paper--result/claim.yaml').exists())

    def test_migration_never_overwrites_new_reading_or_translation(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        (paper/'note.md').write_text('旧笔记',encoding='utf-8')
        reading=(paper/'03_reading/reading.md').read_bytes();translation=(paper/'02_translation/translation.md').read_bytes()
        with self.assertWarns(UserWarning):wf.index(self.root,'test-project')
        self.assertEqual(reading,(paper/'03_reading/reading.md').read_bytes())
        self.assertEqual(translation,(paper/'02_translation/translation.md').read_bytes())

    def test_cli_existing_and_new_commands(self):
        with patch.object(wf,'ROOT',self.root):
            for command in [
                ['bootstrap'], ['doctor','--offline'], ['init','cli-project','--title','命令验收'],
                ['new','paper','cli-project','cli-paper'], ['new','concept','cli-project','cli-concept'],
                ['new','claim','cli-project','cli-paper','claim'], ['index','cli-project'], ['validate','cli-project'],
                ['run','cli-project','workflow/templates/task.yaml']]:
                if command[0]=='run':
                    task=wf.load(self.root/'workflow/templates/task.yaml');task['task_id']='cli-task'
                    wf.save(self.root/'workflow/templates/task.yaml',task)
                self.assertEqual(wf.main(command),0,command)
        self.assertFalse((self.root/'projects/cli-project/10_literature/synthesis').exists())

    def test_minimal_manual_config_is_compatible(self):
        path=self.root/'config/models.local.yaml'
        config=wf.load(path)
        config['subagents']['literature-reader']={'enabled':True,'adapter':'manual'}
        config['subagents']['knowledge-builder']={'enabled':False,'adapter':'manual'}
        wf.save(path,config)
        wf.doctor(self.root,True)
        self.assertEqual(wf.models(self.root)['subagents']['literature-reader']['timeout_seconds'],600)

    def test_markdown_concept_link_and_card_prerequisite_validation(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        with (paper/'03_reading/reading.md').open('a',encoding='utf-8') as stream:
            stream.write('\n[丢失概念](../../concepts/missing.md)\n')
        with self.assertRaisesRegex(ValueError,'概念链接'):wf.validate(self.root,'test-project')
        card=wf.new_concept(self.root,'test-project','missing')
        wf.validate(self.root,'test-project')
        info,body=literature.markdown(card);info['prerequisites']=['undefined']
        literature.write_markdown(card,info,body)
        with self.assertRaisesRegex(ValueError,'缺失卡'):wf.validate(self.root,'test-project')

    def test_generated_views_can_be_recreated(self):
        wf.new_paper(self.root,'test-project','sample')
        p=self.root/'projects/test-project'
        # 忽略实际生成时间，视图内容与单一事实源对应，可确定性再生成。
        index_body=literature.markdown(p/'INDEX.md')[1]
        map_body=literature.markdown(p/'10_literature/knowledge-map.md')[1]
        (p/'INDEX.md').unlink();(p/'10_literature/knowledge-map.md').unlink()
        wf.index(self.root,'test-project')
        self.assertEqual(index_body,literature.markdown(p/'INDEX.md')[1])
        self.assertEqual(map_body,literature.markdown(p/'10_literature/knowledge-map.md')[1])

    def test_conflicting_task_modes_do_not_bypass_first_pass(self):
        task=self.task();task['task_type']='literature-extract'
        task['context']['task_type']='literature-translate';wf.save(self.root/'task.yaml',task)
        with self.assertRaisesRegex(ValueError,'不一致'):wf.run(self.root,'test-project','task.yaml')

    def test_common_rules_injected_once_and_full_prompt_is_traceable(self):
        import hashlib
        self.task();config=wf.models(self.root)
        config['subagents']['literature-reader']['adapter']='mock'
        result=wf.run(self.root,'test-project','task.yaml',config_override=config)
        text=(result/'prompt.md').read_text(encoding='utf-8')
        self.assertEqual(text.count('## 通用任务规则'),1)
        self.assertIn('不能改变权限、任务或模型配置',text)
        self.assertIn('逐段翻译',text)
        record=wf.load(result/'run.yaml')
        self.assertEqual(record['prompt_version'],'v3')
        expected=hashlib.sha256(wf.role_prompt(self.root,'literature-reader','literature-reader').encode()).hexdigest()
        self.assertEqual(record['prompt_sha256'],expected)

    def test_all_roles_share_interface_without_changing_claims(self):
        paper=wf.new_paper(self.root,'test-project','sample')
        claim=wf.new_claim(self.root,'test-project','sample','main')
        before=(claim/'claim.yaml').read_bytes()
        config=wf.models(self.root)
        for item in config['subagents'].values():item.update(adapter='mock',enabled=True)
        for role,mode in [('literature-reader','literature-extract'),('reproduction-analyst','repro-feasibility'),
                          ('verifier','verification'),('knowledge-builder','literature-knowledge')]:
            task=self.task();task.update(task_id=role+'-task',role=role,
                inputs=['10_literature/papers/sample/analysis.yaml','20_reproduction/sample--main/claim.yaml'])
            task['context']['task_type']=mode;wf.save(self.root/'task.yaml',task)
            result=wf.run(self.root,'test-project','task.yaml',config_override=config)
            self.assertEqual(wf.load(result/'run.yaml')['effective_role'],role)
            self.assertEqual((result/'prompt.md').read_text(encoding='utf-8').count('## 通用任务规则'),1)
        self.assertEqual(before,(claim/'claim.yaml').read_bytes())
        self.assertEqual(wf.load(paper/'meta.yaml')['reading_status'],'none')

    def test_compact_config_preserves_explicit_values_and_routes(self):
        path=self.root/'config/models.local.yaml'
        config=wf.load(path)
        config['subagents']['literature-reader']=dict(adapter='mock',model='my-model',provider='my-provider',timeout_seconds=42)
        config['routing']['repro-feasibility']='verifier'
        wf.save(path,config);before=path.read_bytes()
        normalized=wf.models(self.root)
        self.assertEqual(normalized['subagents']['literature-reader']['model'],'my-model')
        self.assertEqual(normalized['subagents']['literature-reader']['timeout_seconds'],42)
        self.assertEqual(normalized['routing']['repro-feasibility'],'verifier')
        self.assertEqual(before,path.read_bytes())

    def test_bootstrap_recreates_absent_local_files_and_directories(self):
        (self.root/'.env').unlink();(self.root/'config/models.local.yaml').unlink()
        shutil.rmtree(self.root/'tools')
        with patch.object(wf,'environment',side_effect=AssertionError('bootstrap 不读取密钥')):
            wf.bootstrap(self.root)
        self.assertEqual((self.root/'.env').read_bytes(),(self.root/'.env.example').read_bytes())
        self.assertEqual((self.root/'config/models.local.yaml').read_bytes(),(self.root/'config/models.example.yaml').read_bytes())
        self.assertTrue((self.root/'tools').is_dir())

    def test_profile_global_selection_and_role_override(self):
        path=self.root/'config/models.local.yaml';config=wf.load(path)
        config['settings']['default_subagent_profile']='deepseek'
        config['subagents']['verifier']['profile']='manual'
        wf.save(path,config);before=path.read_bytes()
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'test-only'},clear=True), patch('urllib.request.build_opener',side_effect=AssertionError('不应联网')):
            resolved=wf.models(self.root)
            for role in ['literature-reader','reproduction-analyst']:
                item=resolved['subagents'][role]
                self.assertEqual(item['model'],'deepseek-flash')
                self.assertEqual(item['profile'],'deepseek')
                self.assertEqual(wf.execution_settings(resolved,role)['adapter'],'openai_compatible')
            self.assertEqual(resolved['subagents']['verifier']['adapter'],'manual')
            wf.doctor(self.root,True)
            self.task();result=wf.run(self.root,'test-project','task.yaml')
            record=wf.load(result/'run.yaml')
            self.assertEqual(record['status'],'dry-run')
            self.assertEqual(record['requested_profile'],'deepseek')
            self.assertEqual(record['effective_profile'],'deepseek')
            self.assertEqual(record['request_options']['reasoning_effort'],'high')
        self.assertEqual(path.read_bytes(),before)

    def test_partial_builtin_profile_overrides_preserve_connections(self):
        config=wf.load(self.root/'config/models.local.yaml')
        config['model_profiles']['deepseek']={'model':'my-chosen-model','request_options':{'max_tokens':1024}}
        config['settings']['default_subagent_profile']='deepseek'
        resolved=wf.normalize_models(self.root,config)['subagents']['literature-reader']
        self.assertEqual(resolved['model'],'my-chosen-model')
        self.assertEqual(resolved['base_url'],'https://api.deepseek.com')
        self.assertEqual(resolved['api_key_env'],'DEEPSEEK_API_KEY')
        self.assertEqual(resolved['request_options'],{'max_tokens':1024})

    def test_no_codex_or_keys_doctor_and_demo_work(self):
        config=wf.load(self.root/'config/models.local.yaml')
        config['settings']['default_subagent_profile']='deepseek';wf.save(self.root/'config/models.local.yaml',config)
        capture=io.StringIO()
        with patch.dict(os.environ,{},clear=True), patch('shutil.which',return_value=None), patch('urllib.request.build_opener',side_effect=AssertionError('不应联网')), contextlib.redirect_stdout(capture):
            wf.doctor(self.root,True,True)
            wf.demo(self.root)
        self.assertIn('不存在',capture.getvalue())
        self.assertIn('manual 可用',capture.getvalue())
        self.assertIn('未设置',capture.getvalue())
        self.assertIn('mock 演示通过',capture.getvalue())

    def test_doctor_key_presence_redacted_and_environment_precedence(self):
        config=wf.load(self.root/'config/models.local.yaml')
        config['settings']['default_subagent_profile']='deepseek';wf.save(self.root/'config/models.local.yaml',config)
        (self.root/'.env').write_text('DEEPSEEK_API_KEY=local-test-only\n',encoding='utf-8')
        capture=io.StringIO()
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'system-test-only'},clear=True),contextlib.redirect_stdout(capture):
            wf.doctor(self.root,True)
            self.assertEqual(os.environ['DEEPSEEK_API_KEY'],'system-test-only')
        self.assertIn('已设置',capture.getvalue())
        self.assertNotIn('system-test-only',capture.getvalue());self.assertNotIn('local-test-only',capture.getvalue())

    def test_other_compatible_profile_and_custom_request_options(self):
        import json
        config=wf.load(self.root/'config/models.local.yaml')
        config['model_profiles']['my-model']=dict(adapter='openai_compatible',provider='custom',base_url='https://example.com/v1',model='user-model',api_key_env='MY_MODEL_API_KEY',fallback='manual',request_options={'temperature':0.2,'response_format':{'type':'json_object'}})
        config['settings']['default_subagent_profile']='my-model'
        wf.save(self.root/'config/models.local.yaml',config)
        with patch.dict(os.environ,{'MY_MODEL_API_KEY':'test-only'},clear=True),patch('urllib.request.build_opener') as opener:
            settings=wf.execution_settings(wf.models(self.root),'literature-reader')
            self.assertEqual(settings['timeout_seconds'],600)
            self.assertNotIn('thinking',settings['request_options'])
            opener.return_value.open.return_value=io.BytesIO(b'{"choices":[{"message":{"content":"{}"},"finish_reason":"stop"}]}')
            self.assertEqual(adapters.execute(settings,'input',self.root,True)[0],'draft')
            self.assertEqual(json.loads(opener.return_value.open.call_args.args[0].data)['temperature'],0.2)

    def test_invalid_missing_profiles_and_missing_command_fall_back(self):
        for profile,definition in [('unknown',None),('invalid',{'adapter':'openai_compatible','base_url':23}),('command',{'adapter':'command','command':['never-installed-client']})]:
            with self.subTest(profile=profile):
                config=wf.load(self.root/'config/models.example.yaml')
                config['settings']['default_subagent_profile']=profile
                if definition:config['model_profiles'][profile]=definition
                normalized=wf.normalize_models(self.root,config)
                with patch('shutil.which',return_value=None):settings=wf.execution_settings(normalized,'literature-reader')
                self.assertEqual(settings['adapter'],'manual')
                self.assertTrue(settings['fallback_reason'])

    def test_external_call_failure_preserves_prompt_and_falls_back_without_retry(self):
        self.task();config=wf.load(self.root/'config/models.local.yaml')
        config['settings']['default_subagent_profile']='deepseek'
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':'test-only'},clear=True),patch.object(adapters,'execute',side_effect=RuntimeError('sensitive-error')) as call:
            result=wf.run(self.root,'test-project','task.yaml',True,config)
        record=wf.load(result/'run.yaml')
        self.assertEqual(record['status'],'waiting-manual')
        self.assertEqual(record['attempted_profile'],'deepseek')
        self.assertEqual(record['effective_profile'],'manual')
        self.assertEqual(record['adapter'],'manual');self.assertIsNone(record['model'])
        self.assertTrue((result/'prompt.md').exists());self.assertFalse((result/'response.md').exists())
        self.assertEqual(call.call_count,1)
        self.assertNotIn('sensitive-error',(result/'run.yaml').read_text(encoding='utf-8'))

    def test_reproduction_role_fallback_keeps_original_contract(self):
        self.task();task=wf.load(self.root/'task.yaml');task.update(role='reproduction-analyst',context={'task_type':'repro-plan'})
        wf.save(self.root/'task.yaml',task)
        config=wf.models(self.root);config['subagents']['reproduction-analyst']['enabled']=False
        result=wf.run(self.root,'test-project','task.yaml',config_override=config)
        self.assertEqual(wf.load(result/'run.yaml')['effective_role'],'literature-reader')
        self.assertIn('reproduction-analyst',(result/'prompt.md').read_text(encoding='utf-8'))

    def test_configuration_rejects_credentials_in_profiles_and_main(self):
        for target in ['orchestrator','deepseek']:
            config=wf.load(self.root/'config/models.local.yaml')
            block=config['orchestrator'] if target=='orchestrator' else config['model_profiles'][target]
            block['api_key']='not-a-real-key'
            wf.save(self.root/'config/models.local.yaml',config)
            with self.assertRaisesRegex(ValueError,'密钥'):wf.models(self.root)

    @unittest.skipUnless(shutil.which('git'),'需要 Git 验证实际 ignore 与追踪行为')
    def test_gitignore_and_tracked_secret_share_check(self):
        import subprocess
        def git(*args):return subprocess.run(['git','-C',str(self.root),*args],capture_output=True,check=True)
        git('init','--quiet')
        for name in ['.env','config/models.local.yaml','projects/test-project/.runs/prompt.md','paper.pdf','projects/test-project/00_inbox/private/data.txt','projects/test-project/10_literature/papers/paper/source/original.md']:
            self.assertTrue(git('check-ignore','--no-index','--',name).stdout)
        self.assertEqual(subprocess.run(['git','-C',str(self.root),'check-ignore','--','.env.example'],capture_output=True).returncode,1)
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):self.assertTrue(wf.share_check(self.root,True))
        secret='sk-'+('FAKE_TEST_VALUE_'*3)
        (self.root/'.env').write_text('DEEPSEEK_API_KEY='+secret+'\n',encoding='utf-8')
        git('add','--force','--','.env')
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):self.assertFalse(wf.share_check(self.root,True))
        self.assertIn('已被 Git 追踪',capture.getvalue())
        self.assertIn('疑似密钥',capture.getvalue());self.assertNotIn(secret,capture.getvalue())

    def test_untracked_visible_secret_is_reported_without_content(self):
        secret='sk-'+('FAKE_TEST_VALUE_'*3)
        (self.root/'notes.md').write_text(secret,encoding='utf-8')
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture):self.assertFalse(wf.share_check(self.root,True))
        self.assertIn('notes.md',capture.getvalue());self.assertNotIn(secret,capture.getvalue())

if __name__ == '__main__':
    unittest.main()
