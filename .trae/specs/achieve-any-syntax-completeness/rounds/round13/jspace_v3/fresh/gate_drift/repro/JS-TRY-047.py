def v_nest_fin_continue(rows):
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                out.append(1)
        finally:
            out.append(2)
        out.append(r)
    return out
if __name__ == '__main__':
    print(v_nest_fin_continue([0, 1, -1]))
