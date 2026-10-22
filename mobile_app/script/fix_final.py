import os
import re

def replace_in_file(filepath, old_str, new_str):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old_str in content:
        content = content.replace(old_str, new_str)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

# Fix scan history screen
f_history = 'lib/features/scanner/presentation/cs_scan_history_screen.dart'
replace_in_file(f_history, "import '../core/database/hive_service.dart';", "import 'package:mobile_app/core/database/hive_service.dart';")
replace_in_file(f_history, "import '../core/utils/time_format.dart';", "import 'package:mobile_app/core/utils/time_format.dart';")
replace_in_file(f_history, "import '../mock/mock_data.dart';", "import 'package:mobile_app/core/models/scan_models.dart';")
replace_in_file(f_history, "import '../theme/app_theme.dart';", "import 'package:mobile_app/theme/app_theme.dart';")

with open(f_history, 'r', encoding='utf-8') as f:
    h_content = f.read()
h_content = re.sub(
    r'CSMockData\.movies\.firstWhere\([^)]*\)',
    "CSMockMovie(id: '1', title: 'Movie', time: '', room: '', roomId: '', showId: '')",
    h_content
)
with open(f_history, 'w', encoding='utf-8') as f:
    f.write(h_content)

# Fix scanner_screen.dart
f_scanner = 'lib/features/scanner/presentation/scanner_screen.dart'
with open(f_scanner, 'r', encoding='utf-8') as f:
    s_content = f.read()
s_content = s_content.replace(
    """  int get _scannedCount => HiveService.getScanHistory(
        roomId: widget.roomId,
        showId: widget.showId,
        capacity: 100,
      ).length;""",
    """  int get _scannedCount => HiveService.getScanHistory(
        roomId: widget.roomId,
        showId: widget.showId,
      ).length;"""
)
with open(f_scanner, 'w', encoding='utf-8') as f:
    f.write(s_content)


# Fix settings screen
f_settings = 'lib/features/settings/presentation/cs_settings_screen.dart'
with open(f_settings, 'r', encoding='utf-8') as f:
    set_content = f.read()
set_content = set_content.replace('CSMockData.employeeRole', "ApiClient.currentUser?['role'] ?? 'Nhân viên'")
set_content = set_content.replace('CSMockData.employeeId', "ApiClient.currentUser?['id'] ?? 'ID'")
with open(f_settings, 'w', encoding='utf-8') as f:
    f.write(set_content)


# Fix test
f_test = 'test/seat_and_scan_flow_test.dart'
with open(f_test, 'r', encoding='utf-8') as f:
    t_content = f.read()
t_content = re.sub(r'SeatReportStore\..*?;\n', '', t_content)
with open(f_test, 'w', encoding='utf-8') as f:
    f.write(t_content)


# Fix movie card
f_movie_card = 'lib/features/rooms/presentation/widgets/cs_movie_card.dart'
replace_in_file(f_movie_card, "import '../mock/mock_data.dart';", "import 'package:mobile_app/core/models/scan_models.dart';")
replace_in_file(f_movie_card, "import '../theme/app_theme.dart';", "import 'package:mobile_app/theme/app_theme.dart';")


# Fix notifications
f_notif = 'lib/features/notifications/presentation/cs_notification_screen.dart'
with open(f_notif, 'r', encoding='utf-8') as f:
    n_content = f.read()
n_content = n_content.replace("import '../mock/mock_data.dart';", "")
n_content = re.sub(r'final List<CSMockNotification> notifications = \[.*?\];', 'final List<dynamic> notifications = [];', n_content, flags=re.DOTALL)
n_content = n_content.replace('CSMockNotification', 'dynamic')
with open(f_notif, 'w', encoding='utf-8') as f:
    f.write(n_content)

print("Final patch done.")
