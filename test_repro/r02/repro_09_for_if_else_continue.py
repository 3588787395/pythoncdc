# Repro 09: for loop + if-not-continue (also produces POP_JUMP_FORWARD_IF_TRUE)
for item in items:
    if not item.is_valid():
        continue
    process(item)
