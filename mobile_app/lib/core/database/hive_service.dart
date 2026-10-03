import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:hive_flutter/hive_flutter.dart';

/// Một bản ghi lịch sử quét vé (lưu vĩnh viễn trên máy, KHÔNG bị xóa khi sync).
class ScanRecord {
  final String ticket;
  final String room;
  final String seat;
  final String show;
  final DateTime scannedAt;

  const ScanRecord({
    required this.ticket,
    required this.room,
    required this.seat,
    required this.show,
    required this.scannedAt,
  });

  Map<String, dynamic> toJson() => {
        'ticket': ticket,
        'room': room,
        'seat': seat,
        'show': show,
        'scanned_at': scannedAt.toIso8601String(),
      };

  static ScanRecord? tryParse(String raw) {
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return ScanRecord(
        ticket: '${map['ticket']}',
        room: '${map['room'] ?? ''}',
        seat: '${map['seat'] ?? ''}',
        show: '${map['show'] ?? ''}',
        scannedAt: DateTime.tryParse('${map['scanned_at']}') ?? DateTime.now(),
      );
    } catch (_) {
      return null;
    }
  }
}

class HiveService {
  static const String _ticketBoxName = 'scanned_tickets_box';

  /// Hộp lịch sử: giữ lại mọi vé đã quét để chống quét trùng sau khi sync
  /// và để hiển thị màn "Lịch sử quét vé". Key = mã vé.
  static const String _historyBoxName = 'scan_history_box';

  /// Khởi tạo Hive Database (Chạy 1 lần duy nhất khi mở App)
  static Future<void> init() async {
    // Khởi tạo engine lưu trữ trên điện thoại
    await Hive.initFlutter();

    // Mở một cái "Hộp" (Bảng) để chứa danh sách vé
    await Hive.openBox<String>(_ticketBoxName);
    await Hive.openBox<String>(_historyBoxName);
  }

  /// Ghi lịch sử quét (key = mã vé nên mỗi vé chỉ có 1 bản ghi).
  static Future<void> addScanRecord(ScanRecord record) async {
    final box = Hive.box<String>(_historyBoxName);
    await box.put(record.ticket, jsonEncode(record.toJson()));
  }

  /// Tìm bản ghi quét trước đó của 1 mã vé (null nếu chưa quét).
  static ScanRecord? findScanRecord(String ticket) {
    final raw = Hive.box<String>(_historyBoxName).get(ticket);
    return raw == null ? null : ScanRecord.tryParse(raw);
  }

  /// Lịch sử quét, mới nhất trước. Lọc theo phòng / suất nếu truyền vào.
  static List<ScanRecord> getScanHistory({String? roomId, String? showId}) {
    final records = Hive.box<String>(_historyBoxName)
        .values
        .map(ScanRecord.tryParse)
        .whereType<ScanRecord>()
        .where((r) => roomId == null || roomId.isEmpty || r.room == roomId)
        .where((r) => showId == null || showId.isEmpty || r.show == showId)
        .toList()
      ..sort((a, b) => b.scannedAt.compareTo(a.scannedAt));
    return records;
  }

  /// Hàm lưu mã vé vừa quét vào bộ nhớ máy (Dành cho lúc rớt mạng)
  static Future<void> saveScannedTicket(String ticketCode) async {
    final box = Hive.box<String>(_ticketBoxName);

    // Thuật toán chống lưu trùng lặp: Nếu trong máy chưa có vé này thì mới lưu
    if (!box.values.contains(ticketCode)) {
      await box.add(ticketCode);
      debugPrint('[HIVE] Đã lưu vé $ticketCode vào bộ nhớ Offline thành công!');
    }
  }

  /// Lấy danh sách toàn bộ vé đang lưu trong máy để chuẩn bị đẩy lên AI Server
  static List<String> getAllScannedTickets() {
    final box = Hive.box<String>(_ticketBoxName);
    return box.values.toList();
  }

  /// Xóa toàn bộ vé trong máy SAU KHI đã đồng bộ lên mạng thành công
    static Future<void> clearTicketsAfterSync(List<String> syncedTickets) async {
    final box = Hive.box<String>(_ticketBoxName);
    final keysToDelete = [];
    for (var key in box.keys) {
      if (syncedTickets.contains(box.get(key))) {
        keysToDelete.add(key);
      }
    }
    await box.deleteAll(keysToDelete);
    debugPrint('[HIVE] Đã dọn dẹp ${keysToDelete.length} vé khỏi bộ nhớ Offline sau khi đồng bộ!');
  }
}
