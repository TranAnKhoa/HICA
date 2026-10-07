#!/bin/bash
# After the main timing chain: kill-depth statistics, the exploratory policy, the travel-time-table effect.
cd "$(dirname "$0")"
until [ -f ../audit_logs3/chain_done.txt ]; do sleep 5; done
python3 kill_depth.py           > ../audit_logs3/kill_depth.log 2>&1
python3 explore_open_policy.py  > ../audit_logs3/explore_open_policy.log 2>&1
python3 ttable_effect.py        > ../audit_logs3/ttable_effect.log 2>&1
echo done > ../audit_logs3/chain2_done.txt
