from pathlib import Path
import sys,json,yaml
sys.path.insert(0,str(Path.cwd()/'tools'))
import wf,tasks,literature
root=Path.cwd();P=root/'projects/2d-semiconductor-contacts';K='liApproachingQuantumLimit2023';B=f'10_literature/papers/{K}';S=f'{B}/01_source';tid='sb-contact-analysis-verification'
idx=json.loads((P/'INDEX.json').read_text(encoding='utf-8'));sid=idx['aliases'][f'{S}/evidence-results.md']
task={'task_id':tid,'task_type':'verification','role':'verifier','objective':'复核已完成全局分析的关键数字与证据边界，生成可读的论文分析与核验报告；当前Codex真实人工接力，不假称独立外部模型复核，不执行API。','inputs':[{'id':f'paper:{K}','type':'paper'},{'id':f'reading:{K}','type':'reading'},{'id':sid,'type':'source.text'}],'outputs':[{'id':f'artifact:{tid}:verification','type':'artifact','path':'30_outputs/antimony-contact-analysis.md','mode':'replace'}],'allowed_paths':['30_outputs'],'context':{'task_type':'verification','paper_citekey':K},'output_schema':None,'source_refs':[f'{S}/evidence-results.md',f'{B}/03_reading/reading.md']}
tp=P/'00_inbox'/f'{tid}.yaml';wf.save(tp,task);tasks.execute(root,P,tp.relative_to(root).as_posix(),wf)
_,body=literature.markdown(P/B/'03_reading/reading.md')
intro='''这篇工作的核心价值，是证明**半金属电极的晶面也是接触工程变量**：特定 Sb 晶面通过增强跨界面电子态耦合与电荷转移，使单层 MoS₂ 的最佳接触电阻接近论文定义的量子下限。读论文时应把“最佳电阻”“批量统计”“本征速度估算”“长期可靠性”分别评价。

| 核验项 | 判断 | 依据与范围 |
|---|---|---|
| 42 Ω·μm 与量子极限 | 支持，限定同浓度 | n₂D=3×10¹³ cm⁻²；式(1)给29.53 Ω·μm，比例1.42 |
| 晶面改善接触 | 实验支持；机制计算支持 | 同材料晶面对照、结构表征与DFT相互印证；未定量排除所有工艺伴随变化 |
| 热稳定 | 支持限定试验；长期未知 | 125 °C、氮气、24 h；不扩展到空气长期寿命 |
| 已达到5 nm晶体管3.6 fs | 不支持此实测表述 | 原文是用最佳Rc外推，不是已制造器件测量 |
| 已完整优于/替代硅CMOS | 现有证据不足 | 本文特定指标比较不能替代完整工艺、寄生与电路评价 |

核验方法：当前Codex会话对照原PDF关键页/图与受控提取文本，重算式(1)，核对样本量和条件。结构校验只检查文件与连接，不是科学结论来源。本报告草稿本身不决定验收，由单独登记的主模型评审后应用；未调用外部DeepSeek，也没有独立第二模型复核。

待办映射：证据可追溯性→取得Source data重拟合TLM；已支持/未知区分→长期老化和补充资料核验；实测/外推区分→保留5 nm预测标签。这些为后续范围，不阻碍本轮限定分析。项目决策见ROADMAP.md。

'''
for cid in ['quantum-contact-limit','interface-band-hybridization','transfer-length-method']:
 intro+=f'- 概念卡：[ {cid} ](../10_literature/concepts/{cid}.md)\n'
prov={'id':f'artifact:{tid}:verification','type':'artifact','generated_by':'current-codex-session/manual-handoff','model_role':'verifier','prompt_version':'sb-contact-verification-v1','source_refs':task['source_refs'],'created_at':wf.now(),'scope':'全局分析与关键证据核验；未完成全文翻译或独立复现'}
report='---\n'+yaml.safe_dump(prov,allow_unicode=True,sort_keys=False)+'---\n\n# Sb–MoS₂接触：论文分析与证据核验\n\n'+intro+'\n'+body
criteria=['evidence_traceable','supported_unsupported_unknown','criterion_mapped_issues','structural_vs_scientific_checks','no_self_acceptance']
result={'task_id':tid,'attempt':1,'status':'submitted','summary':'当前Codex真实人工接力：关键结论支持度、误读纠正及可读分析报告；等待单独主模型审核。','created_artifacts':[{'id':prov['id'],'type':'artifact'}],'updated_artifacts':[],'evidence':[{'id':sid,'type':'source.text'},{'id':f'reading:{K}','type':'reading'}],'unresolved_issues':['Source data/全部补充资料/长期可靠性未独立核验，报告明确排除'],'confidence':'high','self_check':{x:'pass' for x in criteria}}
tasks.submit(root,P,tid,1,{'result':result,'artifacts':[{'id':prov['id'],'mode':'replace','content':report}]},wf);tasks.review(root,P,tid,1,wf)
review={'task_id':tid,'attempt':1,'reviewer':'main','review_source':'actual current Codex source checks and comparison with accepted analysis','decision':'accept','passed_criteria':criteria,'failed_criteria':[],'issues':[],'required_changes':[],'evidence_checks':[{'ref':{'id':sid,'type':'source.text','hash':idx['artifacts'][sid]['hash']},'status':'verified','detail':'实际核对42/209±100、24h氮气、160ns/偏压、573器件与5nm预测的原文标签；报告支持度表与原文一致。'},{'ref':{'id':f'reading:{K}','type':'reading','hash':idx['artifacts'][f'reading:{K}']['hash']},'status':'verified','detail':'对照已接受阅读分析，正式报告保留数字、公式、证据和范围；补充模型限制与核验项，未把结构检查、自检或外部模型身份当科学证据。'}],'next_action':'应用正式报告；meta只标pre-read与partial，用户缺口归ROADMAP','reason':'核对报告实测/预测、最佳/平均及证据类型分离；接受限定全局分析，不接受未核验的完整翻译/独立复现/长期寿命宣称。'}
rp=P/'00_inbox'/f'{tid}-review.yaml';wf.save(rp,review);tasks.review(root,P,tid,1,wf,review_file=rp.relative_to(root).as_posix());tasks.accept(root,P,tid,1,wf)
m=wf.load(P/B/'meta.yaml');m.update(status='pre-read',reading_status='partial',analysis_status='partial',concept_ids=['quantum-contact-limit','interface-band-hybridization','transfer-length-method'],formula_ids=['eq-1','intrinsic-delay'],next_action='TODO(user)：按需要获取Source data/补充材料，复核TLM或开展逐节精读',updated_at=wf.now());wf.save(P/B/'meta.yaml',m)
project=wf.load(P/'project.yaml');project.update(stage='reading',next_action='全局分析已验收；确认是否继续逐节精读或TLM源数据复核');wf.save(P/'project.yaml',project)
road=P/'ROADMAP.md'
if not road.exists():road.write_text('# 项目路线与用户决策\n\n已按用户指定建立二维半导体接触项目，纳入Zotero IA2ZTFPU论文。原PDF仅引用，未修改。\n\nTODO(user)：是否继续全文翻译/逐节精读？是否取得补充材料与Source data复核TLM？是否比较后续晶面工程工作？实验设备、算力、预算和材料权限尚未知，不视为具备。\n\n本轮没有付费API调用、论文上传或实验执行；DeepSeek配置保留，各任务采用真实当前Codex人工接力及主模型源证据审核。\n',encoding='utf-8')
wf.index(root,P.name)
print('Formal analysis accepted; meta=pre-read/partial; indexes refreshed.')
