"""Round 63 batch 5 witness W1: while-True body whose outer If has BOTH arms
reaching the loop exit differently (then = fall-through suite ending in the
back edge, else = bare break).  Mirrors flyAccount.init_connection.

Run from D:/Temp/opencode/r63gate/diag5:
  python -X utf8 h62.py run --arm=landed --list=w1.txt --out=dump/w1_landed.jsonl --budget=280
  python -X utf8 h62.py build --spec=specs/cand_x.json --dst=c1
  python -X utf8 h62.py run --arm=c1 --list=w1.txt --out=dump/w1_c1.jsonl --budget=280
  python -X utf8 cmp_arms.py dump/w1_landed.jsonl dump/w1_c1.jsonl landed c1
"""
import time

SUCCESS = 0


def init_connection(self):
    i = 0
    while True:
        error_no, error_info = self.connector_manager.CreateConnector(1, self.t2sdk_ini_path)
        if error_no != SUCCESS:
            if i < 3:
                time.sleep(1)
            else:
                error_info = 'init_connection创建连接超时,请稍后再试'
                break
            i += 1
        else:
            break
    return {'error_no': error_no, 'error_info': error_info}
