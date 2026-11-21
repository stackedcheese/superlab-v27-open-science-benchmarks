"""Track 1. Deterministic subject-disjoint pitching regression and oscillator recovery."""
import argparse
from pathlib import Path
import sys
def offline(event,args):
 if event.startswith('socket.') and event != 'socket.gethostname': raise RuntimeError('OFFLINE_SOCKET_BLOCK')
sys.addaudithook(offline)
import hashlib
import importlib.metadata as metadata
import json
import zipfile
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score

BASE=Path(r"M:\bringitback\WO_V27_NOTE209_WAVE6_SCIENCE_SHIELD_AND_NOLA_MARKET_20261119\note209_mech_archive_alignment.json")
RECEIPT_SHA="8bd9413f1d362aa8c065ba36530a3107ffb04b8d55ce7652f02f02bf642ed124"

def hashfile(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()

def oscillator():
    import pysindy as ps
    ts=np.linspace(0,10,501)
    stiffness,frequency=-4.0,2.0
    trials=[]
    for angle in [0.1,.35,.7,1.0,1.55,2.2,2.6,3.1]:
        phases=frequency*ts+angle
        x=np.column_stack((np.cos(phases),-frequency*np.sin(phases)))
        derivative=np.column_stack((x[:,1],stiffness*x[:,0]))
        trials.append((x,derivative))
    train=trials[:5]; test=trials[5:]
    mod=ps.SINDy(feature_library=ps.PolynomialLibrary(degree=2,include_bias=False),
                 optimizer=ps.STLSQ(threshold=.1,alpha=0.0))
    mod.fit([x for x,_ in train], t=[ts for _ in train],x_dot=[d for _,d in train])
    actual=np.concatenate([d for _,d in test]);pred=np.concatenate([mod.predict(x) for x,_ in test])
    co=np.asarray(mod.coefficients())
    names=mod.get_feature_names()
    assert set(np.flatnonzero(abs(co[0])>1e-9))=={names.index('x1')}
    assert set(np.flatnonzero(abs(co[1])>1e-9))=={names.index('x0')}
    return {"held_out_trajectories":len(test),"equations":mod.equations(precision=5),
      "derivative_rmse":float(np.sqrt(np.mean((pred-actual)**2))),
      "ground_truth_derivative_rmse":0.0,"pysindy":metadata.version("pysindy")}

def read_source(ref,cols,hz):
    p=Path(ref["path"])
    assert hashfile(p)==ref["sha256"],"SOURCE_SHA_MISMATCH"
    if "member" in ref:
        with zipfile.ZipFile(p) as archive,archive.open(ref["member"]) as stream:
            rows=pd.read_csv(stream,usecols=cols)
    else:
        rows=pd.read_csv(p,usecols=cols)
    times=rows.pop("time").to_numpy()*hz
    tick=np.rint(times).astype("int64")
    assert np.max(np.abs(times-tick))<=.061
    rows["tick"]=tick
    a=rows.pop("BR_time").to_numpy()*360
    anchor=np.rint(a).astype("int64")
    assert np.max(np.abs(a-anchor))<=.061
    rows["release_anchor"]=anchor
    return rows

def grouped_pitching(references):
    ref={row["role"]:row for row in references["archives"]}
    keys=["session_pitch","time","BR_time"]
    angle=read_source(references["joint_angles"],[*keys,"pelvis_angle_x"],360)
    forces=["rear_force_x","rear_force_y","rear_force_z","lead_force_x","lead_force_y","lead_force_z"]
    force=read_source(ref["force"],[*keys,*forces],1080)
    force=force[force["tick"]%3==0].copy()
    force["tick"]//=3
    energies=["rear_knee_energy_generated","lead_knee_energy_generated","elbow_energy_generated"]
    velos=["elbow_velo_x","elbow_velo_y","elbow_velo_z"]
    slow1=read_source(ref["energy"],[*keys,*energies],360)
    slow2=read_source(ref["velocities"],[*keys,*velos],360)
    joined=angle
    for frame in (slow1,slow2,force):
        joined=joined.merge(frame,on=["session_pitch","tick","release_anchor"],validate='one_to_one')
    assert len(joined)==242608
    rows=joined.dropna(subset=[*forces,*energies,*velos,"pelvis_angle_x"]).copy()
    assert len(rows)==240995 and rows["session_pitch"].nunique()==403
    meta=references["trial_metadata_pins"][0]
    assert hashfile(Path(meta["path"]))==meta["sha256"]
    roster=pd.read_csv(meta["path"],usecols=["session_pitch","user"])
    rows=rows.merge(roster,on="session_pitch",validate='many_to_one')
    assert len(rows)==240995 and not rows["user"].isna().any()
    y=np.linalg.norm(rows[velos].to_numpy(),axis=1)
    x=rows[[*forces,*energies,"pelvis_angle_x"]].to_numpy()
    grouping=rows["user"].to_numpy()
    prepared=list(GroupKFold(n_splits=5).split(x,y,groups=grouping))
    assert all(not set(grouping[tr])&set(grouping[te]) for tr,te in prepared)
    frontier=[]
    for degree in [0,1,2]:
        prediction=np.empty_like(y,dtype=float)
        n_features=1
        for tr,te in prepared:
            if degree==0:
                prediction[te]=float(y[tr].mean())
            else:
                map_=PolynomialFeatures(degree,include_bias=False)
                pipeline=make_pipeline(StandardScaler(),map_,Ridge(alpha=10.0))
                pipeline.fit(x[tr],y[tr])
                prediction[te]=pipeline.predict(x[te])
                n_features=map_.n_output_features_
        rmse=float(np.sqrt(np.mean((prediction-y)**2)))
        frontier.append({"degree":degree,"terms":n_features,"rmse":rmse,"r2":float(r2_score(y,prediction))})
    best_rmse=float('inf')
    efficient=[]
    for point in frontier:
        if point["rmse"]<best_rmse:
            efficient.append(point); best_rmse=point["rmse"]
    return {"frames":len(rows),"trials":int(rows["session_pitch"].nunique()),"groups":int(pd.Series(grouping).nunique()),
      "source_sha256":[references["joint_angles"]["sha256"],*[ref[k]["sha256"] for k in ("force","energy","velocities")]],
      "folds":len(prepared),"group_overlap":0,"diagnostic":"Same-time kinematic reconstruction, no prospective claim.",
      "library":"Fixed polynomial ridge comparison","evaluated_frontier":frontier,"pareto_frontier":efficient,
      "local_egress":"HASH_ONLY","zone_a_raw_export":False}

def addbio():
    root=Path(r"M:\AddBiomechanicsDataset")
    summary=[]
    for label in ('Carter2023','Falisse2017'):
        counts={}
        for split in ('train','test'):
            p=root/split/'No_Arm'/(label+'_Formatted_No_Arm')
            matches=sorted(p.glob('*/*.b3d'))
            assert matches
            counts[split]=len(matches)
        summary.append({"study":label,"local_b3d_counts":counts,"scope":"inventory only"})
    return {"studies":summary,"status":"HOLD_NATIVE_B3D_READER_REPLAY_NOT_EXECUTED"}

def run():
    assert metadata.version("pysindy")=="2.1.0" and metadata.version("pysr")=="2.7.2"
    assert hashfile(BASE)==RECEIPT_SHA
    astro=oscillator()
    real=grouped_pitching(json.loads(BASE.read_bytes()))
    return {"schema":"SDL_V27_BENCHMARK_TRACK1_V1","status":"PARTIAL_SCOPE",
      "pitching":real,"synthetic_ground_truth":astro,"pysr":{"version":"2.7.2","state":"HOLD_JULIA_UNAVAILABLE_OFFLINE"},
      "addbiomechanics":addbio(),"inference_calls":0,"network_calls":0}

if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__); cli.add_argument('--output',type=Path,required=True)
    out=cli.parse_args().output
    payload=run()
    with out.open("x",encoding="utf8",newline="\n") as fp: json.dump(payload,fp,sort_keys=True,indent=2,allow_nan=False); fp.write("\n")
