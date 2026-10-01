"""模型接入离线验证：仅使用临时目录、假密钥与假的 HTTP 响应。"""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import adapters, wf


class ModelIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='paper-model-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # 不复制或读取工作区 models.local.yaml 和 .env。
        (self.root / 'config').mkdir()
        for target in ['models.example.yaml', 'models.local.yaml']:
            shutil.copyfile(wf.ROOT / 'config/models.example.yaml', self.root / 'config' / target)
        for rel in ['workflow/layouts', 'workflow/prompts']:
            shutil.copytree(wf.ROOT / rel, self.root / rel)
        for rel in ['workflow/README.md', 'workflow/schemas.yaml']:
            shutil.copyfile(wf.ROOT / rel, self.root / rel)
        (self.root / '.env').write_text('', encoding='utf-8')
        self.output = io.StringIO()
        self.silent = contextlib.redirect_stdout(self.output)
        self.silent.__enter__()
        self.addCleanup(self.silent.__exit__, None, None, None)
        self.environ = patch.dict(os.environ, {}, clear=True)
        self.environ.start()
        self.addCleanup(self.environ.stop)
        self.no_network = patch('urllib.request.build_opener', side_effect=AssertionError('禁止真实网络请求'))
        self.no_network.start()
        self.addCleanup(self.no_network.stop)
        wf.init(self.root, 'model-project', '模型接口测试')
        task = wf.load(self.root / 'workflow/layouts/task.yaml')
        task.update(task_id='model-test', objective='核对研究方向画像，输出草稿',
                    inputs=['research-profile.yaml'], source_refs=['research-profile.yaml'])
        wf.save(self.root / 'task.yaml', task)

    def configuration(self):
        config = wf.load(self.root / 'config/models.example.yaml')
        config.pop('subagent_profiles', None)
        config['model_profiles'] = {'manual': {'adapter': 'manual', 'timeout_seconds': 600}}
        config['orchestrator'] = {'adapter': 'codex', 'model': 'inherit', 'auth': 'external'}
        config['settings']['default_subagent_profile'] = 'manual'
        for role in config['subagents'].values():
            role['profile'] = None
        return config

    def api(self, adapter='openai_compatible', model='independent-model', key='ARBITRARY_MODEL_CREDENTIAL', **options):
        definition = dict(adapter=adapter, model=model, api_key_env=key,
                          base_url='https://model.invalid/v1', timeout_seconds=30)
        definition.update(options)
        return definition

    def response(self, text='测试草稿', finish='stop'):
        return io.BytesIO(json.dumps({'choices': [{'message': {'content': text}, 'finish_reason': finish}]},
                                    ensure_ascii=False).encode('utf-8'))

    def anthropic_response(self, stop='end_turn', blocks=None):
        data = {'content': blocks if blocks is not None else [{'type': 'text', 'text': 'Anthropic 草稿'}],
                'stop_reason': stop}
        return io.BytesIO(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    @staticmethod
    def request_headers(request):
        return {name.lower(): value for name, value in request.header_items()}

    def assert_no_credentials(self, run_dir, *credentials):
        text = '\n'.join(path.read_text(encoding='utf-8') for path in run_dir.iterdir() if path.is_file())
        text += self.output.getvalue()
        for credential in credentials:
            self.assertNotIn(credential, text)

    def test_arbitrary_openai_compatible_provider_uses_its_own_connection(self):
        config = self.api(provider='independent-vendor', request_options={'temperature': 0.1})
        os.environ[config['api_key_env']] = 'fake-independent-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.response()
            self.assertEqual(adapters.execute(config, '标准任务', self.root, True), ('draft', '测试草稿'))
            request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://model.invalid/v1/chat/completions')
        self.assertEqual(self.request_headers(request)['authorization'], 'Bearer fake-independent-credential')
        body = json.loads(request.data)
        self.assertEqual(body['model'], 'independent-model')
        self.assertEqual(body['messages'], [{'role': 'user', 'content': '标准任务'}])
        self.assertEqual(body['temperature'], 0.1)
        self.assertNotIn('thinking', body)

    def test_explicit_key_alias_and_primary_precedence(self):
        config = self.api(api_key_aliases=['other_model_key'])
        os.environ['other_model_key'] = 'fake-alias-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = [self.response(), self.response()]
            adapters.execute(config, '任务', self.root, True)
            self.assertEqual(self.request_headers(opener.return_value.open.call_args.args[0])['authorization'],
                             'Bearer fake-alias-credential')
            os.environ[config['api_key_env']] = 'fake-primary-credential'
            adapters.execute(config, '任务', self.root, True)
            self.assertEqual(self.request_headers(opener.return_value.open.call_args.args[0])['authorization'],
                             'Bearer fake-primary-credential')

    def test_legacy_deepseek_lowercase_key_is_accepted(self):
        config = self.api(provider='deepseek', model='test-ds', key='DEEPSEEK_API_KEY',
                          base_url='https://api.deepseek.com')
        os.environ['ds_apikey'] = 'fake-ds-lowercase-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.response()
            self.assertEqual(adapters.execute(config, '任务', self.root, True)[0], 'draft')
            request = opener.return_value.open.call_args.args[0]
        self.assertEqual(self.request_headers(request)['authorization'], 'Bearer fake-ds-lowercase-credential')

    def test_environment_values_win_over_dotenv_and_never_enter_logs(self):
        config = self.configuration()
        config['model_profiles']['alternate'] = self.api(key='MY_VENDOR_SECRET')
        config['settings']['default_subagent_profile'] = 'alternate'
        wf.save(self.root / 'config/models.local.yaml', config)
        (self.root / '.env').write_text('MY_VENDOR_SECRET="fake-local-credential"\n', encoding='utf-8')
        os.environ['MY_VENDOR_SECRET'] = 'fake-process-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.response()
            run_dir = wf.run(self.root, 'model-project', 'task.yaml', execute_external=True)
            request = opener.return_value.open.call_args.args[0]
        self.assertEqual(self.request_headers(request)['authorization'], 'Bearer fake-process-credential')
        self.assert_no_credentials(run_dir, 'fake-local-credential', 'fake-process-credential')

    def test_key_names_and_aliases_are_validated_without_network(self):
        for change in [{'api_key_env': 'invalid-name'}, {'api_key_aliases': 'one_key'},
                       {'api_key_aliases': ['invalid-name']}, {'api_key_aliases': [123]}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                adapters.check(dict(self.api(), **change), require_credentials=False)

    def test_process_alias_wins_over_dotenv_primary_and_dotenv_is_not_exported(self):
        config = self.configuration()
        config['model_profiles']['secondary'] = self.api(key='PRIMARY_VENDOR_KEY',
                                                        api_key_aliases=['process_vendor_key'])
        config['settings']['default_subagent_profile'] = 'secondary'
        wf.save(self.root / 'config/models.local.yaml', config)
        (self.root / '.env').write_text('PRIMARY_VENDOR_KEY=fake-dotenv-primary\n', encoding='utf-8')
        os.environ['process_vendor_key'] = 'fake-process-alias'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.response()
            run_dir = wf.run(self.root, 'model-project', 'task.yaml', True)
            request = opener.return_value.open.call_args.args[0]
        self.assertEqual(self.request_headers(request)['authorization'], 'Bearer fake-process-alias')
        self.assertNotIn('PRIMARY_VENDOR_KEY', os.environ)
        self.assert_no_credentials(run_dir, 'fake-dotenv-primary', 'fake-process-alias')

    def test_dotenv_lowercase_ds_key_supplies_legacy_role_without_environment_export(self):
        config = self.configuration()
        config['subagents']['literature-reader'].update(self.api(provider='deepseek', model='legacy-ds',
                                                                key='DEEPSEEK_API_KEY',
                                                                base_url='https://api.deepseek.com'))
        wf.save(self.root / 'config/models.local.yaml', config)
        (self.root / '.env').write_text('ds_apikey=fake-local-ds-key\n', encoding='utf-8')
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.response()
            run_dir = wf.run(self.root, 'model-project', 'task.yaml', True)
            request = opener.return_value.open.call_args.args[0]
        self.assertEqual(self.request_headers(request)['authorization'], 'Bearer fake-local-ds-key')
        self.assertNotIn('ds_apikey', os.environ)
        self.assertEqual(wf.load(run_dir / 'run.yaml')['requested_model'], 'legacy-ds')
        self.assert_no_credentials(run_dir, 'fake-local-ds-key')

    def test_anthropic_root_and_v1_urls_and_authentication(self):
        for base_url in ['https://anthropic.invalid', 'https://anthropic.invalid/v1/']:
            with self.subTest(base_url=base_url):
                config = self.api('anthropic', model='vendor-model', key='NONSTANDARD_ANTHROPIC_KEY',
                                  base_url=base_url, api_version='2023-06-01',
                                  request_options={'max_tokens': 73, 'temperature': 0.3})
                os.environ[config['api_key_env']] = 'fake-anthropic-credential'
                with patch('urllib.request.build_opener') as opener:
                    opener.return_value.open.return_value = self.anthropic_response()
                    self.assertEqual(adapters.execute(config, '完整任务包', self.root, True),
                                     ('draft', 'Anthropic 草稿'))
                    request = opener.return_value.open.call_args.args[0]
                self.assertEqual(request.full_url, 'https://anthropic.invalid/v1/messages')
                headers = self.request_headers(request)
                self.assertEqual(headers['x-api-key'], 'fake-anthropic-credential')
                self.assertEqual(headers['anthropic-version'], '2023-06-01')
                self.assertNotIn('authorization', headers)
                body = json.loads(request.data)
                self.assertEqual(body['model'], 'vendor-model')
                self.assertEqual(body['max_tokens'], 73)
                self.assertEqual(body['messages'][0]['content'], '完整任务包')

    def test_anthropic_keeps_text_blocks_and_discards_thinking(self):
        config = self.api('anthropic')
        os.environ[config['api_key_env']] = 'fake-anthropic-credential'
        blocks = [{'type': 'thinking', 'thinking': 'private-chain-of-thought'},
                  {'type': 'text', 'text': '第一部分'}, {'type': 'text', 'text': '第二部分'}]
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.anthropic_response(blocks=blocks)
            status, text = adapters.execute(config, '任务', self.root, True)
        self.assertEqual(status, 'draft')
        self.assertIn('第一部分', text)
        self.assertIn('第二部分', text)
        self.assertNotIn('private-chain-of-thought', text)

    def test_anthropic_marks_truncated_text_partial_and_rejects_empty_body(self):
        config = self.api('anthropic')
        os.environ[config['api_key_env']] = 'fake-anthropic-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = [self.anthropic_response(stop='max_tokens'),
                                                    self.anthropic_response(blocks=[{'type': 'thinking', 'thinking': 'internal'}])]
            self.assertEqual(adapters.execute(config, '任务', self.root, True)[0], 'partial')
            with self.assertRaises(ValueError):
                adapters.execute(config, '任务', self.root, True)

    def test_anthropic_vendor_options_are_not_restricted_to_deepseek_options(self):
        options = {'max_tokens': 4096, 'thinking': {'type': 'enabled', 'budget_tokens': 1024}}
        config = self.api('anthropic', request_options=options)
        os.environ[config['api_key_env']] = 'fake-anthropic-options-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.anthropic_response()
            self.assertEqual(adapters.execute(config, '任务', self.root, True)[0], 'draft')
            body = json.loads(opener.return_value.open.call_args.args[0].data)
        self.assertEqual(body['thinking'], options['thinking'])
        self.assertEqual(body['max_tokens'], 4096)

    def test_main_and_subagent_choose_independent_models_protocols_and_keys(self):
        config = self.configuration()
        config['model_profiles']['primary'] = self.api('anthropic', model='main-vendor-model', key='MY_PRIMARY_KEY',
                                                      base_url='https://main.invalid')
        config['model_profiles']['secondary'] = self.api(model='sub-vendor-model', key='MY_SECONDARY_KEY',
                                                        base_url='https://sub.invalid/v1')
        config['orchestrator'] = {'profile': 'primary'}
        config['settings']['default_subagent_profile'] = 'secondary'
        os.environ.update(MY_PRIMARY_KEY='fake-main-credential', MY_SECONDARY_KEY='fake-sub-credential')
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = [self.response('子模型草稿'), self.anthropic_response()]
            sub = wf.run(self.root, 'model-project', 'task.yaml', True, config)
            main = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
            calls = opener.return_value.open.call_args_list
        sub_request, main_request = [call.args[0] for call in calls]
        self.assertEqual(sub_request.full_url, 'https://sub.invalid/v1/chat/completions')
        self.assertEqual(main_request.full_url, 'https://main.invalid/v1/messages')
        self.assertEqual(json.loads(sub_request.data)['model'], 'sub-vendor-model')
        self.assertEqual(json.loads(main_request.data)['model'], 'main-vendor-model')
        self.assertEqual(self.request_headers(sub_request)['authorization'], 'Bearer fake-sub-credential')
        self.assertEqual(self.request_headers(main_request)['x-api-key'], 'fake-main-credential')
        sub_record, main_record = wf.load(sub / 'run.yaml'), wf.load(main / 'run.yaml')
        self.assertEqual(sub_record['execution_target'], 'subagent')
        self.assertEqual(main_record['execution_target'], 'main')
        self.assertEqual(main_record['effective_role'], 'orchestrator')
        self.assertEqual(main_record['requested_role'], 'literature-reader')
        self.assertEqual(main_record['model'], 'main-vendor-model')
        self.assertEqual(sub_record['model'], 'sub-vendor-model')
        for directory in [sub, main]:
            self.assert_no_credentials(directory, 'fake-main-credential', 'fake-sub-credential')
        self.assertIn('核对研究方向画像', (main / 'prompt.md').read_text(encoding='utf-8'))

    def test_direct_main_api_configuration_and_cli_main_flag(self):
        config = self.configuration()
        config['orchestrator'] = self.api(model='direct-main-model', key='DIRECT_MAIN_KEY')
        wf.save(self.root / 'config/models.local.yaml', config)
        os.environ['DIRECT_MAIN_KEY'] = 'fake-direct-main-credential'
        with patch.object(wf, 'ROOT', self.root), patch('urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = self.response('主模型草稿')
            self.assertEqual(wf.main(['run', 'model-project', 'task.yaml', '--main', '--execute']), 0)
            self.assertEqual(opener.return_value.open.call_count, 1)
            self.assertEqual(json.loads(opener.return_value.open.call_args.args[0].data)['model'], 'direct-main-model')
        record = wf.load(next((self.root / 'projects/model-project/.runs').glob('*/run.yaml')))
        self.assertEqual(record['execution_target'], 'main')
        self.assertEqual(record['status'], 'draft')

    def test_main_api_dry_run_never_requests_network(self):
        config = self.configuration()
        config['orchestrator'] = self.api(model='main-dry-run', key='MAIN_DRY_KEY')
        os.environ['MAIN_DRY_KEY'] = 'fake-main-dry-credential'
        run_dir = wf.run(self.root, 'model-project', 'task.yaml', config_override=config, use_main=True)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['status'], 'dry-run')
        self.assertEqual(record['execution_target'], 'main')
        self.assertFalse((run_dir / 'response.md').exists())

    def test_keyless_main_falls_back_to_manual_and_preserves_task(self):
        config = self.configuration()
        config['model_profiles']['primary'] = self.api(model='keyless-main', key='ABSENT_MAIN_KEY')
        config['orchestrator'] = {'profile': 'primary'}
        run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['execution_target'], 'main')
        self.assertEqual(record['status'], 'waiting-manual')
        self.assertEqual(record['effective_profile'], 'manual')
        self.assertEqual(record['requested_model'], 'keyless-main')
        self.assertTrue(record['fallback_reason'])
        self.assertTrue((run_dir / 'prompt.md').is_file())
        self.assertFalse((run_dir / 'response.md').exists())

    def test_keyless_subagent_does_not_borrow_main_provider_or_key(self):
        config = self.configuration()
        config['orchestrator'] = self.api(model='ready-main', key='READY_MAIN_KEY')
        config['model_profiles']['secondary'] = self.api(model='keyless-sub', key='ABSENT_SUB_KEY')
        config['settings']['default_subagent_profile'] = 'secondary'
        os.environ['READY_MAIN_KEY'] = 'fake-ready-main-credential'
        run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['status'], 'waiting-manual')
        self.assertEqual(record['execution_target'], 'subagent')
        self.assertEqual(record['requested_model'], 'keyless-sub')
        self.assertEqual(record['adapter'], 'manual')
        self.assert_no_credentials(run_dir, 'fake-ready-main-credential')

    def test_unknown_main_profile_falls_back_to_manual(self):
        config = self.configuration()
        config['orchestrator'] = {'profile': 'undefined-main'}
        run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['status'], 'waiting-manual')
        self.assertEqual(record['requested_profile'], 'undefined-main')
        self.assertEqual(record['effective_profile'], 'manual')

    def test_main_profile_with_list_adapter_falls_back_to_manual(self):
        config = self.configuration()
        config['model_profiles']['malformed-main'] = self.api(adapter=['openai_compatible'],
                                                             model='invalid-main-model', key='UNSET_MAIN_KEY')
        config['orchestrator'] = {'profile': 'malformed-main'}
        run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['status'], 'waiting-manual')
        self.assertEqual(record['execution_target'], 'main')
        self.assertEqual(record['effective_profile'], 'manual')
        self.assertTrue(record['fallback_reason'])
        self.assertTrue((run_dir / 'prompt.md').is_file())
        self.assertFalse((run_dir / 'response.md').exists())

    def test_main_command_receives_standard_task_on_stdin_without_shell(self):
        config = self.configuration()
        config['orchestrator'] = {'adapter': 'command', 'model': 'local-main',
                                  'command': ['main-model-client', '--stdin'], 'timeout_seconds': 42}
        with patch('shutil.which', return_value='fake-client-path'), patch('subprocess.run') as command:
            command.return_value.returncode = 0
            command.return_value.stdout = '本地主模型草稿'
            run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
        self.assertEqual(command.call_args.args[0], ['main-model-client', '--stdin'])
        self.assertIn('核对研究方向画像', command.call_args.kwargs['input'])
        self.assertFalse(command.call_args.kwargs['shell'])
        self.assertEqual(command.call_args.kwargs['timeout'], 42)
        self.assertEqual(wf.load(run_dir / 'run.yaml')['status'], 'draft')

    def test_command_credentials_are_passed_to_child_without_exporting_dotenv(self):
        config = self.configuration()
        config['orchestrator'] = {'adapter': 'command', 'model': 'wrapper-main',
                                  'command': ['model-wrapper'], 'timeout_seconds': 30}
        (self.root / '.env').write_text('LOCAL_WRAPPER_KEY=fake-wrapper-local\n'
                                      'SHARED_WRAPPER_KEY=fake-wrapper-local-shared\n', encoding='utf-8')
        os.environ['SHARED_WRAPPER_KEY'] = 'fake-wrapper-process-shared'
        with patch('shutil.which', return_value='fake-client-path'), patch('subprocess.run') as command:
            command.return_value.returncode = 0
            command.return_value.stdout = '封装程序草稿'
            run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
        child_environment = command.call_args.kwargs['env']
        self.assertEqual(child_environment['LOCAL_WRAPPER_KEY'], 'fake-wrapper-local')
        self.assertEqual(child_environment['SHARED_WRAPPER_KEY'], 'fake-wrapper-process-shared')
        self.assertNotIn('LOCAL_WRAPPER_KEY', os.environ)
        self.assert_no_credentials(run_dir, 'fake-wrapper-local', 'fake-wrapper-local-shared',
                                   'fake-wrapper-process-shared')

    def test_legacy_codex_main_profile_label_is_not_an_api_reference(self):
        config = self.configuration()
        config['orchestrator'] = {'adapter': 'codex', 'model': 'inherit', 'profile': 'main',
                                  'auth': 'external', 'api_key_env': None}
        normalized = wf.normalize_models(self.root, config)
        self.assertEqual(normalized['orchestrator']['adapter'], 'codex')
        self.assertEqual(normalized['orchestrator']['model'], 'inherit')
        run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['status'], 'waiting-manual')
        self.assertEqual(record['execution_target'], 'main')
        self.assertTrue((run_dir / 'prompt.md').is_file())

    def test_old_subagent_profiles_and_direct_role_settings_remain_compatible(self):
        config = self.configuration()
        config.pop('model_profiles')
        config['subagent_profiles'] = {'custom-legacy': self.api(model='legacy-profile-model')}
        config['settings']['default_subagent_profile'] = 'custom-legacy'
        config['subagents']['verifier'].update(self.api(model='legacy-direct-model'))
        normalized = wf.normalize_models(self.root, config)
        self.assertEqual(normalized['subagents']['literature-reader']['model'], 'legacy-profile-model')
        self.assertEqual(normalized['subagents']['verifier']['model'], 'legacy-direct-model')

    def test_shared_profile_role_override_does_not_change_other_roles_or_main(self):
        config = self.configuration()
        config['model_profiles'].update(primary=self.api(model='main-model'),
                                         default=self.api(model='default-sub-model'),
                                         reviewer=self.api('anthropic', model='reviewer-model'))
        config['orchestrator'] = {'profile': 'primary'}
        config['settings']['default_subagent_profile'] = 'default'
        config['subagents']['verifier']['profile'] = 'reviewer'
        original = copy.deepcopy(config)
        normalized = wf.normalize_models(self.root, config)
        self.assertEqual(normalized['orchestrator']['model'], 'main-model')
        self.assertEqual(normalized['subagents']['literature-reader']['model'], 'default-sub-model')
        self.assertEqual(normalized['subagents']['verifier']['model'], 'reviewer-model')
        self.assertEqual(config, original)

    def test_main_external_error_is_redacted_without_retry_or_provider_change(self):
        config = self.configuration()
        config['orchestrator'] = self.api(model='failing-main', key='FAILING_MAIN_KEY')
        os.environ['FAILING_MAIN_KEY'] = 'fake-failing-main-credential'
        with patch('urllib.request.build_opener') as opener:
            opener.return_value.open.side_effect = RuntimeError('fake-failing-main-credential sensitive-error-body')
            run_dir = wf.run(self.root, 'model-project', 'task.yaml', True, config, use_main=True)
            self.assertEqual(opener.return_value.open.call_count, 1)
        record = wf.load(run_dir / 'run.yaml')
        self.assertEqual(record['status'], 'waiting-manual')
        self.assertEqual(record['attempted_model'], 'failing-main')
        self.assertEqual(record['adapter'], 'manual')
        self.assert_no_credentials(run_dir, 'fake-failing-main-credential', 'sensitive-error-body')

    def test_http_adapters_reject_credential_urls_and_remote_plain_http(self):
        for adapter in ['openai_compatible', 'anthropic']:
            for base_url in ['https://user:password@model.invalid', 'http://model.invalid',
                             'https://model.invalid?api_key=secret']:
                with self.subTest(adapter=adapter, base_url=base_url), self.assertRaises(ValueError):
                    adapters.check(self.api(adapter, base_url=base_url), require_credentials=False)

    def test_anthropic_request_options_cannot_replace_routing_or_authentication(self):
        for field in ['model', 'messages', 'stream', 'api_key', 'authorization', 'headers']:
            with self.subTest(field=field), self.assertRaises(ValueError):
                adapters.check(self.api('anthropic', request_options={field: 'replacement'}), require_credentials=False)


if __name__ == '__main__':
    unittest.main()
