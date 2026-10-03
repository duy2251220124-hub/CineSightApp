import re
path = r'c:\CineSightApp\mobile_app\lib\features\scanner\presentation\scanner_screen.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r'\s*void _showError\(String message\) \{[\s\S]*?\}\s*\}\s*,?\s*\}\s*,\s*\);\s*\}\s*\}', r'', content)
# It might be safer to just do a precise replace for _showError if I know its exact span.
# Let's print _showError to see its bounds
