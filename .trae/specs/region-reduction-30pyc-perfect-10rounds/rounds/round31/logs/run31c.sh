#!/bin/bash
# Round 31 gates for R31-C (arm c): G2' (38 synthetic repros) -> G3 (98 load-bearing anchors)
# -> G4 (full-402 sha A/B, shipping authority).  Both arms are built fresh in this ROOT from
# the current worktree bytes, so nothing is reused from the diagnosing agent's directory.
set -u
cd /d/Temp/r31gate/c1 || exit 9
PY="python -X utf8"
L(){ echo "@@@ $*"; }

L "G2' 38-synthetic battery (head vs c)"
$PY r31c.py run --arm=head --list=../reprobat38.txt --out=rb_head.jsonl >rb_head.log 2>&1; L "rc=$?"
$PY r31c.py run --arm=c     --list=../reprobat38.txt --out=rb_c.jsonl   >rb_c.log   2>&1; L "rc=$?"
$PY ../cmp30.py rb_head.jsonl rb_c.jsonl >g2prime_38.txt 2>&1; L "rc=$?"; tail -3 g2prime_38.txt

L "G3 98-anchor battery"
$PY r31c.py run --arm=head --list=../anchors98.txt --out=base_head98.jsonl >base_head98.log 2>&1; L "rc=$?"
$PY r31c.py run --arm=c     --list=../anchors98.txt --out=base_c_98.jsonl  >base_c_98.log   2>&1; L "rc=$?"
$PY ../cmp30.py base_head98.jsonl base_c_98.jsonl >g3_98.txt 2>&1; L "rc=$?"; tail -3 g3_98.txt

L "G4 full-402 A/B (head 4 shards, c 4 shards, sha-first)"
for i in 0 1 2 3; do
  $PY r31c.py run --arm=head --list=../all402.txt --out=ab402_head_$i.jsonl --nshard=4 --shard=$i >ab402_head_$i.log 2>&1 &
done; wait
cat ab402_head_0.jsonl ab402_head_1.jsonl ab402_head_2.jsonl ab402_head_3.jsonl >ab402_head.jsonl
for i in 0 1 2 3; do
  $PY r31c.py run --arm=c --list=../all402.txt --out=ab402_c_$i.jsonl --nshard=4 --shard=$i >ab402_c_$i.log 2>&1 &
done; wait
cat ab402_c_0.jsonl ab402_c_1.jsonl ab402_c_2.jsonl ab402_c_3.jsonl >ab402_c.jsonl
$PY -c "
import io
for f in ('ab402_head.jsonl','ab402_c.jsonl'):
    print(f, sum(1 for l in io.open(f,encoding='utf-8') if l.strip()))
"
$PY r31c.py ab --a=ab402_head.jsonl --b=ab402_c.jsonl >g4_ab402_sha.txt 2>&1; L "rc=$?"; tail -10 g4_ab402_sha.txt
$PY ../cmp30.py ab402_head.jsonl ab402_c.jsonl >g4_ab402.txt 2>&1; L "rc=$?"; tail -6 g4_ab402.txt
L "R31-C GATES DONE"
