# Debug version - check file content
with open('_r39_batch_out.txt', 'rb') as f:
    content = f.read()
print(f"File size: {len(content)} bytes")
print(f"First 200 bytes: {content[:200]}")
print()

# Try decoding
text = content.decode('utf-8', errors='replace')
lines = text.split('\n')
print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines[:15]):
    print(f"  Line {i}: {repr(line[:100])}")

# Count lines with pyc
pyc_lines = [l for l in lines if '.pyc' in l]
print(f"\nLines with .pyc: {len(pyc_lines)}")
for l in pyc_lines[:5]:
    print(f"  {repr(l[:100])}")

# Count lines with matched
matched_lines = [l for l in lines if 'matched' in l]
print(f"\nLines with 'matched': {len(matched_lines)}")
for l in matched_lines[:5]:
    print(f"  {repr(l[:100])}")
