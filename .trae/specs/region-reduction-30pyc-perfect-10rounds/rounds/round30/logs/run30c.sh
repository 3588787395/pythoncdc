#!/bin/bash
# Round 30 gates for R30-C1: G2' (38 synthetic repros) -> G3 (96 anchors) -> G4 (full-402 A/B).
# head records for G4 are REUSED from ../ab402_head_*.jsonl: that arm was built from the same
# landed worktree bytes (06f0ba50) and its mirror was verified byte-identical before the run.
set -u
cd /d/Temp/r30gate/c1 || exit 9
PY="python -X utf8"
L(){ echo "@@@ $*"; }

L "G2' 38-synthetic battery (head vs c1)"
$PY r30c.py run --arm=head --list=../reprobat38.txt --out=rb_head.jsonl >rb_head.log 2>&1; echo "rc=$?"
$PY r30c.py run --arm=c1   --list=../reprobat38.txt --out=rb_c1.jsonl   >rb_c1.log   2>&1; echo "rc=$?"
$PY ../cmp30.py rb_head.jsonl rb_c1.jsonl >g2prime_38.txt 2>&1; echo "rc=$?"; tail -3 g2prime_38.txt

L "G3 96-anchor battery"
$PY r30c.py run --arm=head --list=../anchors96.txt --out=base_head96.jsonl >base_head96.log 2>&1; echo "rc=$?"
$PY r30c.py run --arm=c1   --list=../anchors96.txt --out=base_c1_96.jsonl >base_c1_96.log 2>&1; echo "rc=$?"
$PY ../cmp30.py base_head96.jsonl base_c1_96.jsonl >g3_96.txt 2>&1; echo "rc=$?"; tail -3 g3_96.txt

L "G4 full-402 A/B (head reused, c1 4 shards)"
cp ../ab402_head_0.jsonl ../ab402_head_1.jsonl ../ab402_head_2.jsonl ../ab402_head_3.jsonl .
for i in 0 1 2 3; do
  $PY r30c.py run --arm=c1 --list=../all402.txt --out=ab402_c1_$i.jsonl --nshard=4 --shard=$i >ab402_c1_$i.log 2>&1 &
done; wait
cat ab402_head_0.jsonl ab402_head_1.jsonl ab402_head_2.jsonl ab402_head_3.jsonl >ab402_head.jsonl
cat ab402_c1_0.jsonl ab402_c1_1.jsonl ab402_c1_2.jsonl ab402_c1_3.jsonl >ab402_c1.jsonl
$PY -c "
import io
for f in ('ab402_head.jsonl','ab402_c1.jsonl'):
    print(f, sum(1 for l in io.open(f,encoding='utf-8') if l.strip()))
"
$PY r30c.py ab --a=ab402_head.jsonl --b=ab402_c1.jsonl >g4_ab402_sha.txt 2>&1; echo "rc=$?"; tail -8 g4_ab402_sha.txt
$PY ../cmp30.py ab402_head.jsonl ab402_c1.jsonl >g4_ab402.txt 2>&1; echo "rc=$?"; tail -8 g4_ab402.txt
L "C1 GATES DONE"
