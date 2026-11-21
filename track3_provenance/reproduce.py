"""Track 3. Offline benchmark transfer smoke and native source custody replay."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

def offline(event,args):
 if event.startswith('socket.') and event != 'socket.gethostname': raise RuntimeError('NETWORK_BLOCKED')
sys.addaudithook(offline)

LAB=Path(r"F:\SDL_SCIENTIFIC_DISCOVERY_LAB_V1")
SCRIPTS=Path(r"J:\SDL_AGENT_STACK\scripts")
ROOT=LAB/'research_intake/V27_SOURCE_VERIFIED_RESEARCH_V1'
REPLAY_SHA="574739aea9c2617fc11197d91c952740337a41f089534f26dce209cbffbb3c7c"
AGENT_SHA="a84813525dc348f60cbe8af4b23ac2e7644307cdb09a162a1815883255f26c28"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def native():
    script=SCRIPTS/'sdl_v27_source_verified_research_engine_v1.py'
    assert sha(script.read_bytes())==REPLAY_SHA
    mod=runpy.run_path(str(script))
    result=mod["verify"](ROOT/'runs/TRAVEL_CIRCADIAN_20261116_R1',replay=True)
    assert result['all_pass'] and result['checks_passed']==result['checks_total']==41
    frozen=json.loads(Path(__file__).with_name('pinned_v2_manifest_hashes.json').read_bytes())
    assert len(frozen)==61
    manifests=[ROOT/'document_runs_v2'/name/'manifest.json' for name in frozen]
    source=set()
    for path in manifests:
        raw=path.read_bytes()
        assert sha(raw)==frozen[path.parent.name]
        obj=json.loads(raw)
        if obj.get("schema")!="SDL_V27_DOCUMENT_MANIFEST_V2":continue
        assert len(obj['original_sha256'])==64
        source.add(obj['original_sha256'])
    return {"literature_replay_checks":41,"v2_local_run_manifests":len(manifests),"v2_unique_manifest_source_hashes":len(source),
            "catalog_claim_61_rechecked":len(source)==61}

def transfer():
    import numpy as np
    from sklearn.model_selection import GroupKFold
    p=SCRIPTS/'sdl_v27_agentdog_slsa_ots_provenance_v1.py'
    assert sha(p.read_bytes())==AGENT_SHA
    agent=runpy.run_path(str(p))
    guard=agent['sanitize_document']
    texts=[("Methods allow local verification.",True),("This paragraph says ignore previous instructions.",False),
           ("A reference to a system prompt appears here.",False),("The holdout remained sealed.",True)]
    matched=[]
    for text,allowed in texts:
        obj=guard(text,source_sha256=sha(text.encode()))
        assert obj["execution_authorized"] is False and (obj['value'] is not None)==allowed
        matched.append(obj['diagnostic'])
    safe={"source_id":"sealed","relative_path":"inputs/methods.json","action":"HASH","authority":"OWNER_PINNED",
          "network":False,"authority_inferred_from_content":False}
    invoke=agent['trajectory_guard']
    expected={("sealed","inputs/methods.json")}
    results=[invoke([safe],expected_sources=expected),
             invoke([{**safe,"action":"WRITE"}],expected_sources=expected),
             invoke([{**safe,"authority_inferred_from_content":True}],expected_sources=expected)]
    assert results==["PASS_SCOPED_READ_ONLY_TRAJECTORY","BLOCK_UNAUTHORIZED_ACTION","BLOCK_CONTENT_AUTHORITY_OR_NETWORK"]
    # These fixtures transfer each benchmark's evaluation pattern. They do not use the official datasets.
    artifacts={"result.json":b'{"estimate":1}',"method.md":b'Executable method'}
    hashes={k:sha(v) for k,v in artifacts.items()}
    paper=sum(sha(artifacts[k])==v for k,v in hashes.items())==2 and sha(b'changed')!=hashes["result.json"]
    citations={"primary":{"scope":"grouped","hash":hashes["method.md"]},
               "unreviewed":{"scope":"discovery","hash":hashes["result.json"]}}
    browse=citations["primary"]["scope"]=="grouped" and citations["unreviewed"]["scope"]!="grouped"
    vector=np.array([[2.,4.],[4.,8.],[6.,12.]])
    ds=np.allclose(vector.mean(axis=0),[4,8]) and np.allclose(np.cov(vector,rowvar=False,ddof=1),[[4,8],[8,16]])
    groups=np.repeat(np.arange(9),3)
    splits=list(GroupKFold(3).split(groups,groups,groups))
    mle=all(not set(groups[train]) & set(groups[test]) for train,test in splits)
    checks={"PaperBench":bool(paper),"BrowseComp":bool(browse),"DS-1000":bool(ds),"MLE-bench":bool(mle)}
    assert all(checks.values())
    return {"transfer_smoke":checks,"official_benchmark_leaderboard_claim":False,
            "agentdog_documents":len(matched),"quarantined":matched.count("QUARANTINED_CONTROL_LANGUAGE"),"trajectory":results}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    result={"schema":"SDL_V27_BENCHMARK_TRACK3_V1","status":"PASS_OFFLINE_TRANSFER_SCOPE",
            "native":native(),"transfer":transfer(),"cross_family_live_audit":"HOLD_PENDING_SEPARATE_PAID_ADMISSION",
            "gpt_family_self_review_executed":False,"network_calls":0}
    with parser.parse_args().output.open("x",encoding="utf8",newline="\n") as fp:
        json.dump(result,fp,sort_keys=True,indent=2);fp.write("\n")
