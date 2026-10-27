/// Tiện ích chuẩn hóa hiển thị tên phòng chiếu trong toàn bộ ứng dụng CineSight
String formatRoomName(String? rawRoom) {
  if (rawRoom == null || rawRoom.trim().isEmpty) return 'Phòng chiếu';
  final clean = rawRoom.replaceAll('seats_config_', '').trim();
  final match = RegExp(r'(\d+)').firstMatch(clean);
  if (match != null) {
    return 'Phòng chiếu số ${match.group(1)}';
  }
  return clean;
}

