String _two(int v) => v.toString().padLeft(2, '0');

/// "19:30"
String formatHm(DateTime t) => '${_two(t.hour)}:${_two(t.minute)}';

/// "19:30 - 03/10/2026"
String formatScanTime(DateTime t) =>
    '${formatHm(t)} - ${_two(t.day)}/${_two(t.month)}/${t.year}';
