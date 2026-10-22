import os
import re

# 1. Fix api_client.dart unterminated string literal
f_api = 'lib/core/network/api_client.dart'
with open(f_api, 'r', encoding='utf-8') as f:
    api_content = f.read()
api_content = re.sub(r'debugPrint\(\'\[NETWORK\] L[^\']*?login: [^\']*?\'\);', "debugPrint('[NETWORK] Login error');", api_content, flags=re.DOTALL)
with open(f_api, 'w', encoding='utf-8') as f:
    f.write(api_content)

# 2. Fix cs_offline_screen.dart
f_off = 'lib/core/network/presentation/cs_offline_screen.dart'
with open(f_off, 'r', encoding='utf-8') as f:
    off_content = f.read()
off_content = off_content.replace("import '../mock/mock_data.dart';", "")
off_content = off_content.replace("CSMockData.employeeName", "'Nhân viên'")
with open(f_off, 'w', encoding='utf-8') as f:
    f.write(off_content)

# 3. Fix cs_login_screen.dart
f_log = 'lib/features/auth/presentation/cs_login_screen.dart'
with open(f_log, 'r', encoding='utf-8') as f:
    log_content = f.read()
log_content = log_content.replace("import '../mock/mock_data.dart';", "")
log_content = log_content.replace("import '../core/network/api_client.dart';", "import 'package:mobile_app/core/network/api_client.dart';")
with open(f_log, 'w', encoding='utf-8') as f:
    f.write(log_content)

# 4. Fix cs_notification_screen.dart
f_notif = 'lib/features/notifications/presentation/cs_notification_screen.dart'
with open(f_notif, 'r', encoding='utf-8') as f:
    notif_content = f.read()
notif_content = notif_content.replace("final List<dynamic> notifications = [];", "List<dynamic> get notifications => [];")
with open(f_notif, 'w', encoding='utf-8') as f:
    f.write(notif_content)

# 5. Fix cs_settings_screen.dart:99 (Remove const)
f_set = 'lib/features/settings/presentation/cs_settings_screen.dart'
with open(f_set, 'r', encoding='utf-8') as f:
    set_content = f.read()
set_content = re.sub(r'const\s+(CSSettingsTile\(\s*icon: Icons.sync)', r'\1', set_content)
with open(f_set, 'w', encoding='utf-8') as f:
    f.write(set_content)

# 6. Fix main.dart AppTheme
f_main = 'lib/main.dart'
with open(f_main, 'r', encoding='utf-8') as f:
    main_content = f.read()
if "import 'package:mobile_app/core/theme/app_theme.dart';" not in main_content:
    main_content = main_content.replace("import 'package:mobile_app/theme/app_theme.dart';", "import 'package:mobile_app/theme/app_theme.dart';\nimport 'package:mobile_app/core/theme/app_theme.dart';")
with open(f_main, 'w', encoding='utf-8') as f:
    f.write(main_content)

print("Fix 5 completed")
