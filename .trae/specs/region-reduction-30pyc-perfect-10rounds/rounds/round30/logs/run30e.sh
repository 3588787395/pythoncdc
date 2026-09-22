#!/bin/bash
# Round 30: re-run the whole gate set on the LANDING arm (mirr_c1c = measured patch + comment
# lines) and sha-compare its products against the measured arm c1.  Strictly serial.
set -u
cd /d/Temp/r30gate/c1 || exit 9
PY="python -X utf8"
L(){ echo "@@@ $*"; }

L "G2'e 38-synthetic battery on landing arm"
$PY r30c.py run --arm=c1c --list=../reprobat38.txt --out=rb_c1c.jsonl >rb_c1c.log 2>&1; echo "rc=$?"
$PY ../cmp30.py rb_c1.jsonl rb_c1c.jsonl >e_g2prime_38.txt 2>&1; echo "rc=$?"; tail -2 e_g2prime_38.txt

L "G3e 96-anchor battery on landing arm"
$PY r30c.py run --arm=c1c --list=../anchors96.txt --out=base_c1c_96.jsonl >base_c1c_96.log 2>&1; echo "rc=$?"
$PY ../cmp30.py base_c1_96.jsonl base_c1c_96.jsonl >e_g3_96.txt 2>&1; echo "rc=$?"; tail -2 e_g3_96.txt

L "G4e full-402 on landing arm vs measured arm c1"
for i in 0 1 2 3; do
  $PY r30c.py run --arm=c1c --list=../all402.txt --out=ab402_c1c_$i.jsonl --nshard=4 --shard=$i >ab402_c1c_$i.log 2>&1 &
done; wait
cat ab402_c1c_0.jsonl ab402_c1c_1.jsonl ab402_c1c_2.jsonl ab402_c1c_3.jsonl >ab402_c1c.jsonl
$PY -c "import io;print('ab402_c1c.jsonl', sum(1 for l in io.open('ab402_c1c.jsonl',encoding='utf-8') if l.strip()))"
$PY r30c.py ab --a=ab402_c1.jsonl --b=ab402_c1c.jsonl >e_g4_ab402_sha.txt 2>&1; echo "rc=$?"; tail -6 e_g4_ab402_sha.txt
L "LANDING-FORM GATES DONE"
