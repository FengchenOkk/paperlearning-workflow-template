"""静态任务接口校验：不读取私有配置，不调用模型或网络。"""
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class TaskContractDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.contracts = yaml.safe_load((ROOT / 'workflow/task-contracts.yaml').read_text(encoding='utf-8'))
        self.models = yaml.safe_load((ROOT / 'config/models.example.yaml').read_text(encoding='utf-8'))

    def test_every_routed_task_has_a_matching_contract_and_review_criteria(self):
        self.assertEqual(self.contracts['version'], 1)
        contracts = self.contracts['tasks']
        self.assertEqual(set(contracts), set(self.models['routing']))
        for task_type, contract in contracts.items():
            with self.subTest(task_type=task_type):
                self.assertEqual(contract['role'], self.models['routing'][task_type])
                self.assertIn(contract['role'], self.models['subagents'])
                criteria = contract['acceptance']
                self.assertTrue(criteria)
                self.assertEqual(len(criteria), len(set(criteria)))
                self.assertTrue(all(re.fullmatch(r'[a-z][a-z0-9_]*', item) for item in criteria))
                self.assertEqual(contract['max_attempts'], 3)

    def test_inputs_and_outputs_have_typed_stable_refs_and_bounded_context(self):
        for task_type, contract in self.contracts['tasks'].items():
            with self.subTest(task_type=task_type):
                self.assertTrue(contract['inputs'])
                self.assertTrue(contract['outputs'])
                for reference in contract['inputs']:
                    self.assertIsInstance(reference['type'], str)
                    self.assertIsInstance(reference['required'], bool)
                for reference in contract['outputs']:
                    self.assertIsInstance(reference['type'], str)
                    self.assertRegex(reference['id_template'], r'^[a-z][a-z.-]*:<[^>]+>')
                    output = reference['path'].replace('\\', '/')
                    self.assertFalse(output.startswith('/'))
                    self.assertNotIn('..', output.split('/'))
                    self.assertNotIn('.env', output.split('/'))
                limits = contract['context_limits']
                for key in ['max_chars', 'max_file_chars', 'max_total_bytes']:
                    self.assertIsInstance(limits[key], int)
                    self.assertGreater(limits[key], 0)
                self.assertLessEqual(limits['max_file_chars'], limits['max_chars'])
                self.assertLessEqual(limits['max_chars'], limits['max_total_bytes'])


if __name__ == '__main__':
    unittest.main()
