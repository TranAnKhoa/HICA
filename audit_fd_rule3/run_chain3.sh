#!/bin/bash
cd "$(dirname "$0")"
until [ -f ../audit_logs3/chain2_done.txt ]; do sleep 5; done
python3 scale_c8.py > ../audit_logs3/scale_c8.log 2>&1
echo done > ../audit_logs3/chain3_done.txt
