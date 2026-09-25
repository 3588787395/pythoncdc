import difflib, hashlib, sys, os

CENTER = r"D:/Temp/opencode/r64gate"
FILES = ["region_ast_generator.py", "region_analyzer.py"]

def read_lines(p):
    raw = open(p, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    nl_crlf = raw.count(b"\r\n")
    nl_lf = raw.count(b"\n") - nl_crlf
    text = raw.decode("utf-8-sig")
    lines = text.splitlines(keepends=True)
    return raw, bom, nl_crlf, nl_lf, lines

ok_all = True
for f in FILES:
    a = os.path.join(CENTER, "pre_doc", "core", "cfg", f)
    b = os.path.join(CENTER, "mirr_docfinal", "core", "cfg", f)
    ra, bom_a, ca, la, lines_a = read_lines(a)
    rb, bom_b, cb, lb, lines_b = read_lines(b)
    print(f"== {f}")
    print(f"   pre_doc  bytes={len(ra)} bom={bom_a} CRLF={ca} bareLF={la} lines={len(lines_a)} sha={hashlib.sha256(ra).hexdigest()[:12]}")
    print(f"   docfinal bytes={len(rb)} bom={bom_b} CRLF={cb} bareLF={lb} lines={len(lines_b)} sha={hashlib.sha256(rb).hexdigest()[:12]}")
    assert bom_a == bom_b, "BOM changed"
    assert la == lb == 0, f"bare LF appeared: {la}/{lb}"
    sm = difflib.SequenceMatcher(None, lines_a, lines_b, autojunk=False)
    ins, dele, repl = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert":
            ins.append((i1, j1, j2))
        elif tag == "delete":
            dele.append((i1, i2, j1))
        elif tag == "replace":
            repl.append((i1, i2, j1, j2))
    all_ins_lines = []
    for i1, j1, j2 in ins:
        all_ins_lines += lines_b[j1:j2]
    print(f"   opcodes: insert_blocks={len(ins)} delete_blocks={len(dele)} replace_blocks={len(repl)} inserted_lines={len(all_ins_lines)}")
    non_comment = [l.rstrip("\r\n") for l in all_ins_lines if not l.lstrip().startswith("#")]
    print(f"   inserted non-comment lines: {len(non_comment)}")
    for l in non_comment[:10]:
        print("     !! " + l)
    good = (not dele) and (not repl) and (not non_comment)
    print(f"   COMMENT-ONLY-ADDITION = {good}")
    ok_all = ok_all and good

print("ALL COMMENT ONLY =", ok_all)
sys.exit(0 if ok_all else 1)
