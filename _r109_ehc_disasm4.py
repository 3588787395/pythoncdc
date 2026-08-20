import dis, marshal, sys, types, io

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

def find_code_objects(code_obj, prefix=""):
    results = []
    for i, const in enumerate(code_obj.co_consts):
        if isinstance(const, types.CodeType):
            full_name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            results.append((full_name, const))
            results.extend(find_code_objects(const, full_name))
    return results

all_codes = find_code_objects(code)
target = None
for name, c in all_codes:
    if 'exception_handling' in name:
        target = (name, c)
        break

if target:
    name, c = target
    lines = []
    lines.append(f"=== {name} ===")
    lines.append(f"argcount={c.co_argcount}, varnames={c.co_varnames}")
    lines.append(f"consts count={len(c.co_consts)}")
    for i, const in enumerate(c.co_consts):
        if isinstance(const, types.CodeType):
            lines.append(f"  const[{i}]: <code {const.co_name}>")
        else:
            lines.append(f"  const[{i}]: {repr(const)}")
    lines.append("")
    lines.append("=== Instructions ===")
    for inst in dis.get_instructions(c):
        lines.append(f"  {inst.offset:4d} {inst.opname:30s} {inst.argrepr}")
    lines.append("")
    lines.append("=== Exception Table ===")
    try:
        et = dis.ExceptionTable.from_bytes(c.co_exceptiontable)
        for entry in et:
            lines.append(f"  start={entry.start}, end={entry.end}, target={entry.target}, depth={entry.depth}, lasti={entry.lasti}")
    except Exception as e:
        lines.append(f"  Error: {e}")
    
    with open('_r109_ehc_orig.txt', 'w', encoding='utf-8') as outf:
        outf.write('\n'.join(lines))
    print(f"Done - wrote {len(lines)} lines")
else:
    print("Not found! Available code objects:")
    for name, c in all_codes:
        print(f"  {name}")
