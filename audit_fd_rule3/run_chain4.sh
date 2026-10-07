#!/bin/bash
# Dead-end filter: gates, then timing (runs alone after the C8 chains).
cd "$(dirname "$0")"
until [ -f ../audit_logs3/chain3_done.txt ]; do sleep 5; done
python3 gate_h.py                     > ../audit_logs3/gate_h.log 2>&1
python3 timing_h.py orig label 10     > ../audit_logs3/timing_h_orig_label.log 2>&1
python3 timing_h.py matrix label 10   > ../audit_logs3/timing_h_matrix_label.log 2>&1
python3 timing_h.py orig grid 5       > ../audit_logs3/timing_h_orig_grid.log 2>&1
python3 timing_h.py matrix grid 5     > ../audit_logs3/timing_h_matrix_grid.log 2>&1
python3 timing_h.py matrix scale 3    > ../audit_logs3/timing_h_matrix_scale.log 2>&1
echo done > ../audit_logs3/chain4_done.txt
