#!/bin/bash
export PYTHONIOENCODING=utf-8
PY="C:/Users/An Khoa/AppData/Local/Programs/Python/Python37/python.exe"
cd "K:/Data Science/Q1 Research/audit_fd_rule2"
"$PY" phase1_after_tier.py > ../audit_logs2/phase1_after_tier.log 2>&1
"$PY" timing.py label 10 > ../audit_logs2/timing_label.log 2>&1
"$PY" timing.py grid 5 > ../audit_logs2/timing_grid.log 2>&1
"$PY" anchor.py > ../audit_logs2/anchor.log 2>&1
"$PY" profile_tables.py C1 C4 C6 > ../audit_logs2/profile.log 2>&1
echo CHAIN_DONE > ../audit_logs2/chain_done.txt
