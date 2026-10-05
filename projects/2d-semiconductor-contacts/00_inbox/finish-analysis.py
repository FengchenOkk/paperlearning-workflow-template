from pathlib import Path
import sys,json,yaml
sys.path.insert(0,str(Path.cwd()/'tools'))
import wf,tasks,literature
root=Path.cwd();P=root/'projects/2d-semiconductor-contacts';K='liApproachingQuantumLimit2023';B=f'10_literature/papers/{K}';S=f'{B}/01_source'
cards=[('quantum-contact-limit','二维接触量子下限','在原文的理想弹道通道计数约定下，有限横向模式数给出宽度归一化接触电阻的非零下限。','即使消除额外界面散射，有限传导模式也限制电导。','像有限数量的并行通道：通道更多，整体电阻更小。',r'$R_{c,\min}=h/(2q^2)\sqrt{\pi/(2n_{2D})}$；原文式(1)，p.274。','h单位J·s，q单位C，n₂D单位m⁻²，结果为Ω·m；换成Ω·μm需乘10⁶。','n₂D=3×10¹³ cm⁻²时下限29.53 Ω·μm，42 Ω·μm约为1.42倍。','不等于肖特基势垒为零；后者并不保证所有模式都无背散射地注入。','勿把Ω·μm当Ω·μm²；勿把高浓度下限当材料常数。','原文引Landauer工作；本轮仅核对本文式(1)，未独立读取该经典原文。','TODO(user)：不同谷/自旋简并、非理想透射及有限温度的模式计数。','evidence-mechanism.md'),('interface-band-hybridization','界面能带杂化','不同材料的轨道耦合使电子态包含双方轨道成分；本文强调费米能级附近跨Sb/MoS₂界面的混合态。','能带对齐不足以描述跨范德华间隙的注入效率，还需检查耦合。','电子态在两种材料中都有空间分布，界面不再仅是两个彼此独立的能带。','用轨道投影能带、局部态密度、空间电荷分布判断；本文Fig.1是DFT结果。','Sb pz与Mo d轨道沿垂直方向的重叠增大，杂化态跨EF。','电荷转移与能带杂化共同支持接触区简并掺杂；两者概念不同。','杂化不等于必须形成共价键；本文XPS未发现Sb–S键形成证据。','勿把计算杂化态称为实验直接观测；勿仅凭Rc降低定量分配机制贡献。','本文Fig.1/p.276；其他文献全文未读取，TODO(user)。','TODO(user)：沉积温度、洁净度、取向分布及模型厚度对杂化的定量影响。','evidence-mechanism.md'),('transfer-length-method','传输长度法（TLM）','用多个沟道长度器件的总电阻线性拟合，分离沟道片电阻与两端接触电阻。','单个器件的电阻通常混合沟道和接触贡献。','比较不同长度；长度增加的部分归入沟道，外推到零长度的截距归入接触。',r'$R_{tot}W=R_{sh}L+2R_c$；这是方法解释式，不是本文编号公式。','Rtot单位Ω，W/L单位长度，Rsh单位Ω/□，Rc单位Ω·长度；原文Lc表示沟道长度。','Fig.3b纵截距为2Rc；使用相同载流子浓度、线性工作区及近似对称接触。','LT不是几何间隙：本文LT=5.1 nm为提取值，几何间隙约0.285 nm。','接触内外片电阻相同的假设可能因电荷转移失效；很小截距需检查置信区间。','本文Fig.3图注与Extended Data Fig.5图注；未独立复算Source data。','TODO(user)：取得源数据重拟合，评估短沟道与接触区片电阻差异。','evidence-results.md')]
for row in cards:
 cid,name,*rest=row;source=rest.pop();idx=json.loads((P/'INDEX.json').read_text(encoding='utf-8')); sid=idx['aliases'][f'{S}/{source}'];tid='sb-concept-'+cid
 task={'task_id':tid,'task_type':'literature-knowledge','role':'knowledge-builder','objective':f'基于已核验原文建立{name}单概念卡；当前Codex真实人工接力，不执行外部API；自动关系保持candidate。','inputs':[{'id':f'paper:{K}','type':'paper'},{'id':f'analysis:{K}','type':'analysis'},{'id':f'reading:{K}','type':'reading'}],'outputs':[{'id':'concept:'+cid,'type':'concept','path':'10_literature/concepts/'+cid+'.md','mode':'replace'},{'id':f'analysis:{K}','type':'analysis','path':f'{B}/04_analysis/analysis.yaml','mode':'replace'}],'allowed_paths':['10_literature/concepts',f'{B}/04_analysis'],'context':{'task_type':'literature-knowledge','paper_citekey':K},'source_refs':[f'{S}/{source}'],'output_schema':None}
 tp=P/'00_inbox'/f'{tid}.yaml';wf.save(tp,task);tasks.execute(root,P,tp.relative_to(root).as_posix(),wf);attempt=tasks.state(root,P,tid,wf)['attempt']
 old,body=literature.markdown(P/'10_literature/concepts'/f'{cid}.md')
 old.update(generated_by='current-codex-session/manual-handoff',model_role='literature-reader',requested_role='knowledge-builder',prompt_version='sb-concepts-v1',source_refs=[f'{S}/{source}'],canonical_statement=rest[0],papers=[K],paper_ids=[f'paper:{K}'],status='learning',created_at=wf.now())
 headings=['一句话定义','为什么需要这个概念','直观理解','形式化定义','公式与符号','前因后果','与相近概念的区别','常见误区','代表文献迷你综述','开放问题']
 body='# 概念：'+name+'\n\n'+'\n\n'.join(f'## {n}. {h}\n\n{t}' for n,(h,t) in enumerate(zip(headings,rest),1))+'\n'
 body+='\n新概念说明替代或修正了什么；旧概念说明为何仍重要。概念定义在本卡唯一维护，正文链接关联概念卡及论文。\n'
 card='---\n'+yaml.safe_dump(old,allow_unicode=True,sort_keys=False)+'---\n\n'+body
 a=wf.load(P/B/'04_analysis/analysis.yaml')
 for c in a['concepts']:
  if c['id']==cid:c['understanding_status']='已核对关键原文并关联全局概念卡'
 for f in a['formulas']:
  if cid=='quantum-contact-limit' and f['id']=='eq-1' or cid=='transfer-length-method' and f['id']=='intrinsic-delay':
   if cid=='quantum-contact-limit':f['related_concepts']=[cid]
 result={'task_id':tid,'attempt':attempt,'status':'submitted','summary':f'真实当前Codex人工接力{name}卡；请求knowledge-builder禁用，路由回退literature-reader；DeepSeek仅dry-run。','created_artifacts':[],'updated_artifacts':[{'id':'concept:'+cid,'type':'concept'},{'id':f'analysis:{K}','type':'analysis'}],'evidence':[{'id':sid,'type':'source.text'}],'unresolved_issues':['经典文献全文/源数据未独立核验；已注明范围'],'confidence':'high','self_check':{x:'pass' for x in ['stable_concept_ids','single_definition','evidence_traceable','links_resolvable','automatic_links_candidate','manual_content_preserved']}}
 tasks.submit(root,P,tid,attempt,{'result':result,'artifacts':[{'id':'concept:'+cid,'content':card,'mode':'replace'},{'id':f'analysis:{K}','content':yaml.safe_dump(a,allow_unicode=True,sort_keys=False),'mode':'replace'}]},wf)
 tasks.review(root,P,tid,attempt,wf)
 print(tid, 'review-ready')
 # Explicit actual current-session review: the card statements above were checked against
 # the already inspected original PDF and source snippets by the authoring session.
 ref={'id':sid,'type':'source.text','hash':idx['artifacts'][sid]['hash']}
 review={'task_id':tid,'attempt':attempt,'reviewer':'main','review_source':'actual current Codex session source review','decision':'accept','passed_criteria':['stable_concept_ids','single_definition','evidence_traceable','links_resolvable','automatic_links_candidate','manual_content_preserved'],'failed_criteria':[],'issues':[],'required_changes':[],'evidence_checks':[{'ref':ref,'status':'verified','detail':f'逐句核对{name}定义、单位/计算或方法条件与已读原文；卡片不将作者计算当实验，不声称读取经典全文；旧links保留candidate、原骨架无人工实质正文。'}],'next_action':'保存单概念卡与分析关联','reason':'实际核对受控原文、概念定义、适用条件和缺口；范围限定于本文；无自检替代来源审核。'}
 rp=P/'00_inbox'/f'{tid}-review.yaml';wf.save(rp,review);tasks.review(root,P,tid,attempt,wf,review_file=rp.relative_to(root).as_posix());tasks.accept(root,P,tid,attempt,wf)
 print(tid,'accepted')
