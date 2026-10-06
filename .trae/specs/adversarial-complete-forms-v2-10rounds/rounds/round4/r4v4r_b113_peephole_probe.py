srcs = {
 "orig":  "def f(xs):\n    return [(a, b) for x in xs for a in [x] for b in [x]]\n",
 "out":   "def f(xs):\n    return [(a, b) for x in xs]\n",
 "tuple": "def f(xs):\n    return [(a, b) for x in xs for a in (x,) for b in (x,)]\n",
 "xx":    "def f(xs):\n    return [(x, x) for x in xs]\n",
}
import dis, io
blobs = {}
for k, s in srcs.items():
    c = compile(s, "<t>", "exec")
    lc = [x for x in c.co_consts if hasattr(x, "co_name") and x.co_name == "f"][0]
    lc2 = [x for x in lc.co_consts if hasattr(x, "co_name") and x.co_name == "<listcomp>"][0]
    b = io.StringIO(); dis.dis(lc2, file=b); blobs[k] = b.getvalue()
for k, v in blobs.items():
    print("=====", k); print(v)
print("orig==tuple:", blobs["orig"] == blobs["tuple"])
print("orig==out:", blobs["orig"] == blobs["out"])
print("orig==xx:", blobs["orig"] == blobs["xx"])
