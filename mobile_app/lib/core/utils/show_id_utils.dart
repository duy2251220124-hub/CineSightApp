import 'package:flutter/foundation.dart';

/// Tiện ích tạo show_id chuẩn để dùng chung giữa
/// màn hình chọn suất chiếu, ScannerScreen và ApiClient.
///
/// Định dạng kết quả: "yyyy-MM-ddTHH:mm" (ISO rút gọn, 24h, số 0 đứng đầu)
/// Ví dụ: toShowId("2026-09-29", "19:30 - 21:20") -> "2026-09-29T19:30"
String toShowId(String date, String timeRange) {
  // Lấy phần giờ bắt đầu, bỏ phần " - HH:mm" phía sau nếu có
  final startTime = timeRange.split(' - ').first.trim();
  final parts = startTime.split(':');
  final h = int.parse(parts[0]).toString().padLeft(2, '0');
  final m = int.parse(parts[1]).toString().padLeft(2, '0');
  return '${date}T$h:$m';
}

/// Trạng thái suất chiếu đang được chọn toàn cục trong ứng dụng
class CSActiveShowtime {
  static final ValueNotifier<Map<String, String>> notifier = ValueNotifier({
    'roomId': 'room4',
    'showId': 'auto',
    'movieTitle': 'Tự động nhận diện',
  });

  static String get roomId => notifier.value['roomId'] ?? 'room4';
  static String get showId => notifier.value['showId'] ?? 'auto';
  static String get movieTitle => notifier.value['movieTitle'] ?? 'Tự động nhận diện';

  static void update({required String roomId, required String showId, String? movieTitle}) {
    notifier.value = {
      'roomId': roomId,
      'showId': showId,
      'movieTitle': movieTitle ?? '',
    };
  }
}
