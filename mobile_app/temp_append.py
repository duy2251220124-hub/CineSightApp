import os
import re

lib_dir = "lib"

# Collect all dart files
all_dart_files = []
for root, dirs, files in os.walk(lib_dir):
    for f in files:
        if f.endswith('.dart'):
            all_dart_files.append(os.path.relpath(os.path.join(root, f), ".").replace("\\", "/"))

out = []
for f in all_dart_files:
    out.append(f"| `{f}` | TBD | TBD | TBD | TBD |")

with open('append_md.txt', 'w', encoding='utf-8') as file:
    file.write('\n'.join(out))
