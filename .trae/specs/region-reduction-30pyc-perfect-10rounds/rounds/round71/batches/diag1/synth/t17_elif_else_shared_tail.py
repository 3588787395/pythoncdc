# F-THENOVER/F-ORELSE (finance.get_fields): statements following an if/elif/else
# chain are absorbed into the else arm, so the then-arm's exit jump re-targets the
# far merge (92 -> 236 vs 94 -> 742) and an extra EXTENDED_ARG appears (177/178).
def get_fields(error_msg):
    fields = []
    if error_msg['error_no'] == -1:
        fields = ['a']
    elif error_msg['error_no'] == -2:
        fields = ['b']
    else:
        fields = ['c']
    if error_msg['error_no'] == 0:
        fields.append('extra')
    return fields
