import 'package:hive_flutter/hive_flutter.dart';

class HiveService {
  static const String _ticketBoxName = 'scanned_tickets_box';

  /// Khởi tạo Hive Database (Chạy 1 lần duy nhất khi mở App)
  static Future<void> init() async {
    // Khởi tạo engine lưu trữ trên điện thoại
    await Hive.initFlutter();

    // Mở một cái "Hộp" (Bảng) để chứa danh sách vé
    await Hive.openBox<String>(_ticketBoxName);
  }

  /// Hàm lưu mã vé vừa quét vào bộ nhớ máy (Dành cho lúc rớt mạng)
  static Future<void> saveScannedTicket(String ticketCode) async {
    final box = Hive.box<String>(_ticketBoxName);

    // Thuật toán chống lưu trùng lặp: Nếu trong máy chưa có vé này thì mới lưu
    if (!box.values.contains(ticketCode)) {
      await box.add(ticketCode);
      print('[HIVE] Đã lưu vé $ticketCode vào bộ nhớ Offline thành công!');
    }
  }

  /// Lấy danh sách toàn bộ vé đang lưu trong máy để chuẩn bị đẩy lên AI Server
  static List<String> getAllScannedTickets() {
    final box = Hive.box<String>(_ticketBoxName);
    return box.values.toList();
  }

  /// Xóa toàn bộ vé trong máy SAU KHI đã đồng bộ lên mạng thành công
  static Future<void> clearTicketsAfterSync() async {
    final box = Hive.box<String>(_ticketBoxName);
    await box.clear();
    print('[HIVE] Đã dọn dẹp bộ nhớ Offline sau khi đồng bộ!');
  }
}
