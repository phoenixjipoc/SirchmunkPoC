"""Export campaign results, source/answer diagnostics and paired comparisons."""
import argparse
import csv
import json
import random
import re
import statistics
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def read_csv(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))


def jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').split('\n') if s.strip()] if path.exists() else []


def write_csv(path,rows,fields=None):
    fields=fields or list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def mean_field(rows,key):
    values=[float(r[key]) for r in rows if r.get(key) not in ('',None)]
    return round(statistics.mean(values),4) if values else ''


def pct(n,d): return round(n/d*100,2) if d else ''


def summarize(stage,group,rows):
    labels=Counter(r['final_label'] for r in rows)
    positive=[r for r in rows if r['type']!='unanswerable']
    negative=[r for r in rows if r['type']=='unanswerable']
    lat=sorted(float(r['latency_s']) for r in rows)
    return {'stage':stage,'group':group,'n':len(rows),
        'correct':labels['correct'],'correct_refusal':labels['correct_refusal'],'partial':labels['partial'],
        'wrong':labels['wrong'],'hallucinated':labels['hallucinated'],'no_answer':labels['no_answer'],'error':labels['error'],
        'overall_correct_pct':pct(labels['correct']+labels['correct_refusal'],len(rows)),
        'initial_correct_pct':pct(sum(r.get('judge_label',r['final_label']) in ('correct','correct_refusal') for r in rows),len(rows)),
        'review_overrides':sum(r.get('judge_label',r['final_label'])!=r['final_label'] for r in rows),
        'independently_reviewed':sum(r.get('review_method','').startswith('coordinating_ai') for r in rows),
        'secondary_model_reviewed':sum(r.get('review_method')=='secondary_llm_reference_review' for r in rows),
        'mechanically_checked':sum(r.get('review_method','').startswith('deterministic_') for r in rows),
        'answerable_correct_pct':pct(sum(r['final_label']=='correct' for r in positive),len(positive)),
        'unanswerable_refusal_pct':pct(sum(r['final_label']=='correct_refusal' for r in negative),len(negative)),
        'unanswerable_hallucination_pct':pct(sum(r['final_label']=='hallucinated' for r in negative),len(negative)),
        'p50_s':round(statistics.median(lat),2) if lat else '',
        'p95_s':round(lat[min(len(lat)-1,round(.95*(len(lat)-1)))],2) if lat else '',
        'mean_s':round(statistics.mean(lat),2) if lat else '',
        'total_search_s':round(sum(lat),2),
        'total_tokens':sum(int(r['total_tokens'] or 0) for r in rows),
        'mean_tokens':round(statistics.mean(int(r['total_tokens'] or 0) for r in rows),2) if rows else '',
        'cluster_reuse_hits':sum(bool(r.get('reused_cluster_id') or r.get('reused_cluster')) for r in rows),
        'rga_timeouts':sum(r.get('rga_timeout')=='True' for r in rows),
        'serialization_errors':sum(bool(r.get('serialization_error')) for r in rows),
        'citation_trace_incomplete_count':sum(bool(r.get('citation_trace_incomplete')) for r in rows),
        'cited_coverage_observations':sum(r.get('gold_coverage_cited') not in ('',None) for r in rows),
        'gold_source_coverage_candidates':mean_field(rows,'gold_coverage_candidates'),
        'gold_source_coverage_sampled':mean_field(rows,'gold_coverage_sampled'),
        'gold_source_coverage_evidence':mean_field(rows,'gold_coverage_evidence'),
        'gold_source_coverage_found_evidence':mean_field(rows,'gold_coverage_found_evidence'),
        'gold_source_coverage_cited':mean_field(rows,'gold_coverage_cited')}


def diagnostic(row):
    label=row['final_label']
    if label=='error': return '运行异常'
    if label in ('correct','correct_refusal'): return ''
    if row.get('reused_cluster_id'): return '复用后回答有误或不完整；需核对是否复用了不适用的簇'
    if row['type']=='unanswerable': return '无答案题给出具体回答'
    if row.get('gold_coverage_candidates')=='0.0': return '候选文件未命中已知参考来源'
    if row.get('gold_coverage_sampled')=='0.0': return '有候选但采样文件未命中已知参考来源'
    if label=='no_answer': return '系统拒答；结合门控前答案与证据复核'
    if row.get('gold_coverage_found_evidence')=='0.0': return '未记录来自参考来源的肯定证据'
    return '证据内容或答案汇总不完整/错误；文件命中不能确定原因'


def generate(root):
    manifest=json.loads((root/'campaign.json').read_text(encoding='utf-8'))
    references={r['id']:r for r in read_csv(root/'inputs/questions.csv')}
    all_rows=[]; summaries=[]; paired=[]; review_queue=[]
    for stage in ('A','B','C'):
        directory=root/stage
        rows=read_csv(directory/'results_judged.csv')
        reviews={r['id']:r for r in jsonl(directory/'review_decisions.jsonl')}
        raw_records={r['id']:r for r in jsonl(directory/'results.jsonl')}
        for row in rows:
            review=reviews.get(row['id'],{})
            # Synthetic answer wrappers and reused clusters may lack evidence;
            # a directory-only citation also cannot identify individual sources.
            raw=raw_records.get(row['id'],{})
            cited=raw.get('cited_files',[])
            directory_only=bool(cited) and set(cited).issubset(set(raw.get('paths',[])))
            row['citation_trace_incomplete']=bool(row.get('serialization_error') and not row.get('cited_files')) or directory_only
            if row['citation_trace_incomplete']:
                row['gold_coverage_cited']=''
            row.update(stage=stage,final_label=review.get('final_label',row['judge_label']),
                       review_status='reviewed' if review else 'not_selected_or_pending',
                       review_method=review.get('reviewer',''),
                       review_note=review.get('note',''),question_ambiguity_note=review.get('question_ambiguity_note',''))
            row['execution_route']=('cluster_reuse' if row.get('reused_cluster_id') else
                                    'direct_document' if row.get('cluster_id','').startswith('DQ') else
                                    'search_or_other')
            row['diagnostic_hint']=diagnostic(row)
        all_rows.extend(rows)
        if rows:
            summaries.append(summarize(stage,'ALL',rows))
            for typ in ('detail','pair_a','pair_b','medium','broad','unanswerable'):
                summaries.append(summarize(stage,typ,[r for r in rows if r['type']==typ]))
        pairs={}
        for r in rows:
            if r['pair_id']: pairs.setdefault(r['pair_id'],{})[r['type']]=r
        for pair_id,p in pairs.items():
            a,b=p['pair_a'],p['pair_b']
            paired.append({'stage':stage,'pair_id':pair_id,'a_id':a['id'],'b_id':b['id'],
              'a_label':a['final_label'],'b_label':b['final_label'],
              'both_correct':a['final_label']==b['final_label']=='correct',
              'b_reused_cluster':bool(b.get('reused_cluster_id')),
              'b_reused_a_cluster':bool(b.get('reused_cluster_id')) and b['reused_cluster_id']==a.get('cluster_id'),
              'a_cluster_id':a.get('cluster_id',''),'b_reused_cluster_id':b.get('reused_cluster_id',''),
              'a_question':a['question'],'b_question':b['question'],
              'a_gold':a['gold_answer'],'b_gold':b['gold_answer'],'a_answer':a['answer'],'b_answer':b['answer']})
        # All problematic outputs plus a reproducible 20% sample of initially
        # correct/refusal outputs. Preserve the sample regardless of later edits.
        correct=sorted((r for r in rows if r['judge_label'] in ('correct','correct_refusal')),key=lambda r:r['id'])
        sample_ids={r['id'] for r in random.Random(20261014).sample(correct,max(1,(len(correct)+4)//5))} if correct else set()
        for r in rows:
            if r['judge_label'] not in ('correct','correct_refusal') or r['id'] in sample_ids:
                q=references[r['id']]
                review_queue.append({k:r.get(k,'') for k in ['stage','id','type','question','gold_answer','answer','judge_label','judge_reason','final_label','review_status','review_note','diagnostic_hint','evidence_files','cited_files','reused_cluster_id','error']} |
                                    {'gold_source_file':q['gold_source_file'],'gold_passage':q['gold_passage'],
                                     'acceptance_notes':q['verify_note'].split(' | Acceptance: ')[-1],
                                     'pre_gate_answer':r.get('pre_gate_answer','')})
    write_csv(root/'summary.csv',summaries,['stage','group','n','correct','correct_refusal','partial','wrong','hallucinated','no_answer','error','overall_correct_pct','initial_correct_pct','review_overrides','independently_reviewed','secondary_model_reviewed','mechanically_checked','answerable_correct_pct','unanswerable_refusal_pct','unanswerable_hallucination_pct','p50_s','p95_s','mean_s','total_search_s','total_tokens','mean_tokens','cluster_reuse_hits','rga_timeouts','serialization_errors','citation_trace_incomplete_count','cited_coverage_observations','gold_source_coverage_candidates','gold_source_coverage_sampled','gold_source_coverage_evidence','gold_source_coverage_found_evidence','gold_source_coverage_cited'])
    write_csv(root/'all_results.csv',all_rows)
    write_csv(root/'paired_results.csv',paired)
    write_csv(root/'review_queue.csv',review_queue)
    write_csv(root/'failure_cases.csv',[r for r in all_rows if r['final_label'] not in ('correct','correct_refusal')])
    route_rows=[]
    for stage in ('A','B','C'):
        for route in ('search_or_other','direct_document','cluster_reuse'):
            subset=[r for r in all_rows if r['stage']==stage and r['execution_route']==route]
            if subset:route_rows.append(summarize(stage,route,subset))
    write_csv(root/'execution_routes.csv',route_rows)
    comparisons=[]
    by_stage={s:{r['id']:r for r in all_rows if r['stage']==s} for s in ('A','B','C')}
    for qid,q in references.items():
        row={'id':qid,'type':q['type'],'question':q['question'],'gold_answer':q['gold_answer']}
        for s in ('A','B','C'):
            r=by_stage[s].get(qid,{})
            row.update({s+'_'+k:r.get(k,'') for k in ('final_label','latency_s','total_tokens','reused_cluster_id','answer')})
        comparisons.append(row)
    write_csv(root/'question_comparison.csv',comparisons)
    transitions=[]
    for alternative in ('B','C'):
        common=set(by_stage['A']) & set(by_stage[alternative])
        if not common:continue
        counts=Counter()
        for qid in common:
            a=by_stage['A'][qid]['final_label'] in ('correct','correct_refusal')
            b=by_stage[alternative][qid]['final_label'] in ('correct','correct_refusal')
            counts['both_correct' if a and b else 'regressions' if a else 'gains' if b else 'neither_correct']+=1
        transitions.append({'baseline':'A','alternative':alternative,'n':len(common),
                            **{k:counts[k] for k in ('both_correct','gains','regressions','neither_correct')}})
    write_csv(root/'transition_summary.csv',transitions)
    matched_reuse=[]
    for reused,name in ((True,'C_reuse_hit'),(False,'C_no_reuse_hit')):
        ids={r['id'] for r in all_rows if r['stage']=='C' and bool(r.get('reused_cluster_id'))==reused}
        if not ids:continue
        for stage in ('A','C'):
            subset=[r for r in all_rows if r['stage']==stage and r['id'] in ids]
            if subset:matched_reuse.append(summarize(stage,name,subset))
    write_csv(root/'reuse_matched_comparison.csv',matched_reuse)
    reuse_cases=[]
    origins={}
    for raw in jsonl(root/'C/results.jsonl'):
        cluster=raw.get('cluster_id')
        reused=raw.get('reused_cluster_id')
        if reused:
            origin=origins.get(reused,{})
            final=by_stage['C'].get(raw['id'],{})
            raw_path=root/'C/raw'/f"{raw['id']}.json"
            detail=json.loads(raw_path.read_text(encoding='utf-8')) if raw_path.exists() else {}
            messages=[log.get('msg','') for log in detail.get('logs',[]) if isinstance(log,dict)]
            similarities=[m.group(1) for msg in messages
                          if (m:=re.search(r'Found similar cluster:.*?similarity: ([0-9.]+)',msg))]
            reuse_cases.append({'id':raw['id'],'source_question_id':origin.get('id',''),
                'cluster_id':reused,'logged_similarity':similarities[-1] if similarities else '',
                'question':raw['question'],'source_question':origin.get('question',''),
                'gold_answer':references[raw['id']]['gold_answer'],'answer':raw['answer'],
                'source_answer':origin.get('answer',''),
                'same_answer_as_origin':raw['answer']==origin.get('answer'),
                'final_label':final.get('final_label',''),'review_note':final.get('review_note',''),
                'latency_s':raw['latency_s'],'total_tokens':raw['total_tokens'],
                'reused_cluster_queries':json.dumps(raw.get('reused_cluster_queries',[]),ensure_ascii=False)})
        elif cluster:
            origins.setdefault(cluster,raw)
    write_csv(root/'reuse_cases.csv',reuse_cases)
    sensitivity=[summarize(stage,'exclude_ambiguous_SVC-15',[r for r in all_rows if r['stage']==stage and r['id']!='SVC-15'])
                 for stage in ('A','B','C') if by_stage[stage]]
    write_csv(root/'sensitivity.csv',sensitivity)
    complete=manifest['state']=='complete' and len(all_rows)==360
    outstanding=[(r['stage'],r['id']) for r in review_queue if r['review_status']!='reviewed']
    progress=[]
    for stage in ('A','B','C'):
        log=root/stage/'execution.log'
        numbers=re.findall(r'^\[(\d+)/120\]',log.read_text(encoding='utf-8',errors='replace'),flags=re.M) if log.exists() else []
        progress.append({'stage':stage,'search_completed':int(numbers[-1]) if numbers else 0,
                         'state':manifest['stages'].get(stage,{}).get('state','pending')})
    md=['# Sirchmunk 120 题 A → B → C 测试报告','',
        '报告生成时间：'+datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')+'。','',
        f"状态：{'三轮执行完成' if complete else '运行中／阶段性结果'}；已评分 {len(all_rows)}/360 条。要求复核的记录还有 {len(outstanding)} 条未完成。",'',
        '搜索进度：'+'；'.join(f"{p['stage']} {p['search_completed']}/120（{p['state']}）" for p in progress)+'。','',
        '## 固定条件','',
        f"81 份原始文档；同一份独立核验的 120 题；DEEP；模型 `{manifest['model']}`；Sirchmunk `{manifest['sirchmunk_version']}`。A=k10/复用关，B=k5/复用关，C=k10/复用开（阈值0.85）。每轮空知识簇起步，同一题序，15 对题均 A题紧接B题。共享预热后的文本解析缓存。",'',
        '## 总体结果','',
        '|配置|题数|正确（含正确拒答）|部分正确|错误/幻觉|无答案|异常|正确率|P50秒|P95秒|总token|复用命中|',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for s in summaries:
        if s['group']!='ALL': continue
        md.append('|'+ '|'.join(str(v) for v in [s['stage'],s['n'],s['correct']+s['correct_refusal'],s['partial'],s['wrong']+s['hallucinated'],s['no_answer'],s['error'],str(s['overall_correct_pct'])+'%',s['p50_s'],s['p95_s'],s['total_tokens'],s['cluster_reuse_hits']])+'|')
    totals={s['stage']:s for s in summaries if s['group']=='ALL'}
    for stage,s in totals.items():
        md.extend(['',f"{stage} 初评正确率 {s['initial_correct_pct']}%；协调AI复核 {s['independently_reviewed']} 条，同模型独立请求复核 {s['secondary_model_reviewed']} 条，确定性拒答/异常检查 {s['mechanically_checked']} 条；调整初评标签 {s['review_overrides']} 条。表中使用复核后的最终标签；未选中或待复核条目沿用初评。"])
        if s['serialization_errors']:
            md.extend(['',f"{stage} 另有 {s['serialization_errors']} 条 SearchContext 序列化异常，脚本从返回对象恢复答案并保存异常。它们仍参与评分，不能据此声称 HTTP 接口可用性正常。"])
        md.extend(['',f"{stage} 的最终引用文件覆盖率有 {s['cited_coverage_observations']} 条可观测记录；{s['citation_trace_incomplete_count']} 条结果的来源追踪不完整（可能包含无答案题）。比较覆盖率时需同时查看缺失数。"])
        md.extend(['',f"{stage} 平均单题搜索耗时 {s['mean_s']} 秒，120题单题耗时之和 {round(s['total_search_s']/60,2)} 分钟；不包含预热、评分、复核和导出。"])
    if 'A' in totals and 'B' in totals:
        a,b=totals['A'],totals['B']
        md.extend(['',f"A 相对 B：正确率变化 {a['overall_correct_pct']-b['overall_correct_pct']:+.2f} 个百分点；P50 变化 {a['p50_s']-b['p50_s']:+.2f} 秒；搜索总 token 变化 {a['total_tokens']-b['total_tokens']:+,}。"])
    if 'A' in totals and 'C' in totals:
        a,c=totals['A'],totals['C']
        md.extend(['',f"C 相对 A：正确率变化 {c['overall_correct_pct']-a['overall_correct_pct']:+.2f} 个百分点；P50 变化 {c['p50_s']-a['p50_s']:+.2f} 秒；搜索总 token 变化 {c['total_tokens']-a['total_tokens']:+,}。"])
    if transitions:
        md.extend(['','|对照|两轮均正确|新答对|原来正确、本轮不正确|两轮均不完全正确|',
                   '|---|---:|---:|---:|---:|'])
        for t in transitions:
            md.append(f"|{t['alternative']} 对 A|{t['both_correct']}|{t['gains']}|{t['regressions']}|{t['neither_correct']}|")
    if sensitivity:
        md.extend(['','敏感性检查：排除存在措辞歧义的 SVC-15（主结果仍保留该题）后，'+
                   '；'.join(f"{r['stage']} 为 {r['overall_correct_pct']}%（{r['n']}题）" for r in sensitivity)+'。'])
    md.extend(['','## 按题型拆分','',
               '|题型|题数|A 正确数 / 正确率|B 正确数 / 正确率|C 正确数 / 正确率|',
               '|---|---:|---:|---:|---:|'])
    groups={(r['stage'],r['group']):r for r in summaries}
    type_counts=Counter(q['type'] for q in references.values())
    for typ,name in [('detail','细节题'),('pair_a','相似题 A'),('pair_b','相似题 B'),
                     ('medium','中等题'),('broad','跨文档综合题'),('unanswerable','无答案题')]:
        values=[]
        for stage in ('A','B','C'):
            g=groups.get((stage,typ))
            values.append(f"{g['correct']+g['correct_refusal']} / {g['overall_correct_pct']}%" if g else '待完成')
        md.append('|'+ '|'.join([name,str(type_counts[typ]),*values])+'|')
    md.extend(['','## 相似题与无答案题','', '|配置|15对中两题全对|B题发生复用|B题复用了配对A题簇|9道无答案题正确拒答|无答案题编造回答|', '|---|---:|---:|---:|---:|---:|'])
    for stage,s in totals.items():
        ps=[p for p in paired if p['stage']==stage]
        md.append(f"|{stage}|{sum(p['both_correct'] for p in ps)} / {len(ps)}|{sum(p['b_reused_cluster'] for p in ps)}|{sum(p['b_reused_a_cluster'] for p in ps)}|{s['correct_refusal']} / 9|{s['hallucinated']} / 9|")
    md.extend(['','## 实际执行路径','',
        'DEEP 配置仍保留库内意图分流。DQ 前缀簇表示直接文档分析；复用由返回对象中的复用簇ID识别，其余归入检索或其他路径。它们的题目不同，分组指标仅描述本次观测。','',
        '|配置|路径|题数|正确率|P50秒|总token|',
        '|---|---|---:|---:|---:|---:|'])
    for r in route_rows:
        md.append(f"|{r['stage']}|{r['group']}|{r['n']}|{r['overall_correct_pct']}%|{r['p50_s']}|{r['total_tokens']}|")
    if matched_reuse:
        md.extend(['','按 C 的实际复用命中划分问题，再取 A 中相同题号作描述性对照。分组由 C 的行为决定，且仍有模型随机性，差异不全是复用的因果效果。','',
            '|C分组|同题数|A正确率|C正确率|A平均秒|C平均秒|A平均token|C平均token|',
            '|---|---:|---:|---:|---:|---:|---:|---:|'])
        for name in ('C_reuse_hit','C_no_reuse_hit'):
            gs={r['stage']:r for r in matched_reuse if r['group']==name}
            if 'A' in gs and 'C' in gs:
                a,c=gs['A'],gs['C']
                md.append(f"|{name}|{c['n']}|{a['overall_correct_pct']}%|{c['overall_correct_pct']}%|{a['mean_s']}|{c['mean_s']}|{a['mean_tokens']}|{c['mean_tokens']}|")
    md.extend(['','## 口径与限制','',
       '- 总体正确率以全部120题为分母，部分正确不算正确，错误和运行异常不会被剔除。111道可回答题与9道无答案题另见 summary.csv。',
       '- 搜索进程收到的是题号和问题，检索范围为81份原始文档；冻结标准答案与核验接受标准仅供后续评分、复核使用，不作为搜索提示或检索语料。',
       '- 文件覆盖率按每题命中的参考来源数/已知参考来源数计算。候选、采样、证据、is_found证据、最终簇引用分别统计；复用跳过新检索时候选为空不代表没使用缓存证据。命中文件不等于关键事实有依据。',
       '- 若序列化异常导致缺失来源元数据，或最终引用仅记录搜索目录而没有具体文件，最终引用覆盖率记为未知并排除该项均值；不会将缺失观测强行算作检索失败。',
       '- 同一模型进行搜索和初评；初评使用冻结的参考答案、原文及核验接受标准。review_queue.csv 覆盖所有非正确结果和随机20%的初判正确/正确拒答结果。第二遍使用独立请求、不提供初评标签，但仍是同一配置模型，不能消除同模型偏差；协调AI复核与分歧裁定另行记录。明确无结果/异常可按冻结题目可答性确定性检查，不冒充语义复核。',
       '- 15 对相似题、9 道无答案题样本较小；一次对照未消除模型与采样随机性，不声称统计显著或证明1000–2000份文件规模的效果。',
       '- 15 对近似问法但答案不同的题是特意安排的串答压力测试；C 评估本轮不同问题之间的复用，观测命中率不代表真实业务的问题分布。',
       '- INREV 旧 DOC 的证据抽取返回63927个字符，但开头大量乱码并有240个替代字符；部分英文仍保留。rga 关键词预检仅得到二进制匹配。记作解析与检索限制，三轮均未替换或转换原始文档。',
       '- 延迟是单题搜索耗时，不包含预热、评分、复核和导出。搜索 token 与评分 token 分开保存；不估算货币费用。API内部失败重试可能未返回可计量token。',
       '- 本轮在 llm.achat 调用边界汇总成功返回的 usage，覆盖采样等子组件；旧脚本仅汇总库内部分 usage 列表，口径可能不同。A/B/C 内部可比，旧48题 token 不直接拼接比较。max_token_budget 是运行时默认参数，不保证并行调用后的实测 token 不超出该值。',
       '- 本轮通过容器内 AgenticSearch SDK 运行，便于记录候选与证据。SearchContext 序列化异常单独记录；从对象恢复出答案不代表对应 HTTP 接口也能正常返回。本轮没有测 HTTP 端到端可用性。',
       '- DEEP 的意图分流可能提前返回直接文档分析答案，绕过关键词、目录排名与证据采样；这类题的表现不能直接归因于 top_k。安装版本的相关源代码片段保存在 inputs/direct_doc_analysis_source.txt。',
       '- no_answer 专指脚本识别到的固定无结果响应；其他明确拒答若参考答案存在，按冻结评分规则归入 wrong。wrong 因此不等于所有答案都编造了具体事实。',
       '- failure_cases.csv 中的错误原因提示是诊断线索，不等于已证实的根因。最终结论需结合原文和调用日志。',
       '- 旧48题结果保持原样；新结果不与旧百分比直接拼接。','',
       '- 复核发现 SVC-15 的措辞风险：只写 KCERA audit services，未写 financial 或年份；语料同时有财务审计（3+最多3年）和精算审计（1年）。按冻结参考来源计分，但将另一文件的真实引文与编造区分；题目限定词留待下版修改，本轮三组均不改题。详见 question_scope_caveats.json。','',
       '## 导出文件','',
       '- test_process.md / events.jsonl：流程、时间、命令、状态。',
       '- summary.csv：按配置与题型的指标；question_comparison.csv：逐题A/B/C对照。',
       '- all_results.csv / failure_cases.csv / paired_results.csv：逐题、失败案例和15对题结果。',
       '- execution_routes.csv：实际执行路径分组的描述性指标。',
       '- transition_summary.csv / sensitivity.csv：逐题正确性迁移统计及排除歧义题后的敏感性检查。',
       '- reuse_matched_comparison.csv：按C实际命中分组，提取A相同题号进行对照。',
       '- reuse_cases.csv：每次实际复用的来源题、相似度、原答案、当前题标准答案及复核结论。',
       '- review_queue.csv：复核清单；各阶段 review_decisions.jsonl：复核裁定。',
       '- A、B、C目录：运行配置、冻结题库、完整执行日志、原始JSON、初评分和知识簇CSV/JSONL。',
       '- inputs、preflight.json：冻结输入/代码和81份文档的哈希、解析检查。'])
    findings=root/'final_findings.md'
    if complete and not outstanding and findings.exists():
        index=md.index('## 固定条件')
        md[index:index]=[findings.read_text(encoding='utf-8').strip(),'']
    (root/'test_report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    status={'search_and_judge_complete':complete,'graded_records':len(all_rows),'required_review_records':len(review_queue),
            'reviewed_records':len(review_queue)-len(outstanding),'pending_reviews':outstanding,
            'search_progress':progress,
            'export_complete':complete and not outstanding}
    (root/'export_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(status,ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('campaign_dir',type=Path);args=ap.parse_args();generate(args.campaign_dir)
