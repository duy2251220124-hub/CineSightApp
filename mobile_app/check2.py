import re
paths = [
    r'lib\features\scanner\presentation\scanner_screen.dart',
    r'lib\mock\mock_data.dart',
    r'lib\screens\cs_handover_screen.dart',
    r'lib\screens\cs_settings_screen.dart'
]
for path in paths:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    print(f'--- {path} ---')
    matches = re.findall(r"'[^']*'|\"[^\"]*\"", text)
    for m in matches:
        if re.search(r'[\xc2\xc3]', m):
            print(ascii(m))
