#!/bin/bash
# Wait for the gates, then run the timing protocol alone on the machine.
cd "$(dirname "$0")"
until grep -q -E "SUMMARY|Traceback|Error" ../audit_logs3/gate_c8.log; do sleep 5; done
python3 timing_c8.py orig label 10   > ../audit_logs3/timing_orig_label.log 2>&1
python3 timing_c8.py matrix label 10 > ../audit_logs3/timing_matrix_label.log 2>&1
python3 timing_c8.py orig grid 5     > ../audit_logs3/timing_orig_grid.log 2>&1
python3 timing_c8.py matrix grid 5   > ../audit_logs3/timing_matrix_grid.log 2>&1
echo done > ../audit_logs3/chain_done.txt
