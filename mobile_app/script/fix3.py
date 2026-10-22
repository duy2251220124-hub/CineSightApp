import os
import re

f_history = 'lib/features/scanner/presentation/cs_scan_history_screen.dart'
with open(f_history, 'r', encoding='utf-8') as f:
    hc = f.read()

# Fix the broken movie definition
broken_def = """    final movie = CSMockMovie(id: '1', title: 'Movie', time: '', room: '', roomId: '', showId: '') => m.roomId == widget.roomId,
      orElse: () => CSMockData.movies.first,
    );"""
fixed_def = "    final movie = CSMockMovie(id: '1', title: 'Ä ang kiá»ƒm vÃ©', time: '', room: widget.roomId, roomId: widget.roomId, showId: widget.showId, capacity: 100);"
hc = hc.replace(broken_def, fixed_def)
with open(f_history, 'w', encoding='utf-8') as f:
    f.write(hc)

f_scanner = 'lib/features/scanner/presentation/scanner_screen.dart'
with open(f_scanner, 'r', encoding='utf-8') as f:
    sc = f.read()

sc = sc.replace("        capacity: 100,", "")
with open(f_scanner, 'w', encoding='utf-8') as f:
    f.write(sc)

f_settings = 'lib/features/settings/presentation/cs_settings_screen.dart'
with open(f_settings, 'r', encoding='utf-8') as f:
    sec = f.read()
# Find invalid constant at 99. "const CSSettingsTile(... title: ... trailing: ApiClient... )"?
# Maybe we can't use const if trailing is not const.
sec = sec.replace("const CSSettingsTile(", "CSSettingsTile(")
sec = sec.replace("const CSSettingsSectionTitle(", "CSSettingsSectionTitle(")
sec = sec.replace("const CSSettingsSwitchTile(", "CSSettingsSwitchTile(")
with open(f_settings, 'w', encoding='utf-8') as f:
    f.write(sec)

f_test = 'test/seat_and_scan_flow_test.dart'
with open(f_test, 'r', encoding='utf-8') as f:
    tc = f.read()

tc = re.sub(r'// expect.*?;\n?', '', tc)
with open(f_test, 'w', encoding='utf-8') as f:
    f.write(tc)
print("Done fixing")
