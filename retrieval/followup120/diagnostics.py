"""Describe stage completeness and replay ordering without changing any score."""
from pathlib import Path
import json
from prepare_support import HERE,read,save,results


def main():
    groups=results()
    names={r['file'] for r in read(HERE/'inputs/corpus.json')}
    directory=[]
    for group in ['R1','R2','R3','D']:
        for qid,r in groups[group].items():
            prompt=r.get('directory_prompt','')
            shown={n for n in names if n in prompt}
            ranked=r.get('directory_ranking',[])
            high=[Path(c.get('path','')).name for c in ranked if c.get('relevance')=='high']
            directory.append(dict(group=group,id=qid,filenames_present_in_prompt=len(shown),
                                  parsed_rank_records=len(ranked),high_count=len(high),
                                  high_files_absent_from_prompt=sorted(set(high)-shown)))
    legacy=next(n for n in names if n.endswith('.doc'))
    parser=[]
    for qid in groups['R1']:
        lists={g:[Path(p).name for p in groups[g][qid]['keyword_files']] for g in ['R1','P0','P']}
        parser.append(dict(id=qid,original_vs_control_order_equal=lists['R1']==lists['P0'],
             control_vs_repaired_order_equal=lists['P0']==lists['P'],
             nonlegacy_order_equal=[p for p in lists['P0'] if p!=legacy]==[p for p in lists['P'] if p!=legacy],
             nonlegacy_set_equal=set(lists['P0'])-{legacy}==set(lists['P'])-{legacy},
             legacy_in_original=legacy in lists['R1'],legacy_in_control=legacy in lists['P0'],legacy_in_repaired=legacy in lists['P']))
    snapshot=read(HERE/'inputs/directory_scan.json')['candidates']
    snapshot_summary=dict(files=len(snapshot),full_content_files=sum(bool(r.get('full_content')) for r in snapshot),
                          max_preview_chars=max(len(r.get('preview') or '') for r in snapshot),
                          max_full_content_chars=max(len(r.get('full_content') or '') for r in snapshot),
                          full_content_sources=[dict(file=r['filename'],characters=len(r['full_content'])) for r in snapshot if r.get('full_content')])
    summary=dict(snapshot=snapshot_summary,directory={g:dict(
        min_prompt_files=min(r['filenames_present_in_prompt'] for r in directory if r['group']==g),
        max_prompt_files=max(r['filenames_present_in_prompt'] for r in directory if r['group']==g),
        min_parsed_rank_records=min(r['parsed_rank_records'] for r in directory if r['group']==g),
        max_parsed_rank_records=max(r['parsed_rank_records'] for r in directory if r['group']==g),
        queries_with_high_file_not_in_prompt=sum(bool(r['high_files_absent_from_prompt']) for r in directory if r['group']==g))
        for g in ['R1','R2','R3','D']},
        parser=dict(original_vs_control_order_changes=sum(not r['original_vs_control_order_equal'] for r in parser),
                    control_vs_repaired_order_changes=sum(not r['control_vs_repaired_order_equal'] for r in parser),
                    nonlegacy_order_changes=sum(not r['nonlegacy_order_equal'] for r in parser),
                    nonlegacy_set_changes=sum(not r['nonlegacy_set_equal'] for r in parser),
                    legacy_discovered_control=sum(r['legacy_in_control'] for r in parser),
                    legacy_discovered_repaired=sum(r['legacy_in_repaired'] for r in parser)))
    save(HERE/'reports/stage_diagnostics.json',dict(summary=summary,directory_queries=directory,parser_queries=parser))
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
