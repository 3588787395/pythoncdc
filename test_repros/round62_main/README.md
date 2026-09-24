Fix4 battery (Round 62). Compile each to cpython-311 .pyc next to it, then run the
mirror harness: python -X utf8 <gate>/h62.py run --arm=<arm> --list=<shapes.txt> --out=...
Expected on the landed R62 bytes: r62f_r102name 2/2, w_B 2/2, w_C 2/2, w_D 2/2;
w_A 1/2 and w_E 1/2 are the still-open name-collision variant (Round 63 handover).
