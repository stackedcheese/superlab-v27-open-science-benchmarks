"""Track 4. Deterministic decision-time telemetry anomaly evaluation."""
import argparse
import json
from pathlib import Path
import random
from statistics import median
import sys

def offline(event,args):
 if event.startswith('socket.'): raise RuntimeError('NETWORK_BLOCKED')
sys.addaudithook(offline)

FAULTS=("CLOCK_DRIFT","SOURCE_FREEZE","MISSED_WINDOW","SURVIVORSHIP")
SEED=19527

def fixture():
    rng=random.Random(SEED)
    truth={}
    jobs=[]
    locations=rng.sample(range(554),159)
    labels={job:FAULTS[i%4] for i,job in enumerate(locations)}
    for i in range(554):
        cut=1_000_000+i*120
        published=cut-25
        observed=cut-19
        eligible=cut-13
        freshness=cut-rng.randint(7,29)
        arrived=cut-8
        checkpoint=cut+12
        row={"job":i,"published":published,"observed":observed,"eligible":eligible,"last_change":freshness,
             "cutoff":cut,"arrived":arrived,"first_check":checkpoint,"source_age":cut-freshness}
        fault=labels.get(i)
        if fault=='CLOCK_DRIFT':
            row["observed"]=cut+rng.randint(1,16)
            row["first_check"]=row["observed"]+3
            truth[i]=(fault,row["observed"])
        elif fault=='SOURCE_FREEZE':
            row["last_change"]=cut-rng.randint(81,150)
            row["source_age"]=cut-row["last_change"]
            truth[i]=(fault,cut)
        elif fault=='MISSED_WINDOW':
            row["arrived"]=cut+rng.randint(25,40)
            truth[i]=(fault,cut)
        elif fault=='SURVIVORSHIP':
            truth[i]=(fault,cut)
            continue
        # Benign delays exercise the detector's tolerance without changing eligibility.
        if fault is None and i%16==0: row["arrived"]=cut-1
        jobs.append(row)
    expected={i:1_000_000+i*120 for i in range(554)}
    return expected,jobs,truth

def detect(expected,observed):
    tracked={}
    for row in observed:
        if row["job"] in tracked or expected.get(row["job"])!=row["cutoff"]:
            raise ValueError("UNIVERSE_OR_ID_MISMATCH")
        tracked[row["job"]]=row
    alerts={}
    for job,cut in expected.items():
        row=tracked.get(job)
        if row is None:
            alerts[job]=("SURVIVORSHIP",cut+30)
        elif row["first_check"]>=cut:
            if not row["published"]<=row["observed"]<=row["eligible"]<cut:
                alerts[job]=("CLOCK_DRIFT",row["first_check"])
            elif row["last_change"]<cut-60:
                alerts[job]=("SOURCE_FREEZE",row["first_check"])
            elif row["arrived"]>=cut:
                alerts[job]=("MISSED_WINDOW",row["first_check"])
    return alerts

def run():
    expected,observe,labels=fixture()
    assert len(expected)==554 and len(labels)==159
    seen=detect(expected,observe)
    hits=[k for k,(fault,_) in seen.items() if k in labels and labels[k][0]==fault]
    missing=len(labels)-len(hits)
    false=len(seen)-len(hits)
    lat=[seen[k][1]-labels[k][1] for k in hits]
    assert min(lat)>=0 and len(seen)>0
    # Negative controls make missing universe records and future-eligible rows visible.
    one=next(row for row in observe if row["job"] not in labels)
    assert detect({one["job"]:one["cutoff"]},[])=={one["job"]:("SURVIVORSHIP",one["cutoff"]+30)}
    changed={**one,"eligible":one["cutoff"]}
    assert detect({one["job"]:one["cutoff"]},[changed])[one["job"]][0]=="CLOCK_DRIFT"
    try: detect({one["job"]:one["cutoff"]},[one,one])
    except ValueError: duplicate_rejected=True
    else: raise AssertionError("NO_DUPLICATE_REJECTION")
    return {"schema":"SDL_V27_BENCHMARK_TRACK4_V1","status":"PASS_SYNTHETIC_EXECUTION","seed":SEED,
        "jobs":len(expected),"incidents":len(labels),"observed_rows":len(observe),"alerts":len(seen),
        "true_positive":len(hits),"false_positive":false,"false_negative":missing,
        "precision":len(hits)/len(seen),"recall":len(hits)/len(labels),
        "false_positive_rate":len([k for k in seen if k not in labels])/(len(expected)-len(labels)),
        "median_detection_latency_s":median(lat),"max_detection_latency_s":max(lat),
        "by_fault":{fault:{"truth":sum(1 for t,_ in labels.values() if t==fault),
           "detected":sum(1 for k in hits if labels[k][0]==fault)} for fault in FAULTS},
        "duplicate_identity_rejected":duplicate_rejected,"live_monitor_evaluated":False,"network_calls":0}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    payload=run()
    with parser.parse_args().output.open("x",encoding="utf8",newline="\n") as fp:
        json.dump(payload,fp,sort_keys=True,indent=2,allow_nan=False);fp.write("\n")
