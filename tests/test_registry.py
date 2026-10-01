"""Offline identity, connection and integrity checks for the machine index."""
from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import shutil
from types import SimpleNamespace
import unittest
import yaml

from tools import registry, storage


def load(path):
    value = yaml.safe_load(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(value,dict):
        raise ValueError('mapping required')
    return value


def contained(base,value):
    base = Path(base).resolve()
    path = (base/value).resolve()
    if not path.is_relative_to(base):
        raise ValueError('outside')
    return path


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.p = self.root/'projects/research'
        self.paper = self.p/'10_literature/papers/Paper2024'
        self.ops = SimpleNamespace(load=load,contained=contained,now=lambda:'2026-10-01T00:00:00+00:00')
        self.put('project.yaml','slug: research\ntitle: Human title\nstage: intake\n# Keep this comment\n')
        self.put('research-profile.yaml','direction: Human research direction\n')
        self.put('10_literature/papers/Paper2024/meta.yaml',
                 'citekey: Paper2024\ntitle: Human paper title\nconcept_ids: [energy]\n'
                 'categories: [物理]\nsource_files: [10_literature/papers/Paper2024/01_source/source.txt]\n'
                 'zotero:\n  item_key: ABCD1234\n')
        self.put('10_literature/papers/Paper2024/01_source/source.txt','Original source text.\n')
        self.put('10_literature/papers/Paper2024/04_analysis/analysis.yaml',
                 'paper: Paper2024\nformulas:\n  - id: eq-one\n    latex: E = mc^2\n'
                 '    related_concepts: [energy]\n    source_refs: []\nfirst_principles: []\nconcepts: []\n'
                 'overview:\n  core_problem: Preserve scientific interpretation\n')
        for folder,name in [('02_translation','translation'),('03_reading','reading')]:
            self.put(f'10_literature/papers/Paper2024/{folder}/{name}.md',
                     '---\ngenerated_by: human\n# Keep front matter comment\n---\n\n'
                     '# Human heading\n\nExact human text, including trailing spaces.  \n')
        self.put('10_literature/concepts/energy.md','---\nconcept_id: energy\ntype: foundational\n'
                 'papers: [Paper2024]\nprerequisites: []\n---\n\n# Human energy explanation\n')

    def put(self,rel,content):
        path = self.p/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(content,encoding='utf-8')
        return path

    def build(self,**kwargs):
        return registry.build(self.root,self.p,self.ops,**kwargs)

    def test_core_ids_links_and_types(self):
        index = self.build()
        self.assertEqual(index['issues'],[])
        self.assertEqual(index['project_id'],'project:research')
        for identifier in ['paper:Paper2024','analysis:Paper2024','translation:Paper2024',
                           'reading:Paper2024','concept:energy','formula:Paper2024:eq-one',
                           'topic:物理','artifact:research:research-profile']:
            self.assertIn(identifier,index['artifacts'])
        self.assertEqual(index['aliases']['zotero:ABCD1234'],'paper:Paper2024')
        concept=load_front(self.p/'10_literature/concepts/energy.md')
        self.assertEqual(concept['type'],'foundational')
        self.assertEqual(concept['object_type'],'concept')
        self.assertTrue(all(link['status']=='candidate' for link in index['links']))
        analysis=load(self.paper/'04_analysis/analysis.yaml')
        self.assertEqual(analysis['formulas'][0]['id'],'eq-one')
        self.assertEqual(analysis['formulas'][0]['object_id'],'formula:Paper2024:eq-one')

    def test_repeated_build_bytes_are_identical(self):
        self.build()
        files={p.relative_to(self.p):p.read_bytes() for p in self.p.rglob('*') if p.is_file()}
        self.build()
        self.assertEqual(files,{p.relative_to(self.p):p.read_bytes() for p in self.p.rglob('*') if p.is_file()})

    def test_markdown_body_and_comments_are_preserved(self):
        path=self.paper/'03_reading/reading.md'
        old=path.read_text(encoding='utf-8').split('---',2)[2]
        self.build()
        self.assertEqual(old,path.read_text(encoding='utf-8').split('---',2)[2])
        self.assertIn('# Keep front matter comment',path.read_text(encoding='utf-8'))
        self.assertIn('# Keep this comment',(self.p/'project.yaml').read_text(encoding='utf-8'))

    def test_renamed_paper_keeps_ids_and_old_aliases_after_index_deletion(self):
        self.build()
        moved=self.paper.with_name('RenamedPaper')
        self.paper.rename(moved)
        meta=load(moved/'meta.yaml')
        meta['citekey']='RenamedPaper'
        meta['source_files']=['10_literature/papers/RenamedPaper/01_source/source.txt']
        storage.write_text(moved/'meta.yaml',yaml.safe_dump(meta,allow_unicode=True,sort_keys=False))
        (self.p/'INDEX.json').unlink()
        index=self.build()
        self.assertIn('paper:Paper2024',index['artifacts'])
        self.assertEqual(index['aliases']['paper:RenamedPaper'],'paper:Paper2024')
        self.assertEqual(index['aliases']['paper:Paper2024'] if 'paper:Paper2024' in index['aliases'] else 'paper:Paper2024','paper:Paper2024')
        self.assertEqual(index['artifacts']['paper:Paper2024']['path'],'10_literature/papers/RenamedPaper/meta.yaml')

    def test_source_file_rename_keeps_registered_identity(self):
        index=self.build()
        source_id=next(i for i,r in index['artifacts'].items() if r['type']=='source.text')
        original=self.paper/'01_source/source.txt'
        original.rename(original.with_name('renamed.txt'))
        meta=load(self.paper/'meta.yaml')
        meta['source_files']=['10_literature/papers/Paper2024/01_source/renamed.txt']
        storage.write_text(self.paper/'meta.yaml',yaml.safe_dump(meta,allow_unicode=True,sort_keys=False))
        index=self.build()
        self.assertEqual(index['artifacts'][source_id]['path'],'10_literature/papers/Paper2024/01_source/renamed.txt')

    def test_dry_run_and_readonly_build_do_not_write(self):
        before={p.relative_to(self.p):p.read_bytes() for p in self.p.rglob('*') if p.is_file()}
        self.build(dry_run=True)
        self.build(write=False)
        self.assertEqual(before,{p.relative_to(self.p):p.read_bytes() for p in self.p.rglob('*') if p.is_file()})

    def test_duplicate_id_reports_without_stopping_scan(self):
        self.put('10_literature/concepts/duplicate.md','---\nid: concept:energy\nconcept_id: duplicate\ntype: classic\n---\nHuman\n')
        index=self.build()
        self.assertIn('concept:energy',index['duplicates'])
        self.assertIn('paper:Paper2024',index['artifacts'])
        with self.assertRaisesRegex(ValueError,'重复'):
            registry.resolve(self.p,'concept:energy',self.ops,index=index)

    def test_dangling_link_has_local_warning_and_other_objects_survive(self):
        meta=load(self.paper/'meta.yaml')
        meta['links']=[dict(rel='uses',target='concept:missing',evidence=[{'file':'project.yaml','field':'title'}],confidence='high',status='verified')]
        storage.write_text(self.paper/'meta.yaml',yaml.safe_dump(meta,allow_unicode=True))
        index=self.build()
        self.assertTrue(any('悬空 link target：concept:missing'==error for error in index['issues']))
        self.assertIn('formula:Paper2024:eq-one',index['artifacts'])

    def test_manual_link_takes_precedence_over_legacy_migration(self):
        meta=load(self.paper/'meta.yaml')
        link=dict(rel='uses',target='concept:energy',evidence=[{'file':'project.yaml','field':'title'}],confidence='high',status='verified',review_note='Human decision')
        meta['links']=[deepcopy(link)]
        storage.write_text(self.paper/'meta.yaml',yaml.safe_dump(meta,allow_unicode=True))
        index=self.build()
        rows=[r for r in index['links'] if r['source']=='paper:Paper2024' and r['target']=='concept:energy' and r['rel']=='uses']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['review_note'],'Human decision')
        self.assertEqual(load(self.paper/'meta.yaml')['links'][1 if load(self.paper/'meta.yaml')['links'][0]['rel']=='belongs-to-topic' else 0]['status'],'verified')

    def test_resolver_uses_index_path_not_supplied_path(self):
        index=self.build()
        ref=registry.resolve(self.p,{'id':'paper:Paper2024','path':'../../.env','role':'output'},self.ops,index=index)
        self.assertEqual(ref['path'],'10_literature/papers/Paper2024/meta.yaml')
        self.assertEqual(ref['role'],'output')
        self.assertEqual(ref['id'],'paper:Paper2024')

    def test_resolver_rejects_stale_current_or_input_hash(self):
        index=self.build()
        self.paper.joinpath('meta.yaml').write_text(self.paper.joinpath('meta.yaml').read_text(encoding='utf-8')+'# New human comment\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'hash'):
            registry.resolve(self.p,'paper:Paper2024',self.ops,index=index)
        index=self.build()
        with self.assertRaisesRegex(ValueError,'hash'):
            registry.resolve(self.p,{'id':'paper:Paper2024','hash':'sha256:bad'},self.ops,index=index)

    def test_formula_anchor_resolves_and_unknown_anchor_is_rejected(self):
        index=self.build()
        ref=registry.resolve(self.p,'formula:Paper2024:eq-one',self.ops,index=index)
        self.assertEqual(ref['anchor'],'formulas[0]')
        with self.assertRaisesRegex(ValueError,'anchor'):
            registry.resolve(self.p,{'id':'reading:Paper2024','anchor':'missing'},self.ops,index=index)
        self.assertEqual(registry.resolve(self.p,{'id':'reading:Paper2024','anchor':'human-heading'},self.ops,index=index)['anchor'],'human-heading')

    def test_registration_keeps_identity_when_artifact_moves(self):
        self.put('30_outputs/result.txt','Human draft\n')
        index=registry.register(self.root,self.p,self.ops,[dict(id='artifact:result',type='artifact',path='30_outputs/result.txt')])
        self.assertIn('artifact:result',index['artifacts'])
        self.p.joinpath('30_outputs/result.txt').rename(self.p/'30_outputs/moved.txt')
        index=registry.register(self.root,self.p,self.ops,[dict(id='artifact:result',type='artifact',path='30_outputs/moved.txt')])
        self.assertEqual(registry.resolve(self.p,'artifact:result',self.ops,index=index)['path'],'30_outputs/moved.txt')

    def test_registration_rejects_private_config_and_escape_before_writing(self):
        before=self.p.joinpath('project.yaml').read_bytes()
        self.put('.env','not-a-real-key')
        self.put('config/models.local.yaml','model: test\n')
        for unsafe in ['.env','config/models.local.yaml','../outside.txt']:
            with self.assertRaises(ValueError):
                registry.register(self.root,self.p,self.ops,[dict(id='artifact:private',path=unsafe)])
        self.assertEqual(before,self.p.joinpath('project.yaml').read_bytes())

    def test_task_status_and_attempt_are_indexed(self):
        self.put('.runs/check/task.yaml','id: check\nrole: literature-reader\n')
        self.put('.runs/check/status.yaml','task_id: check\nstatus: submitted\nattempt: 1\n')
        self.put('.runs/check/attempts/1/result.yaml','task_id: check\nattempt: 1\nstatus: submitted\n')
        index=self.build()
        self.assertEqual(index['tasks']['task:check']['status'],'submitted')
        self.assertIn('task:check',index['artifacts'])
        self.assertIn('attempt:check:1',index['artifacts'])

    def test_bad_links_do_not_stop_or_destroy_human_document(self):
        self.put('10_literature/concepts/bad.md','---\nconcept_id: bad\ntype: current\nlinks: [invalid]\n---\n\nHuman exact body\n')
        index=self.build()
        self.assertIn('损坏 link：concept:bad',index['issues'])
        self.assertIn('paper:Paper2024',index['artifacts'])
        self.assertTrue(self.p.joinpath('10_literature/concepts/bad.md').read_text(encoding='utf-8').endswith('\n\nHuman exact body\n'))

    def test_nested_first_principle_card_is_one_canonical_node(self):
        self.put('10_literature/concepts/energy.md','---\nconcept_id: energy\ntype: foundational\nis_first_principle: true\npapers: [Paper2024]\n---\nHuman body\n')
        data=load(self.paper/'04_analysis/analysis.yaml')
        data['first_principles']=[dict(id='energy',statement='Human principle',concept_ids=['energy'],source_refs=['project.yaml'])]
        storage.write_text(self.paper/'04_analysis/analysis.yaml',yaml.safe_dump(data,allow_unicode=True))
        index=self.build()
        self.assertIn('principle:energy',index['artifacts'])
        self.assertNotIn('principle:energy',index['duplicates'])
        self.assertTrue(any(e['source']=='principle:energy' and e['target']=='concept:energy' for e in index['links']))

    def test_validator_reports_unsafe_and_invalid_evidence(self):
        index=self.build()
        index['artifacts']['artifact:unsafe']=dict(type='artifact',path='../../outside.txt',hash='sha256:bad')
        index['links'].append(dict(source='paper:Paper2024',rel='uses',target='concept:energy',evidence=[{'file':'.env'}],confidence='medium',status='candidate'))
        issues=registry.validate(index,self.p,self.ops)
        self.assertIn('artifact 路径不安全：artifact:unsafe',issues)
        self.assertIn('link 证据路径不安全：.env',issues)

    def test_plain_artifact_ref_and_contract_type_round_trip(self):
        self.put('30_outputs/plan.md','# Draft plan\n')
        index=registry.register(self.root,self.p,self.ops,[dict(id='artifact:plan',type='artifact',path='30_outputs/plan.md',contract_type='claim.plan')])
        ref=registry.resolve(self.p,'artifact:plan',self.ops,index=index)
        self.assertEqual(ref['contract_type'],'claim.plan')
        self.assertEqual(yaml.safe_load(yaml.safe_dump(ref)),ref)

    def test_line_anchor_supported_on_source_text(self):
        index=self.build()
        identifier=next(i for i,r in index['artifacts'].items() if r['type']=='source.text')
        ref=registry.resolve(self.p,dict(id=identifier,anchor='L1'),self.ops,index=index)
        self.assertEqual(ref['anchor'],'L1')
        with self.assertRaisesRegex(ValueError,'anchor'):
            registry.resolve(self.p,dict(id=identifier,anchor='L99'),self.ops,index=index)

    def test_malformed_id_and_alias_are_reported_without_scan_crash(self):
        self.put('10_literature/concepts/bad.md','---\nid: [bad]\nconcept_id: bad\ntype: current\n---\nHuman\n')
        data=load(self.p/'project.yaml')
        data['id_aliases']={'bad':['not-an-id']}
        storage.write_text(self.p/'project.yaml',yaml.safe_dump(data,allow_unicode=True))
        index=self.build()
        self.assertIn('无效持久别名：bad',index['issues'])
        self.assertIn('无法索引概念：10_literature/concepts/bad.md',index['issues'])
        self.assertIn('paper:Paper2024',index['artifacts'])

    def test_legacy_claim_identity_uses_claim_slug_and_keeps_aliases(self):
        self.put('20_reproduction/Paper2024--main/claim.yaml',
                 'claim_id: Paper2024--main\npaper_citekey: Paper2024\nformula_ids: [eq-one]\nconcept_ids: [energy]\n')
        index=self.build()
        self.assertIn('claim:Paper2024:main',index['artifacts'])
        self.assertEqual(index['aliases']['Paper2024--main'],'claim:Paper2024:main')
        self.assertEqual(index['aliases']['claim:Paper2024--main'],'claim:Paper2024:main')
        self.assertTrue(any(e['source']=='claim:Paper2024:main' and e['target']=='formula:Paper2024:eq-one' for e in index['links']))

    def test_embedded_identity_additions_preserve_yaml_formula_comments(self):
        path=self.paper/'04_analysis/analysis.yaml'
        text=path.read_text(encoding='utf-8').replace('latex: E = mc^2','latex: E = mc^2  # Human formula explanation')
        storage.write_text(path,text)
        index=self.build()
        self.assertIn('# Human formula explanation',path.read_text(encoding='utf-8'))
        self.assertIn('formula:Paper2024:eq-one',index['artifacts'])
        self.assertNotIn('安全追加失败，原件保留：10_literature/papers/Paper2024/04_analysis/analysis.yaml',index['issues'])

    def test_yaml_key_anchor_is_resolved_and_missing_field_rejected(self):
        index=self.build()
        ref=registry.resolve(self.p,dict(id='analysis:Paper2024',anchor='overview.core_problem'),self.ops,index=index)
        self.assertEqual(ref['anchor'],'overview.core_problem')
        with self.assertRaisesRegex(ValueError,'anchor'):
            registry.resolve(self.p,dict(id='analysis:Paper2024',anchor='formulas[9].latex'),self.ops,index=index)

    def test_owned_zotero_source_links_has_a_resolvable_stable_artifact(self):
        self.put('10_literature/papers/Paper2024/01_source/source-links.yaml',
                 'id: artifact:Paper2024:source-links\ntype: artifact\ncontract_type: paper.source.links\n'
                 'paper_id: paper:Paper2024\nlinks: []\nattachments: []\n')
        index=self.build()
        ref=registry.resolve(self.p,'artifact:Paper2024:source-links',self.ops,index=index)
        self.assertEqual(ref['contract_type'],'paper.source.links')
        self.assertEqual(ref['path'],'10_literature/papers/Paper2024/01_source/source-links.yaml')

    def test_registered_formal_front_matter_links_are_single_source(self):
        self.put('30_outputs/report.md','---\nid: artifact:report\ntype: artifact\nlinks:\n'
                 '  - rel: uses\n    target: concept:energy\n    evidence:\n'
                 '      - file: project.yaml\n        field: title\n    confidence: high\n    status: verified\n'
                 '---\n\nHuman report\n')
        index=registry.register(self.root,self.p,self.ops,[dict(id='artifact:report',type='artifact',path='30_outputs/report.md',links=[dict(rel='uses',target='concept:missing')])])
        links=[link for link in index['links'] if link['source']=='artifact:report']
        self.assertEqual(len(links),1)
        self.assertEqual(links[0]['target'],'concept:energy')
        registration=next(row for row in load(self.p/'project.yaml')['artifact_registry'] if row['id']=='artifact:report')
        self.assertNotIn('links',registration)
        self.assertEqual(registry.validate(index,self.p,self.ops),[])

    def test_draft_body_official_id_does_not_change_registered_draft_identity(self):
        self.put('.runs/check/task.yaml','id: task:check\nrole: literature-reader\n')
        self.put('.runs/check/status.yaml','task_id: check\nstatus: submitted\nattempt: 1\n')
        self.put('.runs/check/attempts/1/result.yaml','task_id: check\nattempt: 1\nstatus: submitted\n')
        draft=self.put('.runs/check/attempts/1/drafts/1.md','---\nid: reading:Paper2024\nlinks: []\n---\n\nCandidate\n')
        index=registry.register(self.root,self.p,self.ops,[dict(id='artifact:check:draft-1',type='artifact',path=draft.relative_to(self.p).as_posix(),links=[dict(rel='generated-from',target='attempt:check:1',evidence=[{'file':'.runs/check/attempts/1/result.yaml','field':'status'}],confidence='high',status='candidate')])])
        self.assertEqual(index['artifacts']['reading:Paper2024']['path'],'10_literature/papers/Paper2024/03_reading/reading.md')
        self.assertEqual(registry.resolve(self.p,'artifact:check:draft-1',self.ops,index=index)['path'],draft.relative_to(self.p).as_posix())
        self.assertTrue(any(link['source']=='artifact:check:draft-1' and link['target']=='attempt:check:1' for link in index['links']))


def load_front(path):
    return yaml.safe_load(path.read_text(encoding='utf-8').split('---',2)[1])


class RegistryLiteratureMoveTests(unittest.TestCase):
    def setUp(self):
        from tools import wf
        self.wf=wf
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        for rel in ['config','workflow']:
            # Vendored research material is irrelevant to these offline cases.
            shutil.copytree(wf.ROOT/rel,self.root/rel,ignore=shutil.ignore_patterns('vendor'))
        for rel in ['.gitignore','.env.example']:
            shutil.copyfile(wf.ROOT/rel,self.root/rel)
        for rel in ['tools','tests']:(self.root/rel).mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            wf.bootstrap(self.root)
            wf.init(self.root,'research','Identity compatibility')
            self.paper=wf.new_paper(self.root,'research','Paper2024')
            self.card=wf.new_concept(self.root,'research','energy')
        self.project=self.root/'projects/research'

    def test_index_and_validate_after_paper_and_card_move(self):
        from tools import literature
        source=self.paper/'01_source/source.txt'
        source.write_text('Original scientific source',encoding='utf-8')
        meta=self.wf.load(self.paper/'meta.yaml')
        meta.update(concept_ids=['energy'],source_files=[source.relative_to(self.project).as_posix()])
        self.wf.save(self.paper/'meta.yaml',meta)
        reading=self.paper/'03_reading/reading.md'
        storage.write_text(reading,reading.read_text(encoding='utf-8')+'\nManual [energy](../../../concepts/energy.md) explanation.\n')
        self.wf.index(self.root,'research')
        moved=self.paper.with_name('renamed-paper')
        self.paper.rename(moved)
        self.card.rename(self.card.with_name('renamed-card.md'))
        old_meta=moved.joinpath('meta.yaml').read_bytes()
        self.wf.index(self.root,'research')
        with contextlib.redirect_stdout(io.StringIO()):
            self.wf.validate(self.root,'research')
        index=registry.load_index(self.project)
        self.assertEqual(index['artifacts']['paper:Paper2024']['path'],'10_literature/papers/renamed-paper/meta.yaml')
        self.assertEqual(index['artifacts']['concept:energy']['path'],'10_literature/concepts/renamed-card.md')
        self.assertIn('papers/renamed-paper/',self.project.joinpath('INDEX.md').read_text(encoding='utf-8'))
        self.assertEqual(literature.resolve_path(self.project,'10_literature/concepts/energy.md',self.wf),self.card.with_name('renamed-card.md'))
        self.assertEqual(self.wf.load(moved/'meta.yaml')['citekey'],'Paper2024')
        self.assertTrue(old_meta)

    def test_changed_citekey_reading_notes_stay_visible_by_stable_id(self):
        from tools import literature
        reading_list=self.project/'10_literature/reading-list.md'
        info,body=literature.markdown(reading_list)
        info.update(reading_notes={'Paper2024':'Human reason'},reading_order=['Paper2024'])
        literature.write_markdown(reading_list,info,body)
        moved=self.paper.with_name('RenamedPaper')
        self.paper.rename(moved)
        meta=self.wf.load(moved/'meta.yaml')
        meta['citekey']='RenamedPaper'
        self.wf.save(moved/'meta.yaml',meta)
        self.wf.index(self.root,'research')
        with contextlib.redirect_stdout(io.StringIO()):
            self.wf.validate(self.root,'research')
        self.assertIn('Human reason',reading_list.read_text(encoding='utf-8'))
        self.assertEqual(registry.load_index(self.project)['aliases']['paper:RenamedPaper'],'paper:Paper2024')


if __name__=='__main__':
    unittest.main()

