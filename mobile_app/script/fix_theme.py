import os

def fix_import(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.dart'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                new_content = content.replace(
                    "import 'package:mobile_app/core/theme/app_theme.dart';",
                    "import 'package:mobile_app/theme/app_theme.dart';"
                )
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed {filepath}")

fix_import('lib/features')
