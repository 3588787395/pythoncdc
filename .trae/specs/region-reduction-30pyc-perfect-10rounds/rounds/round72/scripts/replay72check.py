import io, json, subprocess, sys, os
sys.stdout.reconfigure(encoding="utf-8")
REPO = r"F:\Downloads\pythoncdc-main"
ROOT = r"D:/Temp/opencode/r72gate/center"
spec = json.load(io.open(r"D:/Temp/opencode/r72gate/merged72_comprehension_generator.py.json", encoding="utf-8"))
rel = spec["file"]
blob = subprocess.run(["git", "-C", REPO, "show", "HEAD:" + rel], capture_output=True).stdout
head = blob.decode("utf-8-sig").replace("\r\n", "\n")
patched = head
for k, e in enumerate(spec["edits"]):
    n = patched.count(e["anchor"])
    print("edit %d anchor occurrences=%d (on HEAD bytes)" % (k, n))
    assert n == 1, k
    patched = patched.replace(e["anchor"], e["repl"])
mir = io.open(os.path.join(ROOT, "mirr_m", rel.replace("/", os.sep)), "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
same = patched == mir
print("replay(HEAD + spec) == mirr_m bytes (LF-normalised): %s" % same)
w = io.open(os.path.join(REPO, rel.replace("/", os.sep)), "rb").read().decode("utf-8-sig").replace("\r\n", "\n")
print("mirr_m == worktree bytes (LF-normalised): %s" % (mir == w))
print("net inserted lines: %d" % sum(e["repl"].count("\n") - e["anchor"].count("\n") for e in spec["edits"]))
raise SystemExit(0 if (same and mir == w) else 1)
