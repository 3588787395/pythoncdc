#!/bin/bash
# usage: runsh.sh <arm> <list> <outprefix> <nshard>
ARM=$1; LIST=$2; OUT=$3; N=$4
i=0
while [ $i -lt $N ]; do
  python -X utf8 D:/Temp/r43gate/r43g.py run --arm=$ARM --list=$LIST --out=${OUT}_s$i.jsonl --nshard=$N --shard=$i > ${OUT}_s$i.log 2>&1 &
  i=$((i+1))
done
wait
cat ${OUT}_s*.jsonl > ${OUT}.jsonl
wc -l ${OUT}.jsonl
