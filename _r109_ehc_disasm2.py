import dis, marshal, sys, io

buf = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buf

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex':
        print(f"=== {c.co_name} ===")
        print(f"argcount={c.co_argcount}, varnames={c.co_varnames}")
        print(f"consts count={len(c.co_consts)}")
        for i, const in enumerate(c.co_consts):
            if hasattr(const, 'co_name'):
                print(f"  const[{i}]: <code {const.co_name}>")
            else:
                print(f"  const[{i}]: {repr(const)}")
        print()
        dis.dis(c)
        print()
        print("=== Exception Table ===")
        for entry in dis.ExceptionTable.from_bytes(c.co_exceptiontable):
            print(f"  start={entry.start}, end={entry.end}, target={entry.target}, depth={entry.depth}, lasti={entry.lasti}")
        break

sys.stdout = old_stdout
with open('_r109_ehc_orig.txt', 'w', encoding='utf-8') as outf:
    outf.write(buf.getvalue())
print("Done - wrote to _r109_ehc_orig.txt")
