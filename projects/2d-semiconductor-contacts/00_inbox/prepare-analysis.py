from pathlib import Path
import sys, json, math
sys.path.insert(0, str(Path.cwd()/'tools'))
import wf
P=Path.cwd()/'projects/2d-semiconductor-contacts'
K='liApproachingQuantumLimit2023'
B=f'10_literature/papers/{K}'
lines=(P/B/'01_source/paper-reading.txt').read_text(encoding='utf-8').splitlines()
pieces={
 'evidence-mechanism.md':[(42,66),(306,318),(636,710)],
 'evidence-results.md':[(938,973),(1108,1208),(621,632)],
 'evidence-methods.md':[(1366,1449)]}
for name,ranges in pieces.items():
 text='# Extracted evidence; read-only derivative of Zotero PDF\n\nSource: paper-reading.txt; original PDF DOI 10.1038/s41586-022-05431-4.\nExtraction drops superscripts and overbars: use PDF for formulas and Sb crystal index.\n\n'
 for a,b in ranges:text+=f'## Original extracted text L{a}-{b}\n\n'+'\n'.join(lines[a-1:b])+'\n\n'
 if name=='evidence-mechanism.md':text+='## Visually verified equation (1), PDF p.274\n\nRc,min = h/(2 q^2) * sqrt(pi/(2 n2D)). Rc is width-normalized (ohm length). Sb contact plane is (01\\bar{1}2), NOT unbarred (0112). This line is a checked transcription, not extracted text.\n'
 (P/B/'01_source'/name).write_text(text,encoding='utf-8')
 print(name,len(text))
m=wf.load(P/B/'meta.yaml')
m['source_files']=[f'{B}/01_source/{n}' for n in ['paper.txt','paper-reading.txt',*pieces]]
m['source_refs']=[f'{B}/01_source/source-links.yaml']
m['paper_role']='method';m['categories']=['二维半导体接触'];m['next_action']='完成全局分析与证据审核'
wf.save(P/B/'meta.yaml',m)
wf.index(Path.cwd(),P.name)
idx=json.loads((P/'INDEX.json').read_text(encoding='utf-8'))
refs=[]
for n in pieces:
 path=f'{B}/01_source/{n}'
 ident=idx['aliases'][path]
 refs.append({'id':ident,'type':idx['artifacts'][ident]['type'],'required':True})
task={'task_id':'sb-contact-first-pass','task_type':'literature-first-pass','role':'literature-reader','objective':'依据受控原文完成全局定位、论文逻辑链及关键机制/实验/边界分析；区分作者声称、计算与实验证据、读者推断。非全文翻译、非逐节精读。当前 Codex 会话作为真实人工接力撰写草稿，再由主模型独立核对证据；不调用付费 API。','inputs':[{'id':f'paper:{K}','type':'paper','required':True},*refs,{'id':'artifact:2d-semiconductor-contacts:research-profile','type':'research-profile','required':False}],'outputs':[{'id':f'reading:{K}','type':'reading','path':f'{B}/03_reading/reading.md','mode':'replace'},{'id':f'analysis:{K}','type':'analysis','path':f'{B}/04_analysis/analysis.yaml','mode':'replace'}],'allowed_paths':[f'{B}/03_reading',f'{B}/04_analysis'],'context':{'task_type':'literature-first-pass','paper_citekey':K},'output_schema':None,'source_refs':[f'{B}/01_source/{n}' for n in pieces]}
wf.save(P/'00_inbox/sb-contact-first-pass.yaml',task)
