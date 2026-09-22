#!/bin/bash
# Round 32 gates for R32-C (arm c: POP_TOP is a statement terminator in the comprehension
# prefix scanner).  Strictly serial: G2' (38 synthetic repros) -> G3 (100 load-bearing
# anchors) -> G4 (full-402 sha-first A/B, shipping authority) -> d1 A/B.
set -u
cd /d/Temp/r32gate/c1 || exit 9
PY="python -X utf8"
L(){ echo "@@@ $*"; }

L "G2' 38-synthetic battery (head vs c)"
$PY r32c.py run --arm=head --list=../reprobat38.txt --out=rb_head.jsonl >rb_head.log 2>&1; L "rc=$?"
$PY r32c.py run --arm=c     --list=../reprobat38.txt --out=rb_c.jsonl   >rb_c.log   2>&1; L "rc=$?"
$PY ../cmp30.py rb_head.jsonl rb_c.jsonl >g2prime_38.txt 2>&1; L "rc=$?"; tail -3 g2prime_38.txt

L "G3 100-anchor battery"
$PY r32c.py run --arm=head --list=../anchors100.txt --out=base_head100.jsonl >base_head100.log 2>&1; L "rc=$?"
$PY r32c.py run --arm=c     --list=../anchors100.txt --out=base_c_100.jsonl >base_c_100.log 2>&1; L "rc=$?"
$PY ../cmp30.py base_head100.jsonl base_c_100.jsonl >g3_100.txt 2>&1; L "rc=$?"; tail -3 g3_100.txt

L "G4 full-402 A/B (head 4 shards, c 4 shards, sha-first)"
for i in 0 1 2 3; do
  $PY r32c.py run --arm=head --list=all402.txt --out=ab402_head_$i.jsonl --nshard=4 --shard=$i >ab402_head_$i.log 2>&1 &
done; wait
cat ab402_head_0.jsonl ab402_head_1.jsonl ab402_head_2.jsonl ab402_head_3.jsonl >ab402_head.jsonl
for i in 0 1 2 3; do
  $PY r32c.py run --arm=c --list=all402.txt --out=ab402_c_$i.jsonl --nshard=4 --shard=$i >ab402_c_$i.log 2>&1 &
done; wait
cat ab402_c_0.jsonl ab402_c_1.jsonl ab402_c_2.jsonl ab402_c_3.jsonl >ab402_c.jsonl
$PY -c "
import io
for f in ('ab402_head.jsonl','ab402_c.jsonl'):
    print(f, sum(1 for l in io.open(f,encoding='utf-8') if l.strip()))
"
$PY r32c.py ab --a=ab402_head.jsonl --b=ab402_c.jsonl >g4_ab402_sha.txt 2>&1; L "rc=$?"; tail -14 g4_ab402_sha.txt
$PY ../cmp30.py ab402_head.jsonl ab402_c.jsonl >g4_ab402.txt 2>&1; L "rc=$?"; tail -6 g4_ab402.txt

L "G4-d1 seven one-function-away files"
$PY r32c.py run --arm=head --list=d1list.txt --out=d1_head.jsonl >d1_head.log 2>&1; L "rc=$?"
$PY r32c.py run --arm=c     --list=d1list.txt --out=d1_c.jsonl   >d1_c.log   2>&1; L "rc=$?"
$PY r32c.py ab --a=d1_head.jsonl --b=d1_c.jsonl >g4d1_d1.txt 2>&1; L "rc=$?"; tail -6 g4d1_d1.txt
L "R32-C GATES DONE"
