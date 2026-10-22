import re

f = 'lib/core/network/presentation/cs_offline_screen.dart'
with open(f, 'r', encoding='utf-8') as file:
    content = file.read()
content = re.sub(r'CSMockData\.[a-zA-Z0-9_]+', "'Offline'", content)
with open(f, 'w', encoding='utf-8') as file:
    file.write(content)

f = 'lib/features/notifications/presentation/cs_notification_screen.dart'
with open(f, 'r', encoding='utf-8') as file:
    content = file.read()
content = content.replace('List<dynamic> get notifications => [];', 'final List<dynamic> notifications = [];')
with open(f, 'w', encoding='utf-8') as file:
    file.write(content)

f = 'lib/features/settings/presentation/cs_settings_screen.dart'
with open(f, 'r', encoding='utf-8') as file:
    content = file.read()
content = content.replace('const CSSettingsTile(', 'CSSettingsTile(')
with open(f, 'w', encoding='utf-8') as file:
    file.write(content)
