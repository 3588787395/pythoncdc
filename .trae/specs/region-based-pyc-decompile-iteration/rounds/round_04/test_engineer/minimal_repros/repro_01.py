# family: G1  while True yield 首（id_gen 形态）
def id_gen(start=1):
    i = start
    while True:
        yield i
        i += 1
