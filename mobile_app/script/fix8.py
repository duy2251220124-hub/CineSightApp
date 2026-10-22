import os
import re

def fix_file(filepath, fixes):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in fixes:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. cs_offline_screen.dart
fix_file('lib/core/network/presentation/cs_offline_screen.dart', [
    ("final movie = 'O';", ""),
    ("movie.title", "'Dune: Part Two'"),
    ("${movie.time} | ${movie.room}", "19:30 | P.03"),
])

# 2. unused imports
def remove_import(filepath, imp):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(rf"import\s+'{imp}';\s*", "", content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

remove_import('lib/features/alerts/presentation/cs_add_incident_screen.dart', 'package:mobile_app/theme/app_theme.dart')
remove_import('lib/features/alerts/presentation/cs_handover_screen.dart', 'package:mobile_app/theme/app_theme.dart')
remove_import('lib/features/alerts/presentation/cs_incident_detail_screen.dart', 'package:mobile_app/theme/app_theme.dart')
remove_import('lib/main.dart', 'package:mobile_app/theme/app_theme.dart')

# 3. prefer_final_fields
fix_file('lib/features/alerts/presentation/cs_damaged_seat_screen.dart', [
    ("Set<String> _selectedSeats", "final Set<String> _selectedSeats")
])
fix_file('lib/features/home/presentation/home_screen.dart', [
    ("String _selectedShowtime", "final String _selectedShowtime")
])
fix_file('lib/features/rooms/presentation/cs_seat_map_screen.dart', [
    ("Set<String> _selectedSeats", "final Set<String> _selectedSeats"),
    ("Map<String, String> _reportedSeats", "final Map<String, String> _reportedSeats")
])

# 4. cs_settings_screen.dart invalid constant and missing const constructors
fix_file('lib/features/settings/presentation/cs_settings_screen.dart', [
    ("child: const Column(", "child: Column("),
])
def add_const_constructors():
    filepath = 'lib/features/settings/presentation/cs_settings_screen.dart'
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = re.sub(r'class CSSettingsGroup extends StatelessWidget \{\s*CSSettingsGroup\(\{super\.key,', 'class CSSettingsGroup extends StatelessWidget {\n  const CSSettingsGroup({super.key,', content)
    content = re.sub(r'class CSSettingsItem extends StatelessWidget \{\s*CSSettingsItem\(\{super\.key,', 'class CSSettingsItem extends StatelessWidget {\n  const CSSettingsItem({super.key,', content)
    content = re.sub(r'class CSSettingsSwitch extends StatelessWidget \{\s*CSSettingsSwitch\(\{super\.key,', 'class CSSettingsSwitch extends StatelessWidget {\n  const CSSettingsSwitch({super.key,', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

add_const_constructors()

# 5. test/seat_and_scan_flow_test.dart unused variable
fix_file('test/seat_and_scan_flow_test.dart', [
    ("final previous = ", "")
])

print("Done fix8")
