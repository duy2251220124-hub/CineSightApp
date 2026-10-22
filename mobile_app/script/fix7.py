import re

# 1. cs_offline_screen.dart
f_off = 'lib/core/network/presentation/cs_offline_screen.dart'
with open(f_off, 'r', encoding='utf-8') as file:
    content = file.read()
# Replace any remaining mock things or broken .first
content = re.sub(r"'Offline'\.split\(' '\)\.first", "'Offline'", content)
content = content.replace("'Offline'.first", "'O'")
with open(f_off, 'w', encoding='utf-8') as file:
    file.write(content)

# 2. cs_notification_screen.dart
f_notif = 'lib/features/notifications/presentation/cs_notification_screen.dart'
with open(f_notif, 'r', encoding='utf-8') as file:
    content = file.read()
content = content.replace("final List<dynamic> notifications = [];", "")
content = re.sub(r'\bnotifications\b', '[]', content)
# But wait, notifications.isEmpty or notifications.length etc
content = content.replace("[].isEmpty", "true")
content = content.replace("[].length", "0")
content = content.replace("![][index]", "null")
with open(f_notif, 'w', encoding='utf-8') as file:
    file.write(content)

# 3. cs_settings_screen.dart
f_set = 'lib/features/settings/presentation/cs_settings_screen.dart'
with open(f_set, 'r', encoding='utf-8') as file:
    content = file.read()
# Remove ALL const before CSSettingsTile and CSSettingsSwitchTile and CSSettingsSectionTitle
content = content.replace("const CSSettingsTile", "CSSettingsTile")
content = content.replace("const CSSettingsSwitchTile", "CSSettingsSwitchTile")
content = content.replace("const CSSettingsSectionTitle", "CSSettingsSectionTitle")
with open(f_set, 'w', encoding='utf-8') as file:
    file.write(content)

print("Done final fix")
