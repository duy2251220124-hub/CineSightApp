import os

filepath = 'lib/features/scanner/presentation/cs_scan_history_screen.dart'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "import '../../../theme/app_theme.dart';",
    "import 'package:mobile_app/theme/app_theme.dart';"
)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
