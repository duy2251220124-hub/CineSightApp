import re
with open(r'lib\screens\cs_login_screen.dart', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r"'[^']*'|\"[^\"]*\"", text)
for m in matches:
    if re.search(r'[\xc2\xc3]', m):
        print(ascii(m))
