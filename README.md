# SuperLab V27 — Open-Science FAIR4RS Benchmark Suite

**Organization:** Stacked Cheese Intelligence LLC · SuperLab V27 Scientific Discovery Lab (New Orleans, Louisiana, USA · NAICS 541715 / 518210)  
**Principal Investigator:** Levord Rose Jr. ([ORCID: 0009-0007-7479-7082](https://orcid.org/0009-0007-7479-7082))  
**Live Interactive Workbench & WebCrypto Verifiers:** [https://stackedcheese.com/research](https://stackedcheese.com/research)  
**Release Manifest:** [https://stackedcheese.com/research/manifest.json](https://stackedcheese.com/research/manifest.json)

## Four Reproducible FAIR4RS Benchmark Packages (`4/4 CLAUDE_RING0_PASS`)

1. **`track1_biomechanics` — Multirate 3D Biomechanical Kinematics & Force-Plate Symbolic Recovery:**
   - Deterministic `360 Hz` optical kinematics to `1,080 Hz` dual force-plate ground-reaction-force alignment (`240,995` complete frames across `403` trials, `100` subject groups, `0` fold overlap) and PySINDy coupled-oscillator differential equation recovery (`RMSE = 5.22e-16`).
2. **`track2_calibration` — Non-Crossing 19-Quantile PAVA Conformal Calibration & Sequential E-Processes:**
   - Weighted Pool-Adjacent-Violators Algorithm (`PAVA-19`) isotonic projection, Split Conformalized Quantile Regression (`Split-CQR`), Power/Shin simplex probability normalization (`0` quantile crossings across `36,040` historical out-of-fold rows and `900` synthetic distribution-shift test rows), and Ville-bounded anytime-valid sequential e-processes with `e-BH` false discovery rate control.
3. **`track3_provenance` — Fail-Closed Scientific Provenance, Triple-DOI Literature Verification & AgentDoG Safety:**
   - Deterministic replay across `41` triple-DOI scholarly metadata checks (Europe PMC, Crossref, OpenAlex), `61` span-anchored Document Adapter V2 manifests, `AgentDoG` untrusted-instruction quarantine, and `4/4` offline transfer fixtures (`PaperBench`, `BrowseComp`, `DS-1000`, `MLE-bench`).
4. **`track4_telemetry` — Bitemporal Three-Clock Telemetry Anomaly Detection (`Blindspot`):**
   - Enforces the strict point-in-time inequality (`published_at_utc <= observed_at_utc <= eligible_at_utc < cutoff_utc`) across `554` longitudinal jobs and `159` injected clock-drift, stale-freeze, missed-window, and survivorship faults (`precision = 1.0`, `recall = 1.0`, `false_positive_rate = 0.0`, `12s` median detection latency).

Each track directory contains a standalone `reproduce.py`, `result.json`, `CITATION.cff`, `codemeta.json`, `requirements.lock.txt`, and `LICENSE` (MIT).
