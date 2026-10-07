#!/bin/bash
export PYTHONIOENCODING=utf-8
PY="C:/Users/An Khoa/AppData/Local/Programs/Python/Python37/python.exe"
cd "K:/Data Science/Q1 Research/audit_fd_rule2"
"$PY" timing.py label3 10 > ../audit_logs2/timing_label3_rerun.log 2>&1
"$PY" anchor.py > ../audit_logs2/anchor_rerun.log 2>&1
"$PY" phase1_after_tier.py > ../audit_logs2/phase1_after_tier.log 2>&1
echo DONE > ../audit_logs2/chain2_done.txt
