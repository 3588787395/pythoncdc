import dis

def test_inverted():
    if not (tmp_dividends and symbol not in tmp_dividends):
        early_return()
    else:
        main_body()

dis.dis(test_inverted)
print()
print("=== Both jumps to same target? ===")
# In the original, PJIF→64 and PJIT→64 go to SAME target
# In this version, PJIF→44 (then) and PJIT→76 (else) go to DIFFERENT targets
