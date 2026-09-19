"""R3-G: 循环内 break 汇聚块布局重排 —— or 短路真路径与 else:break 路径经过
额外中转块（orig 直达循环底, decomp 多一条 JUMP_FORWARD 中转）。
对照 quote.pyc one_prod_to_dataframe 内层循环:
    elif len(v) == 14: temp_time = ...; if int(...) >= 16 or int(...) < 9: break
    else: break
    index.append(temp_time)"""


def one_prod_to_dataframe(self, prod, time_index):
    index = []
    for item in prod:
        for i, v in enumerate(item):
            if i == time_index:
                v = str(v)
                if len(v) == 14:
                    temp_time = v
                    if int(temp_time[11:13]) >= 16 or int(temp_time[11:13]) < 9:
                        break
                else:
                    break
                index.append(temp_time)
    return index
